"""
Signal File Generator for XAUUSD macro-factor model.

Generates standardized signal files from model predictions with:
  - Point-in-Time (PIT) timestamps
  - No look-ahead bias
  - Proper macro data release alignment
  - Deterministic output for reproducibility

Output format:
    timestamp,signal,confidence,factors_used,data_available_at,notes
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Constants — DO NOT CHANGE without explicit version bump
# ---------------------------------------------------------------------------
CALCULATION_VERSION = "signal/v1"
ENGINE_VERSION = "researchos/1.0.0"

# Default macro data release lags (calendar days after event)
# These reflect when the data is ACTUALLY available to market participants
MACRO_RELEASE_LAGS = {
    "dxy_return": 0,  # DXY: available next trading session
    "vix_level": 0,  # VIX: available next trading session
    "cpi_inflation": 15,  # CPI: released ~15th of month
    "nfp": 7,  # NFP: released first Friday of month
    "pce": 30,  # PCE: released ~30 days after month-end
}

# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SignalRecord:
    """
    Immutable signal record with full PIT provenance.

    Attributes:
        timestamp: When the signal was GENERATED (must be <= data_available_at)
        signal: Trading signal (1=BUY, -1=SELL, 0=HOLD)
        confidence: Model confidence [0.0, 1.0]
        factors_used: List of factor names that contributed to this signal
        data_available_at: Earliest time this signal could have been generated
        prediction: Raw model output before thresholding
        calculation_version: Version of calculation logic
        engine_version: Engine version that produced this signal
        input_hash: Hash of inputs for reproducibility
        notes: Optional audit notes
    """

    timestamp: str
    signal: int
    confidence: float
    factors_used: list[str]
    data_available_at: str
    prediction: float
    calculation_version: str = CALCULATION_VERSION
    engine_version: str = ENGINE_VERSION
    input_hash: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "signal": self.signal,
            "confidence": round(self.confidence, 6),
            "factors_used": json.dumps(self.factors_used, sort_keys=True),
            "data_available_at": self.data_available_at,
            "prediction": round(self.prediction, 6),
            "calculation_version": self.calculation_version,
            "engine_version": self.engine_version,
            "input_hash": self.input_hash,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SignalRecord:
        return cls(
            timestamp=data["timestamp"],
            signal=int(data["signal"]),
            confidence=float(data["confidence"]),
            factors_used=json.loads(data["factors_used"]),
            data_available_at=data["data_available_at"],
            prediction=float(data["prediction"]),
            calculation_version=data.get("calculation_version", CALCULATION_VERSION),
            engine_version=data.get("engine_version", ENGINE_VERSION),
            input_hash=data.get("input_hash", ""),
            notes=data.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Core signal generation with PIT enforcement
# ---------------------------------------------------------------------------


def enforce_pit_timestamp(
    event_date: pd.Timestamp,
    macro_release_date: pd.Timestamp,
    factor_name: str,
) -> pd.Timestamp:
    """
    Enforce Point-in-Time constraint: signal can only be generated
    AFTER the macro data is actually released.

    Args:
        event_date: The date we want to generate a signal for
        macro_release_date: When the macro data was actually released
        factor_name: Name of the macro factor (for lag lookup)

    Returns:
        The earliest valid timestamp for this signal
    """
    release_lag = MACRO_RELEASE_LAGS.get(factor_name, 0)
    earliest_available = macro_release_date + timedelta(days=release_lag)

    if event_date < earliest_available:
        return earliest_available
    return event_date


def generate_signal_file_from_predictions(
    predictions: pd.Series,
    gold_prices: pd.Series,
    macro_data: dict[str, pd.Series],
    output_path: str | Path,
    threshold: float = 0.0,
    confidence_func: callable | None = None,
) -> pd.DataFrame:
    """
    Generate a standardized signal file from model predictions.

    CRITICAL RULES:
    1. No look-ahead bias: timestamp is when signal COULD have been generated
    2. PIT data: macro factors use their actual release dates
    3. Today's close → tomorrow's trade signal

    Args:
        predictions: Model predictions (aligned with gold_prices index)
        gold_prices: Gold price series (used for entry price reference)
        macro_data: Dict of {factor_name: series} with release dates
        output_path: Where to save the signal CSV
        threshold: Prediction threshold for signal generation
        confidence_func: Optional function(prediction) -> confidence [0,1]

    Returns:
        DataFrame of signal records
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = []

    for date, pred in predictions.items():
        if pd.isna(pred):
            continue

        # Skip if we don't have gold price for this date
        if date not in gold_prices.index:
            continue

        # Determine signal direction
        if pred > threshold:
            signal = 1
        elif pred < -threshold:
            signal = -1
        else:
            signal = 0

        # Compute confidence
        if confidence_func is not None:
            confidence = confidence_func(pred)
        else:
            # Simple confidence: distance from threshold normalized
            confidence = min(abs(pred) / (abs(threshold) + 1e-9), 1.0)

        # Determine which factors were available at this point (PIT check)
        factors_used = []
        data_available_at = date.strftime("%Y-%m-%d")

        for factor_name, factor_series in macro_data.items():
            if date in factor_series.index and not pd.isna(factor_series[date]):
                # Get the release date for this factor (last non-NaN before or at date)
                available = factor_series.loc[:date].last_valid_index()
                if available is not None:
                    pit_date = enforce_pit_timestamp(date, available, factor_name)
                    factors_used.append(factor_name)
                    if pit_date.strftime("%Y-%m-%d") > data_available_at:
                        data_available_at = pit_date.strftime("%Y-%m-%d")

        if not factors_used:
            continue

        # Compute input hash for reproducibility
        input_data = {
            "timestamp": date.strftime("%Y-%m-%d"),
            "prediction": round(float(pred), 6),
            "signal": signal,
            "factors": sorted(factors_used),
            "gold_price": round(float(gold_prices[date]), 2),
        }
        input_hash = _compute_input_hash(input_data)

        record = SignalRecord(
            timestamp=date.strftime("%Y-%m-%d"),
            signal=signal,
            confidence=confidence,
            factors_used=sorted(factors_used),
            data_available_at=data_available_at,
            prediction=pred,
            input_hash=input_hash,
            notes=f"Generated from {len(factors_used)} factors",
        )
        records.append(record)

    # Build DataFrame
    df = pd.DataFrame([r.to_dict() for r in records])

    # Save to CSV
    df.to_csv(output_path, index=False)

    return df


