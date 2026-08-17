"""Stable data models for the Python <-> C++ bridge contract.

These classes mirror ``cpp_quant_engine/python/bridge_models.h`` one-to-one.
Every model can be converted losslessly to/from a Python BaseObject (a dict of
primitives) via ``to_base_object()`` / ``from_base_object()`` — the same shape
the C++ pybind11 adapter accepts and produces.

Hash contract
-------------
``compute_input_hash`` / ``compute_result_hash`` reproduce the C++ SHA-256
digests byte-for-byte. The canonical serialization is:

* JSON object with alphabetically sorted keys,
* numbers formatted as fixed-point with 10 decimals (``f"{v:.10f}"``),
* strings JSON-escaped, no whitespace.

Timestamps are ISO-8601 strings ("YYYY-MM-DDTHH:MM:SS", UTC-naive).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List

DEFAULT_CALCULATION_VERSION = "CALCULATION_V1"


# ── Canonical serialization primitives (mirror of src/bridge/bridge.cpp) ──


def canonical_float(v: float) -> str:
    return f"{v:.10f}"


def canonical_json_escape(s: str) -> str:
    out: List[str] = []
    for ch in s:
        o = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif o < 0x20:
            out.append(f"\\u{o:04x}")
        else:
            out.append(ch)
    return "".join(out)


def _q(s: str) -> str:
    return '"' + canonical_json_escape(s) + '"'


def canonical_object(fields: Dict[str, str]) -> str:
    items = sorted(fields.items())
    body = ",".join(f"{_q(k)}:{v}" for k, v in items)
    return "{" + body + "}"


def canonical_float_array(values: List[float]) -> str:
    return "[" + ",".join(canonical_float(v) for v in values) + "]"


def canonical_double_map(m: Dict[str, float]) -> str:
    body = ",".join(f"{_q(k)}:{canonical_float(v)}" for k, v in sorted(m.items()))
    return "{" + body + "}"


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ── Candle ─────────────────────────────────────────────────────────────────


@dataclass
class Candle:
    timestamp: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    timeframe: str = "M1"

    def to_canonical(self) -> str:
        return canonical_object(
            {
                "close": canonical_float(self.close),
                "high": canonical_float(self.high),
                "low": canonical_float(self.low),
                "open": canonical_float(self.open),
                "timeframe": _q(self.timeframe),
                "timestamp": _q(self.timestamp),
                "volume": canonical_float(self.volume),
            }
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timeframe": self.timeframe,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "Candle":
        return cls(
            timestamp=str(d.get("timestamp", "")),
            open=float(d.get("open", 0.0)),
            high=float(d.get("high", 0.0)),
            low=float(d.get("low", 0.0)),
            close=float(d.get("close", 0.0)),
            volume=float(d.get("volume", 0.0)),
            timeframe=str(d.get("timeframe", "M1")),
        )


def _candles_canonical(candles: List[Candle]) -> str:
    return "[" + ",".join(c.to_canonical() for c in candles) + "]"


def _candles_to_dict(candles: List[Candle]) -> List[Dict[str, Any]]:
    return [c.to_base_object() for c in candles]


# ── MarketData ─────────────────────────────────────────────────────────────


@dataclass
class MarketDataRequest:
    symbol: str = ""
    timeframe: str = "M1"
    candles: List[Candle] = field(default_factory=list)
    calculation_version: str = DEFAULT_CALCULATION_VERSION

    def compute_input_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "calculation_version": _q(self.calculation_version),
                    "candles": _candles_canonical(self.candles),
                    "symbol": _q(self.symbol),
                    "timeframe": _q(self.timeframe),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "candles": _candles_to_dict(self.candles),
            "calculation_version": self.calculation_version,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "MarketDataRequest":
        return cls(
            symbol=str(d.get("symbol", "")),
            timeframe=str(d.get("timeframe", "M1")),
            candles=[Candle.from_base_object(c) for c in d.get("candles", [])],
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
        )


@dataclass
class MarketDataResult:
    symbol: str = ""
    timeframe: str = "M1"
    size: int = 0
    first_timestamp: str = ""
    last_timestamp: str = ""
    valid: bool = False
    validation_message: str = ""
    input_hash: str = ""
    result_hash: str = ""
    calculation_version: str = DEFAULT_CALCULATION_VERSION
    engine_version: str = ""
    bridge_version: str = ""

    def compute_result_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "bridge_version": _q(self.bridge_version),
                    "calculation_version": _q(self.calculation_version),
                    "engine_version": _q(self.engine_version),
                    "first_timestamp": _q(self.first_timestamp),
                    "input_hash": _q(self.input_hash),
                    "last_timestamp": _q(self.last_timestamp),
                    "size": canonical_float(float(self.size)),
                    "symbol": _q(self.symbol),
                    "timeframe": _q(self.timeframe),
                    "valid": "true" if self.valid else "false",
                    "validation_message": _q(self.validation_message),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "size": self.size,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "valid": self.valid,
            "validation_message": self.validation_message,
            "input_hash": self.input_hash,
            "result_hash": self.result_hash,
            "calculation_version": self.calculation_version,
            "engine_version": self.engine_version,
            "bridge_version": self.bridge_version,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "MarketDataResult":
        return cls(
            symbol=str(d.get("symbol", "")),
            timeframe=str(d.get("timeframe", "M1")),
            size=int(d.get("size", 0)),
            first_timestamp=str(d.get("first_timestamp", "")),
            last_timestamp=str(d.get("last_timestamp", "")),
            valid=bool(d.get("valid", False)),
            validation_message=str(d.get("validation_message", "")),
            input_hash=str(d.get("input_hash", "")),
            result_hash=str(d.get("result_hash", "")),
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
            engine_version=str(d.get("engine_version", "")),
            bridge_version=str(d.get("bridge_version", "")),
        )


@dataclass
class MarketData:
    """Convenience facade: a named, timeframe-aware candle series."""

    symbol: str
    timeframe: str = "M1"
    candles: List[Candle] = field(default_factory=list)
    calculation_version: str = DEFAULT_CALCULATION_VERSION

    def to_request(self) -> MarketDataRequest:
        return MarketDataRequest(
            symbol=self.symbol,
            timeframe=self.timeframe,
            candles=list(self.candles),
            calculation_version=self.calculation_version,
        )

    def compute_input_hash(self) -> str:
        return self.to_request().compute_input_hash()

    def to_base_object(self) -> Dict[str, Any]:
        return self.to_request().to_base_object()

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "MarketData":
        req = MarketDataRequest.from_base_object(d)
        return cls(
            symbol=req.symbol,
            timeframe=req.timeframe,
            candles=req.candles,
            calculation_version=req.calculation_version,
        )


# ── Statistics ─────────────────────────────────────────────────────────────


@dataclass
class StatisticsRequest:
    data: List[float] = field(default_factory=list)
    calculation_version: str = DEFAULT_CALCULATION_VERSION

    def compute_input_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "calculation_version": _q(self.calculation_version),
                    "data": canonical_float_array(self.data),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "data": self.data,
            "calculation_version": self.calculation_version,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "StatisticsRequest":
        return cls(
            data=[float(x) for x in d.get("data", [])],
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
        )


@dataclass
class StatisticsResult:
    count: int = 0
    sum: float = 0.0
    mean: float = 0.0
    variance: float = 0.0
    stddev: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    min: float = 0.0
    max: float = 0.0
    q1: float = 0.0
    median: float = 0.0
    q3: float = 0.0
    iqr: float = 0.0
    input_hash: str = ""
    result_hash: str = ""
    calculation_version: str = DEFAULT_CALCULATION_VERSION
    engine_version: str = ""
    bridge_version: str = ""

    def compute_result_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "bridge_version": _q(self.bridge_version),
                    "calculation_version": _q(self.calculation_version),
                    "count": canonical_float(float(self.count)),
                    "engine_version": _q(self.engine_version),
                    "input_hash": _q(self.input_hash),
                    "iqr": canonical_float(self.iqr),
                    "kurtosis": canonical_float(self.kurtosis),
                    "max": canonical_float(self.max),
                    "mean": canonical_float(self.mean),
                    "median": canonical_float(self.median),
                    "min": canonical_float(self.min),
                    "q1": canonical_float(self.q1),
                    "q3": canonical_float(self.q3),
                    "skewness": canonical_float(self.skewness),
                    "stddev": canonical_float(self.stddev),
                    "sum": canonical_float(self.sum),
                    "variance": canonical_float(self.variance),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "sum": self.sum,
            "mean": self.mean,
            "variance": self.variance,
            "stddev": self.stddev,
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
            "min": self.min,
            "max": self.max,
            "q1": self.q1,
            "median": self.median,
            "q3": self.q3,
            "iqr": self.iqr,
            "input_hash": self.input_hash,
            "result_hash": self.result_hash,
            "calculation_version": self.calculation_version,
            "engine_version": self.engine_version,
            "bridge_version": self.bridge_version,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "StatisticsResult":
        return cls(
            count=int(d.get("count", 0)),
            sum=float(d.get("sum", 0.0)),
            mean=float(d.get("mean", 0.0)),
            variance=float(d.get("variance", 0.0)),
            stddev=float(d.get("stddev", 0.0)),
            skewness=float(d.get("skewness", 0.0)),
            kurtosis=float(d.get("kurtosis", 0.0)),
            min=float(d.get("min", 0.0)),
            max=float(d.get("max", 0.0)),
            q1=float(d.get("q1", 0.0)),
            median=float(d.get("median", 0.0)),
            q3=float(d.get("q3", 0.0)),
            iqr=float(d.get("iqr", 0.0)),
            input_hash=str(d.get("input_hash", "")),
            result_hash=str(d.get("result_hash", "")),
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
            engine_version=str(d.get("engine_version", "")),
            bridge_version=str(d.get("bridge_version", "")),
        )


# ── Risk ───────────────────────────────────────────────────────────────────


@dataclass
class RiskRequest:
    returns: List[float] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    risk_free_rate: float = 0.0
    calculation_version: str = DEFAULT_CALCULATION_VERSION

    def compute_input_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "calculation_version": _q(self.calculation_version),
                    "equity_curve": canonical_float_array(self.equity_curve),
                    "returns": canonical_float_array(self.returns),
                    "risk_free_rate": canonical_float(self.risk_free_rate),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "returns": self.returns,
            "equity_curve": self.equity_curve,
            "risk_free_rate": self.risk_free_rate,
            "calculation_version": self.calculation_version,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "RiskRequest":
        return cls(
            returns=[float(x) for x in d.get("returns", [])],
            equity_curve=[float(x) for x in d.get("equity_curve", [])],
            risk_free_rate=float(d.get("risk_free_rate", 0.0)),
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
        )


@dataclass
class RiskResult:
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0
    cvar_99: float = 0.0
    max_drawdown_pct: float = 0.0
    peak_index: int = 0
    trough_index: int = 0
    recovery_index: int = 0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    input_hash: str = ""
    result_hash: str = ""
    calculation_version: str = DEFAULT_CALCULATION_VERSION
    engine_version: str = ""
    bridge_version: str = ""

    def compute_result_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "bridge_version": _q(self.bridge_version),
                    "calculation_version": _q(self.calculation_version),
                    "cvar_95": canonical_float(self.cvar_95),
                    "cvar_99": canonical_float(self.cvar_99),
                    "engine_version": _q(self.engine_version),
                    "input_hash": _q(self.input_hash),
                    "max_drawdown_pct": canonical_float(self.max_drawdown_pct),
                    "peak_index": canonical_float(float(self.peak_index)),
                    "recovery_index": canonical_float(float(self.recovery_index)),
                    "sharpe_ratio": canonical_float(self.sharpe_ratio),
                    "sortino_ratio": canonical_float(self.sortino_ratio),
                    "trough_index": canonical_float(float(self.trough_index)),
                    "var_95": canonical_float(self.var_95),
                    "var_99": canonical_float(self.var_99),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "var_95": self.var_95,
            "var_99": self.var_99,
            "cvar_95": self.cvar_95,
            "cvar_99": self.cvar_99,
            "max_drawdown_pct": self.max_drawdown_pct,
            "peak_index": self.peak_index,
            "trough_index": self.trough_index,
            "recovery_index": self.recovery_index,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "input_hash": self.input_hash,
            "result_hash": self.result_hash,
            "calculation_version": self.calculation_version,
            "engine_version": self.engine_version,
            "bridge_version": self.bridge_version,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "RiskResult":
        return cls(
            var_95=float(d.get("var_95", 0.0)),
            var_99=float(d.get("var_99", 0.0)),
            cvar_95=float(d.get("cvar_95", 0.0)),
            cvar_99=float(d.get("cvar_99", 0.0)),
            max_drawdown_pct=float(d.get("max_drawdown_pct", 0.0)),
            peak_index=int(d.get("peak_index", 0)),
            trough_index=int(d.get("trough_index", 0)),
            recovery_index=int(d.get("recovery_index", 0)),
            sharpe_ratio=float(d.get("sharpe_ratio", 0.0)),
            sortino_ratio=float(d.get("sortino_ratio", 0.0)),
            input_hash=str(d.get("input_hash", "")),
            result_hash=str(d.get("result_hash", "")),
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
            engine_version=str(d.get("engine_version", "")),
            bridge_version=str(d.get("bridge_version", "")),
        )


# ── Simulation ─────────────────────────────────────────────────────────────


@dataclass
class SimulationRequest:
    dataset_reference: str = ""
    dataset_version: str = "1.0.0"
    calculation_version: str = DEFAULT_CALCULATION_VERSION
    initial_capital: float = 100_000.0
    risk_free_rate: float = 0.0
    seed: int = 42
    start_time: str = ""
    end_time: str = ""
    prices: List[float] = field(default_factory=list)

    def compute_input_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "calculation_version": _q(self.calculation_version),
                    "dataset_reference": _q(self.dataset_reference),
                    "dataset_version": _q(self.dataset_version),
                    "end_time": _q(self.end_time),
                    "initial_capital": canonical_float(self.initial_capital),
                    "prices": canonical_float_array(self.prices),
                    "risk_free_rate": canonical_float(self.risk_free_rate),
                    "seed": canonical_float(float(self.seed)),
                    "start_time": _q(self.start_time),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "dataset_reference": self.dataset_reference,
            "dataset_version": self.dataset_version,
            "calculation_version": self.calculation_version,
            "initial_capital": self.initial_capital,
            "risk_free_rate": self.risk_free_rate,
            "seed": self.seed,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "prices": self.prices,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "SimulationRequest":
        return cls(
            dataset_reference=str(d.get("dataset_reference", "")),
            dataset_version=str(d.get("dataset_version", "1.0.0")),
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
            initial_capital=float(d.get("initial_capital", 100_000.0)),
            risk_free_rate=float(d.get("risk_free_rate", 0.0)),
            seed=int(d.get("seed", 42)),
            start_time=str(d.get("start_time", "")),
            end_time=str(d.get("end_time", "")),
            prices=[float(x) for x in d.get("prices", [])],
        )


@dataclass
class SimulationResult:
    simulation_id: str = ""
    dataset_reference: str = ""
    dataset_version: str = "1.0.0"
    calculation_version: str = DEFAULT_CALCULATION_VERSION
    start_time: str = ""
    end_time: str = ""
    input_hash: str = ""
    result_hash: str = ""
    execution_timestamp: str = ""
    returns: List[float] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    statistics: Dict[str, float] = field(default_factory=dict)
    performance: Dict[str, float] = field(default_factory=dict)
    engine_version: str = ""
    bridge_version: str = ""

    def compute_result_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "bridge_version": _q(self.bridge_version),
                    "calculation_version": _q(self.calculation_version),
                    "dataset_reference": _q(self.dataset_reference),
                    "dataset_version": _q(self.dataset_version),
                    "end_time": _q(self.end_time),
                    "engine_version": _q(self.engine_version),
                    "equity_curve": canonical_float_array(self.equity_curve),
                    "input_hash": _q(self.input_hash),
                    "metrics": canonical_double_map(self.metrics),
                    "performance": canonical_double_map(self.performance),
                    "returns": canonical_float_array(self.returns),
                    "simulation_id": _q(self.simulation_id),
                    "start_time": _q(self.start_time),
                    "statistics": canonical_double_map(self.statistics),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "dataset_reference": self.dataset_reference,
            "dataset_version": self.dataset_version,
            "calculation_version": self.calculation_version,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "input_hash": self.input_hash,
            "result_hash": self.result_hash,
            "execution_timestamp": self.execution_timestamp,
            "returns": self.returns,
            "equity_curve": self.equity_curve,
            "metrics": self.metrics,
            "statistics": self.statistics,
            "performance": self.performance,
            "engine_version": self.engine_version,
            "bridge_version": self.bridge_version,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "SimulationResult":
        return cls(
            simulation_id=str(d.get("simulation_id", "")),
            dataset_reference=str(d.get("dataset_reference", "")),
            dataset_version=str(d.get("dataset_version", "1.0.0")),
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
            start_time=str(d.get("start_time", "")),
            end_time=str(d.get("end_time", "")),
            input_hash=str(d.get("input_hash", "")),
            result_hash=str(d.get("result_hash", "")),
            execution_timestamp=str(d.get("execution_timestamp", "")),
            returns=[float(x) for x in d.get("returns", [])],
            equity_curve=[float(x) for x in d.get("equity_curve", [])],
            metrics={k: float(v) for k, v in d.get("metrics", {}).items()},
            statistics={k: float(v) for k, v in d.get("statistics", {}).items()},
            performance={k: float(v) for k, v in d.get("performance", {}).items()},
            engine_version=str(d.get("engine_version", "")),
            bridge_version=str(d.get("bridge_version", "")),
        )


# ── Backtest ───────────────────────────────────────────────────────────────


@dataclass
class BacktestRequest:
    symbol: str = ""
    timeframe: str = "M1"
    candles: List[Candle] = field(default_factory=list)
    initial_capital: float = 100_000.0
    commission_pct: float = 0.001
    slippage_pct: float = 0.0005
    allow_short: bool = True
    signal_reference: str = ""
    calculation_version: str = DEFAULT_CALCULATION_VERSION

    def compute_input_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "allow_short": "true" if self.allow_short else "false",
                    "calculation_version": _q(self.calculation_version),
                    "candles": _candles_canonical(self.candles),
                    "commission_pct": canonical_float(self.commission_pct),
                    "initial_capital": canonical_float(self.initial_capital),
                    "signal_reference": _q(self.signal_reference),
                    "slippage_pct": canonical_float(self.slippage_pct),
                    "symbol": _q(self.symbol),
                    "timeframe": _q(self.timeframe),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "candles": _candles_to_dict(self.candles),
            "initial_capital": self.initial_capital,
            "commission_pct": self.commission_pct,
            "slippage_pct": self.slippage_pct,
            "allow_short": self.allow_short,
            "signal_reference": self.signal_reference,
            "calculation_version": self.calculation_version,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "BacktestRequest":
        return cls(
            symbol=str(d.get("symbol", "")),
            timeframe=str(d.get("timeframe", "M1")),
            candles=[Candle.from_base_object(c) for c in d.get("candles", [])],
            initial_capital=float(d.get("initial_capital", 100_000.0)),
            commission_pct=float(d.get("commission_pct", 0.001)),
            slippage_pct=float(d.get("slippage_pct", 0.0005)),
            allow_short=bool(d.get("allow_short", True)),
            signal_reference=str(d.get("signal_reference", "")),
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
        )


@dataclass
class BacktestResult:
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    final_equity: float = 0.0
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    total_bars: int = 0
    num_trades: int = 0
    signal_reference: str = ""
    input_hash: str = ""
    result_hash: str = ""
    calculation_version: str = DEFAULT_CALCULATION_VERSION
    engine_version: str = ""
    bridge_version: str = ""

    def compute_result_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "bridge_version": _q(self.bridge_version),
                    "calculation_version": _q(self.calculation_version),
                    "drawdown_curve": canonical_float_array(self.drawdown_curve),
                    "engine_version": _q(self.engine_version),
                    "equity_curve": canonical_float_array(self.equity_curve),
                    "final_equity": canonical_float(self.final_equity),
                    "input_hash": _q(self.input_hash),
                    "max_drawdown_pct": canonical_float(self.max_drawdown_pct),
                    "num_trades": canonical_float(float(self.num_trades)),
                    "signal_reference": _q(self.signal_reference),
                    "total_bars": canonical_float(float(self.total_bars)),
                    "total_return_pct": canonical_float(self.total_return_pct),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "equity_curve": self.equity_curve,
            "drawdown_curve": self.drawdown_curve,
            "final_equity": self.final_equity,
            "total_return_pct": self.total_return_pct,
            "max_drawdown_pct": self.max_drawdown_pct,
            "total_bars": self.total_bars,
            "num_trades": self.num_trades,
            "signal_reference": self.signal_reference,
            "input_hash": self.input_hash,
            "result_hash": self.result_hash,
            "calculation_version": self.calculation_version,
            "engine_version": self.engine_version,
            "bridge_version": self.bridge_version,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "BacktestResult":
        return cls(
            equity_curve=[float(x) for x in d.get("equity_curve", [])],
            drawdown_curve=[float(x) for x in d.get("drawdown_curve", [])],
            final_equity=float(d.get("final_equity", 0.0)),
            total_return_pct=float(d.get("total_return_pct", 0.0)),
            max_drawdown_pct=float(d.get("max_drawdown_pct", 0.0)),
            total_bars=int(d.get("total_bars", 0)),
            num_trades=int(d.get("num_trades", 0)),
            signal_reference=str(d.get("signal_reference", "")),
            input_hash=str(d.get("input_hash", "")),
            result_hash=str(d.get("result_hash", "")),
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
            engine_version=str(d.get("engine_version", "")),
            bridge_version=str(d.get("bridge_version", "")),
        )


# ── Performance ────────────────────────────────────────────────────────────


@dataclass
class PerformanceRequest:
    equity_curve: List[float] = field(default_factory=list)
    bars: List[Candle] = field(default_factory=list)
    initial_capital: float = 100_000.0
    trading_days_per_year: float = 252.0
    calculation_version: str = DEFAULT_CALCULATION_VERSION

    def compute_input_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "bars": _candles_canonical(self.bars),
                    "calculation_version": _q(self.calculation_version),
                    "equity_curve": canonical_float_array(self.equity_curve),
                    "initial_capital": canonical_float(self.initial_capital),
                    "trading_days_per_year": canonical_float(self.trading_days_per_year),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "equity_curve": self.equity_curve,
            "bars": _candles_to_dict(self.bars),
            "initial_capital": self.initial_capital,
            "trading_days_per_year": self.trading_days_per_year,
            "calculation_version": self.calculation_version,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "PerformanceRequest":
        return cls(
            equity_curve=[float(x) for x in d.get("equity_curve", [])],
            bars=[Candle.from_base_object(c) for c in d.get("bars", [])],
            initial_capital=float(d.get("initial_capital", 100_000.0)),
            trading_days_per_year=float(d.get("trading_days_per_year", 252.0)),
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
        )


@dataclass
class PerformanceResult:
    total_return: float = 0.0
    total_return_pct: float = 0.0
    annualized_return: float = 0.0
    annualized_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    downside_deviation_annualized: float = 0.0
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0
    cvar_99: float = 0.0
    time_in_drawdown_pct: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    num_drawdown_periods: int = 0
    num_yearly_periods: int = 0
    num_monthly_periods: int = 0
    max_drawdown_recovery_bars: int = 0
    input_hash: str = ""
    result_hash: str = ""
    calculation_version: str = DEFAULT_CALCULATION_VERSION
    engine_version: str = ""
    bridge_version: str = ""

    def compute_result_hash(self) -> str:
        return _sha256(
            canonical_object(
                {
                    "annualized_return": canonical_float(self.annualized_return),
                    "annualized_volatility": canonical_float(self.annualized_volatility),
                    "bridge_version": _q(self.bridge_version),
                    "calmar_ratio": canonical_float(self.calmar_ratio),
                    "calculation_version": _q(self.calculation_version),
                    "cvar_95": canonical_float(self.cvar_95),
                    "cvar_99": canonical_float(self.cvar_99),
                    "downside_deviation_annualized": canonical_float(
                        self.downside_deviation_annualized
                    ),
                    "engine_version": _q(self.engine_version),
                    "input_hash": _q(self.input_hash),
                    "losing_trades": canonical_float(float(self.losing_trades)),
                    "max_drawdown_pct": canonical_float(self.max_drawdown_pct),
                    "max_drawdown_recovery_bars": canonical_float(
                        float(self.max_drawdown_recovery_bars)
                    ),
                    "num_drawdown_periods": canonical_float(float(self.num_drawdown_periods)),
                    "num_monthly_periods": canonical_float(float(self.num_monthly_periods)),
                    "num_yearly_periods": canonical_float(float(self.num_yearly_periods)),
                    "profit_factor": canonical_float(self.profit_factor),
                    "sharpe_ratio": canonical_float(self.sharpe_ratio),
                    "sortino_ratio": canonical_float(self.sortino_ratio),
                    "time_in_drawdown_pct": canonical_float(self.time_in_drawdown_pct),
                    "total_return": canonical_float(self.total_return),
                    "total_return_pct": canonical_float(self.total_return_pct),
                    "total_trades": canonical_float(float(self.total_trades)),
                    "var_95": canonical_float(self.var_95),
                    "var_99": canonical_float(self.var_99),
                    "win_rate": canonical_float(self.win_rate),
                    "winning_trades": canonical_float(float(self.winning_trades)),
                }
            )
        )

    def to_base_object(self) -> Dict[str, Any]:
        return {
            "total_return": self.total_return,
            "total_return_pct": self.total_return_pct,
            "annualized_return": self.annualized_return,
            "annualized_volatility": self.annualized_volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "max_drawdown_pct": self.max_drawdown_pct,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "downside_deviation_annualized": self.downside_deviation_annualized,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "cvar_95": self.cvar_95,
            "cvar_99": self.cvar_99,
            "time_in_drawdown_pct": self.time_in_drawdown_pct,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "num_drawdown_periods": self.num_drawdown_periods,
            "num_yearly_periods": self.num_yearly_periods,
            "num_monthly_periods": self.num_monthly_periods,
            "max_drawdown_recovery_bars": self.max_drawdown_recovery_bars,
            "input_hash": self.input_hash,
            "result_hash": self.result_hash,
            "calculation_version": self.calculation_version,
            "engine_version": self.engine_version,
            "bridge_version": self.bridge_version,
        }

    @classmethod
    def from_base_object(cls, d: Dict[str, Any]) -> "PerformanceResult":
        return cls(
            total_return=float(d.get("total_return", 0.0)),
            total_return_pct=float(d.get("total_return_pct", 0.0)),
            annualized_return=float(d.get("annualized_return", 0.0)),
            annualized_volatility=float(d.get("annualized_volatility", 0.0)),
            sharpe_ratio=float(d.get("sharpe_ratio", 0.0)),
            sortino_ratio=float(d.get("sortino_ratio", 0.0)),
            calmar_ratio=float(d.get("calmar_ratio", 0.0)),
            max_drawdown_pct=float(d.get("max_drawdown_pct", 0.0)),
            win_rate=float(d.get("win_rate", 0.0)),
            profit_factor=float(d.get("profit_factor", 0.0)),
            downside_deviation_annualized=float(d.get("downside_deviation_annualized", 0.0)),
            var_95=float(d.get("var_95", 0.0)),
            var_99=float(d.get("var_99", 0.0)),
            cvar_95=float(d.get("cvar_95", 0.0)),
            cvar_99=float(d.get("cvar_99", 0.0)),
            time_in_drawdown_pct=float(d.get("time_in_drawdown_pct", 0.0)),
            total_trades=int(d.get("total_trades", 0)),
            winning_trades=int(d.get("winning_trades", 0)),
            losing_trades=int(d.get("losing_trades", 0)),
            num_drawdown_periods=int(d.get("num_drawdown_periods", 0)),
            num_yearly_periods=int(d.get("num_yearly_periods", 0)),
            num_monthly_periods=int(d.get("num_monthly_periods", 0)),
            max_drawdown_recovery_bars=int(d.get("max_drawdown_recovery_bars", 0)),
            input_hash=str(d.get("input_hash", "")),
            result_hash=str(d.get("result_hash", "")),
            calculation_version=str(d.get("calculation_version", DEFAULT_CALCULATION_VERSION)),
            engine_version=str(d.get("engine_version", "")),
            bridge_version=str(d.get("bridge_version", "")),
        )


# Alias for contract naming: a PerformanceReport IS a PerformanceResult.
PerformanceReport = PerformanceResult
