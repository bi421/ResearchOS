"""
Market Memory — Historical market knowledge layer for TRADER-OS.

Stores and retrieves past market states for pattern recognition,
regime analysis, scenario comparison, and outcome analysis.

Architecture:
    Market Observation → MarketSnapshot → HistoricalScenario →
    ScenarioMatcher → OutcomeAnalysis → MarketMemoryReport

Key objects:
    - MarketSnapshot: OHLCV + derived features at a point in time
    - MarketRegime: Classified market regime with confidence
    - MacroContextSnapshot: Macroeconomic conditions snapshot
    - HistoricalScenario: Complete market scenario for comparison
    - ScenarioMatcher: Deterministic similarity matching engine
    - OutcomeAnalysis: Historical outcome statistics
    - MarketMemoryReport: Consolidated analysis report
    - MarketMemoryIntegrator: Adapter-based system integration
"""

from researchos.market_memory.events import MacroMarketEvent, MarketEvent
from researchos.market_memory.event_schema import (
    BootstrapResult,
    ConditionSpec,
    ConditionalResult,
    CrossoverDirection,
    EvidenceRecord,
    EvidenceStatus,
    EventContext,
    EventOutcome,
    EventType,
    MarketEvent as MarketMemoryEvent,
    MarketRegime as MarketRegimeEnum,
    Session,
    SelfAuditResult,
    ValidationResult,
)
from researchos.market_memory.features import FeatureSet, compute_features
from researchos.market_memory.integration import IntegrationContext, MarketMemoryIntegrator
from researchos.market_memory.matcher import DEFAULT_FEATURE_WEIGHTS, MatchResult, ScenarioMatcher
from researchos.market_memory.models import (
    HistoricalScenario,
    MacroContextSnapshot,
    MacroState,
    MarketRegime,
    MarketSnapshot,
)
from researchos.market_memory.outcome_analysis import OutcomeAnalysis, OutcomeAnalysisResult
from researchos.market_memory.report import MarketMemoryReport
from researchos.market_memory.repository import MarketMemoryRepository
from researchos.market_memory.similarity import (
    compare_scenarios,
    compare_snapshots,
    find_similar_snapshots,
)

__all__ = [
    "MarketSnapshot",
    "MarketRegime",
    # Canonical names; MacroState / MarketEvent are deprecated aliases
    "MacroContextSnapshot",
    "MacroState",
    "HistoricalScenario",
    "MarketMemoryRepository",
    "compute_features",
    "FeatureSet",
    "compare_snapshots",
    "find_similar_snapshots",
    "compare_scenarios",
    "ScenarioMatcher",
    "MatchResult",
    "DEFAULT_FEATURE_WEIGHTS",
    "OutcomeAnalysis",
    "OutcomeAnalysisResult",
    "MarketMemoryReport",
    "MarketMemoryIntegrator",
    "IntegrationContext",
    "MacroMarketEvent",
    "MarketEvent",
    # V1 Event Schema
    "EventType",
    "CrossoverDirection",
    "MarketRegimeEnum",
    "Session",
    "EvidenceStatus",
    "EventOutcome",
    "EventContext",
    "MarketMemoryEvent",
    "ConditionSpec",
    "ConditionalResult",
    "BootstrapResult",
    "ValidationResult",
    "EvidenceRecord",
    "SelfAuditResult",
]
