"""
C++ Quant Acceleration Engine — Python integration package.

This package exposes the stable Python/C++ integration contract for the
ResearchOS numerical layer:

    * ``CppQuantEngineBackend``  — typed backend mirroring the C++ bridge.
    * ``MarketData``             — candle series + provenance hashing.
    * ``SimulationRequest/Result`` — deterministic historical simulation.
    * ``Statistics``             — descriptive statistics (C++).
    * ``Risk``                   — VaR / CVaR / drawdown / ratios (C++).
    * ``BacktestEngine``         — backtest facade (bridge transports the
                                   caller's signal; implements no trading logic).
    * ``PerformanceReport``      — full performance analysis over an equity curve.
    * ``models``                 — BaseObject models with cross-language hashes.
    * ``exceptions``             — typed bridge errors with stable numeric codes.

Architecture:
    ResearchOS Python
        |
        v
    cpp_quant_engine (this package)
        |
        |  plain dicts (BaseObjects)
        v
    cpp_quant_backend (pybind11 module, C++20)
        |
        v
    IBridgeBackend / quant engine
"""

from researchos.engines.quant.cpp_engine.backend import (
    BacktestEngine,
    CppQuantEngineBackend,
    Risk,
    Simulation,
    Statistics,
    bridge_version,
    default_backend,
    engine_version,
    error_codes,
    native_module,
    protocol_version,
    supported_calculation_versions,
)
from researchos.engines.quant.cpp_engine.exceptions import (
    BridgeError,
    EmptyDataError,
    HashMismatchError,
    InsufficientDataError,
    InternalError,
    InvalidArgumentError,
    InvalidParameterError,
    InvalidTypeError,
    MalformedDataError,
    OutOfBoundsError,
    UnsupportedVersionError,
    ValidationFailedError,
)
from researchos.engines.quant.cpp_engine.models import (
    BacktestRequest,
    BacktestResult,
    Candle,
    MarketData,
    MarketDataRequest,
    MarketDataResult,
    PerformanceReport,
    PerformanceRequest,
    PerformanceResult,
    RiskRequest,
    RiskResult,
    SimulationRequest,
    SimulationResult,
    StatisticsRequest,
    StatisticsResult,
)

try:  # Optional legacy shim; requires the ResearchOS package tree.
    from researchos.engines.quant.cpp_engine.backend_wrapper import CppQuantBackendWrapper
except Exception:  # pragma: no cover - environment dependent
    CppQuantBackendWrapper = None  # type: ignore[assignment]

__all__ = [
    "CppQuantEngineBackend",
    "default_backend",
    "BacktestEngine",
    "Statistics",
    "Risk",
    "Simulation",
    "MarketData",
    "Candle",
    "MarketDataRequest",
    "MarketDataResult",
    "StatisticsRequest",
    "StatisticsResult",
    "RiskRequest",
    "RiskResult",
    "SimulationRequest",
    "SimulationResult",
    "BacktestRequest",
    "BacktestResult",
    "PerformanceRequest",
    "PerformanceResult",
    "PerformanceReport",
    "BridgeError",
    "InvalidArgumentError",
    "InvalidParameterError",
    "InvalidTypeError",
    "InsufficientDataError",
    "EmptyDataError",
    "MalformedDataError",
    "OutOfBoundsError",
    "UnsupportedVersionError",
    "ValidationFailedError",
    "HashMismatchError",
    "InternalError",
    "engine_version",
    "bridge_version",
    "protocol_version",
    "supported_calculation_versions",
    "error_codes",
    "native_module",
    "CppQuantBackendWrapper",
]
