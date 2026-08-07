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
from researchos.quant_engine.capabilities import (
    QUANT_OPERATIONS,
    REFERENCE_BACKEND_NAME,
    REFERENCE_BACKEND_VERSION,
    BackendCapabilities,
    BackendCapabilitiesError,
    default_capabilities,
)
from researchos.quant_engine.backend_hash import (
    HASH_ALGORITHM,
    HASH_VERSION,
    canonicalize,
    compute_backend_result_hash,
    compute_input_hash,
    stable_float,
)
from researchos.quant_engine.numerical_validation import (
    NumericalComparator,
    NumericalComparisonError,
    NumericalValidationResult,
    ValidationStatus,
)
from researchos.quant_engine.router import (
    ERROR_EXECUTION_FAILED,
    ERROR_NO_CANDIDATE,
    ERROR_OK,
    ERROR_TRUST_BOUNDARY,
    ERROR_VALIDATION_FAILED,
    BackendCapabilityError,
    BackendExecutionError,
    BackendExecutionMetadata,
    BackendExecutionResult,
    BackendRouter,
    BackendRouterError,
    BackendValidationError,
)
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
from researchos.quant_engine.research_interface import (
    RESEARCH_OPERATIONS,
    RESEARCH_SURFACE_VERSION,
    ResearchResult,
    ResearchComputationInterface,
    build_research_result,
)
from researchos.quant_engine.research_engine import (
    PythonResearchBackend,
    ResearchEngine,
    research_capabilities,
)
from researchos.quant_engine.research_cpp_backend import (
    ResearchCppBackend,
    has_cpp_research_engine,
)
from researchos.quant_engine.research_registry import (
    register_research_backend,
    create_research_router,
    create_research_engine,
)

__all__ = [
    # Interface
    "QuantComputationInterface",
    "PythonQuantBackend",
    # Certification (Phase 4.1)
    "QUANT_OPERATIONS",
    "REFERENCE_BACKEND_NAME",
    "REFERENCE_BACKEND_VERSION",
    "BackendCapabilities",
    "BackendCapabilitiesError",
    "default_capabilities",
    "HASH_ALGORITHM",
    "HASH_VERSION",
    "canonicalize",
    "compute_backend_result_hash",
    "compute_input_hash",
    "stable_float",
    "NumericalComparator",
    "NumericalComparisonError",
    "NumericalValidationResult",
    "ValidationStatus",
    "ERROR_OK",
    "ERROR_NO_CANDIDATE",
    "ERROR_EXECUTION_FAILED",
    "ERROR_VALIDATION_FAILED",
    "ERROR_TRUST_BOUNDARY",
    "BackendCapabilityError",
    "BackendExecutionError",
    "BackendExecutionMetadata",
    "BackendExecutionResult",
    "BackendRouter",
    "BackendRouterError",
    "BackendValidationError",
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
    # Research analytical surface (Phase 5.1)
    "RESEARCH_OPERATIONS",
    "RESEARCH_SURFACE_VERSION",
    "ResearchResult",
    "ResearchComputationInterface",
    "build_research_result",
    "PythonResearchBackend",
    "ResearchEngine",
    "research_capabilities",
    "ResearchCppBackend",
    "has_cpp_research_engine",
    "register_research_backend",
    "create_research_router",
    "create_research_engine",
]
