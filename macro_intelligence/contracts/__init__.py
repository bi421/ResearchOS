"""
ResearchOS Macro Intelligence Layer - Contracts Package
"""

from macro_intelligence.contracts.enums import (
    ErrorType,
    HealthStatus,
    Severity,
    FrequencyEnum,
    SeriesType,
    EventCategory,
    ImportanceLevel,
    AlertType,
    QuarantineStatus,
    PatternType,
    InflationRegime,
    GrowthRegime,
    MonetaryRegime,
    RiskRegime,
)

from macro_intelligence.contracts.series import NormalizedSeries
from macro_intelligence.contracts.evidence import (
    EvidenceObject,
    RevisionRef,
    Transformation,
    CheckResult,
    ProvenanceChain,
)
from macro_intelligence.contracts.event import MacroEvent, MarketRelevance
from macro_intelligence.contracts.reaction import (
    MarketReaction,
    WindowSpec,
    ReactionMetrics,
    StatisticalSupport,
)
from macro_intelligence.contracts.knowledge import (
    KnowledgeObject,
    Pattern,
    StatisticalAnalysis,
)
from macro_intelligence.contracts.registry import (
    SUPPORTED_SERIES,
    SERIES_RANGES,
    get_series_metadata,
    is_supported_series,
    get_all_series_ids,
)

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
