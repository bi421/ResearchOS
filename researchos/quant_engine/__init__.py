"""
Quant Computation Engine — high-performance numerical computation layer.

Purpose:
    Provide a clean abstraction for historical market research, simulation,
    and statistical analysis. This is a COMPUTATION LAYER only — NOT a trading
    engine, NOT execution logic, NOT a signal generator.

Architecture:
    ResearchOS (Python)
            │
            ▼
    QuantComputationInterface (abstract)
            │
            ├── PythonQuantBackend (current)
            └── CppQuantBackend (future: C++20 + CMake + pybind11)

Workflow:
    Historical Scenario
            ↓
    SimulationRequest
            ↓
    Quant Computation Engine
            ↓
    SimulationResult
            ↓
    ExperimentResult (from Experiment Framework)
            ↓
    Validation (from Validation System)

Design Principles:
    - Deterministic: Same inputs → same outputs
    - Versioned: CalculationVersion tracks methodology
    - Auditable: Full provenance in every SimulationResult
    - C++ Ready: Abstract interface for future C++ backend
    - No ML: Pure Python, no external dependencies

Based on Article XVII: Object Model — Quant Engine Layer.
"""

from researchos.quant_engine.interface import QuantComputationInterface
from researchos.quant_engine.backend import PythonQuantBackend
from researchos.quant_engine.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)
from researchos.quant_engine.simulation import HistoricalSimulationEngine
from researchos.quant_engine.statistics import (
    calculate_returns_from_prices,
    compute_statistics,
    mean,
    standard_deviation,
    variance,
    skewness,
    kurtosis,
    z_score,
    rolling_volatility,
    volatility_change,
)
from researchos.quant_engine.performance import (
    win_rate,
    loss_rate,
    average_win,
    average_loss,
    win_loss_ratio,
    profit_factor,
    consistency,
    max_consecutive_wins,
    max_consecutive_losses,
    distribution_analysis,
    compute_performance_analytics,
)
from researchos.quant_engine.metrics import (
    sharpe_ratio,
    sortino_ratio,
    calmar_ratio,
    profit_factor_metric,
    max_drawdown,
    downside_deviation,
    compute_all_metrics,
)

__all__ = [
    # Interface
    "QuantComputationInterface",
    "PythonQuantBackend",
    # Models
    "CalculationVersion",
    "SimulationRequest",
    "SimulationResult",
    # Engine
    "HistoricalSimulationEngine",
    # Statistics
    "calculate_returns_from_prices",
    "compute_statistics",
    "mean",
    "standard_deviation",
    "variance",
    "skewness",
    "kurtosis",
    "z_score",
    "rolling_volatility",
    "volatility_change",
    # Performance
    "win_rate",
    "loss_rate",
    "average_win",
    "average_loss",
    "win_loss_ratio",
    "profit_factor",
    "consistency",
    "max_consecutive_wins",
    "max_consecutive_losses",
    "distribution_analysis",
    "compute_performance_analytics",
    # Metrics
    "sharpe_ratio",
    "sortino_ratio",
    "calmar_ratio",
    "profit_factor_metric",
    "max_drawdown",
    "downside_deviation",
    "compute_all_metrics",
]