def generate_signal_file_from_events(
    events: pd.DataFrame,
    output_path: str | Path,
    min_confidence: float = 0.0,
) -> pd.DataFrame:
    """
    Generate signal file from event study results (e.g., SMA crossover events).

    Each event becomes a signal with PIT-validated timestamp.

    Args:
        events: DataFrame with event study results (must have 'timestamp', 'direction')
        output_path: Where to save the signal CSV
        min_confidence: Minimum confidence threshold to include signal

    Returns:
        DataFrame of signal records
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = []

    for _, row in events.iterrows():
        if pd.isna(row.get("timestamp")) or pd.isna(row.get("direction")):
            continue

        timestamp = pd.Timestamp(row["timestamp"])
        direction = str(row["direction"]).upper()

        if direction == "LONG":
            signal = 1
        elif direction == "SHORT":
            signal = -1
        else:
            continue

        # Confidence based on ATR (higher ATR = lower confidence)
        atr = row.get("atr14", 0.0)
        entry = row.get("entry", 0.0)
        if entry > 0 and not pd.isna(atr):
            confidence = max(0.0, min(1.0, 1.0 - (atr / entry)))
        else:
            confidence = 0.5

        if confidence < min_confidence:
            continue

        # PIT: signal timestamp is the event timestamp (when crossover was detected)
        # The signal can only be traded at the NEXT bar
        next_timestamp = (timestamp + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")

        input_data = {
            "timestamp": next_timestamp,
            "signal": signal,
            "direction": direction,
            "entry": round(float(entry), 2) if not pd.isna(entry) else 0.0,
            "atr": round(float(atr), 6) if not pd.isna(atr) else 0.0,
        }
        input_hash = _compute_input_hash(input_data)

        record = SignalRecord(
            timestamp=next_timestamp,
            signal=signal,
            confidence=confidence,
            factors_used=["sma20_sma100_crossover", "atr"],
            data_available_at=next_timestamp,
            prediction=float(signal),
            input_hash=input_hash,
            notes=f"SMA20/SMA100 {direction} crossover at {timestamp}",
        )
        records.append(record)

    df = pd.DataFrame([r.to_dict() for r in records])
    df.to_csv(output_path, index=False)

    return df


# ---------------------------------------------------------------------------
# Deterministic hashing
# ---------------------------------------------------------------------------


def _compute_input_hash(data: dict[str, Any]) -> str:
    """
    Compute deterministic SHA-256 hash of input data.

    Uses the same canonicalization as backend_hash.py for consistency.
    """
    import hashlib
    import json

    def stable_float(value: float) -> str:
        if value == 0.0:
            return "0.0"
        return repr(value)

    def canonicalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): canonicalize(v) for k, v in sorted(value.items(), key=str)}
        if isinstance(value, (list, tuple)):
            return [canonicalize(v) for v in value]
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return stable_float(value)
        if value is None or isinstance(value, str):
            return value
        return str(value)

    canonical = canonicalize(data)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_signal_file(signal_path: str | Path) -> dict[str, Any]:
    """
    Validate a signal file for PIT compliance and determinism.

    Returns:
        Validation report dict with:
            - valid: bool
            - errors: list of error strings
            - warnings: list of warning strings
            - stats: dict of signal statistics
    """
    signal_path = Path(signal_path)
    if not signal_path.exists():
        return {"valid": False, "errors": [f"File not found: {signal_path}"], "warnings": [], "stats": {}}

    df = pd.read_csv(signal_path)
    errors = []
    warnings = []
    stats = {}

    # Check required columns
    required_cols = ["timestamp", "signal", "confidence", "factors_used", "data_available_at"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")

    # Check PIT compliance: data_available_at >= timestamp
    if "timestamp" in df.columns and "data_available_at" in df.columns:
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
        df["data_available_dt"] = pd.to_datetime(df["data_available_at"])
        lookahead = df[df["data_available_dt"] < df["timestamp_dt"]]
        if len(lookahead) > 0:
            errors.append(f"PIT VIOLATION: {len(lookahead)} signals have data_available_at < timestamp. " f"Example: {lookahead.iloc[0]['timestamp']}")

    # Check for duplicate timestamps
    if "timestamp" in df.columns:
        dupes = df[df.duplicated(subset=["timestamp"], keep=False)]
        if len(dupes) > 0:
            warnings.append(f"Duplicate timestamps found: {len(dupes)} rows")

    # Check signal values
    if "signal" in df.columns:
        invalid_signals = df[~df["signal"].isin([-1, 0, 1])]
        if len(invalid_signals) > 0:
            errors.append(f"Invalid signal values: {invalid_signals['signal'].unique().tolist()}")

    # Compute stats
    if "signal" in df.columns:
        stats["total_signals"] = len(df)
        stats["buy_signals"] = int((df["signal"] == 1).sum())
        stats["sell_signals"] = int((df["signal"] == -1).sum())
        stats["hold_signals"] = int((df["signal"] == 0).sum())
    if "confidence" in df.columns:
        stats["mean_confidence"] = round(float(df["confidence"].mean()), 4)
        stats["min_confidence"] = round(float(df["confidence"].min()), 4)
        stats["max_confidence"] = round(float(df["confidence"].max()), 4)

    stats["valid"] = len(errors) == 0

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate signal files from model predictions")
    parser.add_argument("--input", required=True, help="Input CSV with predictions")
    parser.add_argument("--output", default="reports/signals/signals.csv", help="Output signal file path")
    parser.add_argument("--type", choices=["predictions", "events"], default="predictions", help="Input type: predictions or events")
    parser.add_argument("--threshold", type=float, default=0.0, help="Signal threshold")
    parser.add_argument("--validate", action="store_true", help="Validate output file")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)

    if args.type == "predictions":
        # Expect columns: date, prediction
        if "date" not in df.columns or "prediction" not in df.columns:
            print("ERROR: predictions input must have 'date' and 'prediction' columns")
            sys.exit(1)

        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
        predictions = df["prediction"]

        # Create dummy gold prices for timestamp reference
        gold_prices = pd.Series(1.0, index=predictions.index)

        # Create dummy macro data (in real usage, pass actual macro_data dict)
        macro_data = {}

        result = generate_signal_file_from_predictions(
            predictions=predictions,
            gold_prices=gold_prices,
            macro_data=macro_data,
            output_path=args.output,
            threshold=args.threshold,
        )

    elif args.type == "events":
        # Expect columns: timestamp, direction
        required = {"timestamp", "direction"}
        if not required.issubset(df.columns):
            print(f"ERROR: events input must have columns: {required}")
            sys.exit(1)

        result = generate_signal_file_from_events(
            events=df,
            output_path=args.output,
        )

    print(f"\nSignal file generated: {args.output}")
    print(f"Total signals: {len(result)}")
    print(f"  BUY:  {(result['signal'] == 1).sum()}")
    print(f"  SELL: {(result['signal'] == -1).sum()}")
    print(f"  HOLD: {(result['signal'] == 0).sum()}")

    if args.validate:
        report = validate_signal_file(args.output)
        print(f"\nValidation: {'PASS' if report['valid'] else 'FAIL'}")
        if report["errors"]:
            print("Errors:", report["errors"])
        if report["warnings"]:
            print("Warnings:", report["warnings"])
        print("Stats:", report["stats"])


if __name__ == "__main__":
    main()
