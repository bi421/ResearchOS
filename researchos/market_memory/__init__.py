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
    - MacroState: Macroeconomic conditions snapshot
    - HistoricalScenario: Complete market scenario for comparison
    - ScenarioMatcher: Deterministic similarity matching engine
    - OutcomeAnalysis: Historical outcome statistics
    - MarketMemoryReport: Consolidated analysis report
    - MarketMemoryIntegrator: Adapter-based system integration
"""

from researchos.market_memory.models import (
    MarketSnapshot,
    MarketRegime,
    MacroState,
    HistoricalScenario,
)
from researchos.market_memory.repository import MarketMemoryRepository
from researchos.market_memory.features import compute_features, FeatureSet
from researchos.market_memory.similarity import compare_snapshots, find_similar_snapshots, compare_scenarios
from researchos.market_memory.matcher import ScenarioMatcher, MatchResult, DEFAULT_FEATURE_WEIGHTS
from researchos.market_memory.outcome_analysis import OutcomeAnalysis, OutcomeAnalysisResult
from researchos.market_memory.report import MarketMemoryReport
from researchos.market_memory.integration import MarketMemoryIntegrator, IntegrationContext
from researchos.market_memory.events import MarketEvent

__all__ = [
    "MarketSnapshot",
    "MarketRegime",
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
    "MarketEvent",
]
