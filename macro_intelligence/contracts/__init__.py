"""
ResearchOS Macro Intelligence Layer - Contracts Package
"""

from macro_intelligence.contracts.enums import (
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
from macro_intelligence.contracts.event import MacroEvent, MarketRelevance
from macro_intelligence.contracts.evidence import (
    CheckResult,
    EvidenceObject,
    ProvenanceChain,
    RevisionRef,
    Transformation,
)
from macro_intelligence.contracts.knowledge import (
    KnowledgeObject,
    Pattern,
    StatisticalAnalysis,
)
from macro_intelligence.contracts.reaction import (
    MarketReaction,
    ReactionMetrics,
    StatisticalSupport,
    WindowSpec,
)
from macro_intelligence.contracts.registry import (
    SERIES_RANGES,
    SUPPORTED_SERIES,
    get_all_series_ids,
    get_series_metadata,
    is_supported_series,
)
from macro_intelligence.contracts.series import NormalizedSeries

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
