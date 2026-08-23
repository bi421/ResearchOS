from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================
# CONFIG
# ============================================================

BOOTSTRAP_ITERATIONS = 10_000
CONFIDENCE_LEVEL = 0.95
RANDOM_SEED = 42

DATASET = Path("reports/xauusd_event_study/xauusd_sma20_100_events_2021_2025.csv")

RETURNS = [
    "return_15m",
    "return_30m",
    "return_60m",
    "return_240m",
]

SMA20_CANDIDATES = [
    "SMA20",
    "sma20",
    "sma_20",
    "sma20_value",
]

SMA100_CANDIDATES = [
    "SMA100",
    "sma100",
    "sma_100",
    "sma100_value",
]


# ============================================================
# HELPERS
# ============================================================


def blocked(message: str) -> None:
    print()
    print("=" * 70)
    print("OUTCOME: BLOCKED")
    print("=" * 70)
    print(message)
    print()
    sys.exit(1)


def find_column(
    columns: list[str],
    candidates: list[str],
) -> str | None:
    lookup = {str(c).strip().lower(): c for c in columns}

    for candidate in candidates:
        found = lookup.get(candidate.lower())

        if found is not None:
            return found

    return None


def bootstrap_mean_ci(
    x: np.ndarray,
    iterations: int,
    confidence: float,
    seed: int,
) -> tuple[float, float]:
    n = len(x)

    if n == 0:
        return np.nan, np.nan

    rng = np.random.default_rng(seed)

    boot = np.empty(iterations, dtype=np.float64)

    for i in range(iterations):
        sample = rng.choice(x, size=n, replace=True)
        boot[i] = sample.mean()

    alpha = 1.0 - confidence

    lo, hi = np.percentile(
        boot,
        [
            alpha / 2.0 * 100.0,
            (1.0 - alpha / 2.0) * 100.0,
        ],
    )

    return float(lo), float(hi)


def classify(
    lo: float,
    hi: float,
) -> str:
    if lo > 0:
        return "POSITIVE EDGE"

    if hi < 0:
        return "NEGATIVE EDGE"

    return "NO CLEAR EDGE"


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    print("=" * 70)
    print("XAUUSD SMA20/100 — CONDITIONAL RETURN BOOTSTRAP")
    print("=" * 70)
    print()
    print(f"Dataset              : {DATASET}")
    print(f"Bootstrap iterations : {BOOTSTRAP_ITERATIONS:,}")
    print(f"Confidence level     : {CONFIDENCE_LEVEL:.0%}")
    print(f"Random seed          : {RANDOM_SEED}")
    print()

    # --------------------------------------------------------
    # DATASET VALIDATION
    # --------------------------------------------------------

    if not DATASET.exists():
        blocked(f"Dataset not found:\n  {DATASET.resolve()}")

    try:
        df = pd.read_csv(DATASET)
    except Exception as exc:
        blocked(f"Could not read dataset:\n{exc}")

    print(f"Rows                 : {len(df):,}")
    print(f"Columns              : {len(df.columns):,}")
    print()

    # --------------------------------------------------------
    # SCHEMA
    # --------------------------------------------------------

    print("Available columns:")
    for col in df.columns:
        print(f"  {col}")

    print()

    sma20_col = find_column(
        list(df.columns),
        SMA20_CANDIDATES,
    )

    sma100_col = find_column(
        list(df.columns),
        SMA100_CANDIDATES,
    )

    missing_returns = [col for col in RETURNS if col not in df.columns]

    if missing_returns:
        blocked(f"Required return columns are missing:\n  {missing_returns}\n\nNo synthetic or inferred return columns will be created.")

    if sma20_col is None or sma100_col is None:
        print("SMA columns were not found in the event-study file.")

        print()
        print("This is important: the script will NOT invent SMA20/SMA100 values.")

        print()
        print("If this event-study CSV stores the SMA state under different column names, send the column list above.")

        blocked("Cannot establish SMA20/SMA100 conditional state from the dataset schema.")

    print(f"SMA20 column         : {sma20_col}")
    print(f"SMA100 column        : {sma100_col}")
    print()

    # --------------------------------------------------------
    # NUMERIC CONVERSION
    # --------------------------------------------------------

    numeric_cols = [
        sma20_col,
        sma100_col,
        *RETURNS,
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    df = df.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    # --------------------------------------------------------
    # VALID STATE
    # --------------------------------------------------------

    valid_state = df[sma20_col].notna() & df[sma100_col].notna()

    df = df.loc[valid_state].copy()

    if df.empty:
        blocked("No valid rows remain after SMA20/SMA100 validation.")

    bullish = df[sma20_col] > df[sma100_col]
    bearish = df[sma20_col] < df[sma100_col]
    equal = df[sma20_col] == df[sma100_col]

    print("=" * 70)
    print("STATE DISTRIBUTION")
    print("=" * 70)

    print(f"Valid rows           : {len(df):,}")
    print(f"BULLISH SMA20>SMA100 : {bullish.sum():,} ({bullish.mean():.2%})")
    print(f"BEARISH SMA20<SMA100 : {bearish.sum():,} ({bearish.mean():.2%})")
    print(f"EQUAL SMA20=SMA100  : {equal.sum():,} ({equal.mean():.2%})")

    # --------------------------------------------------------
    # ANALYSIS FUNCTION
    # --------------------------------------------------------

    def analyze(
        name: str,
        mask: pd.Series,
        seed_offset: int,
    ) -> None:
        print()
        print("=" * 70)
        print(name)
        print("=" * 70)

        state_df = df.loc[mask].copy()

        print(f"State observations   : {len(state_df):,}")

        for idx, col in enumerate(RETURNS):
            x = state_df[col].dropna().to_numpy(dtype=float)

            n = len(x)

            if n == 0:
                print(f"{col:15} N=0 NO DATA")
                continue

            mean = float(x.mean())
            median = float(np.median(x))
            win_rate = float(np.mean(x > 0))

            lo, hi = bootstrap_mean_ci(
                x=x,
                iterations=BOOTSTRAP_ITERATIONS,
                confidence=CONFIDENCE_LEVEL,
                seed=RANDOM_SEED + seed_offset + idx,
            )

            status = classify(lo, hi)

            print(f"{col:15} N={n:,} mean={mean:.8%} median={median:.8%} win={win_rate:.2%} CI=[{lo:.8%}, {hi:.8%}] {status}")

    # --------------------------------------------------------
    # CONDITIONAL TESTS
    # --------------------------------------------------------

    analyze(
        "BULLISH STATE — SMA20 > SMA100",
        bullish,
        1_000,
    )

    analyze(
        "BEARISH STATE — SMA20 < SMA100",
        bearish,
        2_000,
    )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("CONDITIONAL BOOTSTRAP COMPLETE")
    print("=" * 70)
    print()
    print("Decision rule:")
    print("  CI entirely above 0  -> POSITIVE EDGE")
    print("  CI entirely below 0  -> NEGATIVE EDGE")
    print("  CI crosses 0         -> NO CLEAR EDGE")
    print()
    print("This test measures conditional return evidence.")
    print("It does NOT constitute a trading strategy.")
    print()


if __name__ == "__main__":
    main()
