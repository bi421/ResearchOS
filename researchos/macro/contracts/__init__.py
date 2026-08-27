"""
ResearchOS Macro Intelligence Layer - Contracts Package
"""

from researchos.macro.contracts.enums import (
    AlertType,
    ErrorType,
    EventCategory,
    FrequencyEnum,
    GrowthRegime,
    HealthStatus,
    ImportanceLevel,
    InflationRegime,
    MonetaryRegime,
    PatternType,
    QuarantineStatus,
    RiskRegime,
    SeriesType,
    Severity,
)
from researchos.macro.contracts.event import MacroEvent, MarketRelevance
from researchos.macro.contracts.evidence import (
    CheckResult,
    EvidenceObject,
    ProvenanceChain,
    RevisionRef,
    Transformation,
)
from researchos.macro.contracts.knowledge import (
    KnowledgeObject,
    Pattern,
    StatisticalAnalysis,
)
from researchos.macro.contracts.reaction import (
    MarketReaction,
    ReactionMetrics,
    StatisticalSupport,
    WindowSpec,
)
from researchos.macro.contracts.registry import (
    SERIES_RANGES,
    SUPPORTED_SERIES,
    get_all_series_ids,
    get_series_metadata,
    is_supported_series,
)
from researchos.macro.contracts.series import NormalizedSeries

__all__ = [
    # Enums
    "ErrorType",
    "HealthStatus",
    "Severity",
    "FrequencyEnum",
    "SeriesType",
    "EventCategory",
    "ImportanceLevel",
    "AlertType",
    "QuarantineStatus",
    "PatternType",
    "InflationRegime",
    "GrowthRegime",
    "MonetaryRegime",
    "RiskRegime",
    # Contracts
    "NormalizedSeries",
    "EvidenceObject",
    "RevisionRef",
    "Transformation",
    "CheckResult",
    "ProvenanceChain",
    "MacroEvent",
    "MarketRelevance",
    "MarketReaction",
    "WindowSpec",
    "ReactionMetrics",
    "StatisticalSupport",
    "KnowledgeObject",
    "Pattern",
    "StatisticalAnalysis",
    # Registry
    "SUPPORTED_SERIES",
    "SERIES_RANGES",
    "get_series_metadata",
    "is_supported_series",
    "get_all_series_ids",
]
