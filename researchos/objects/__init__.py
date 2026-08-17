"""ResearchOS object classes — the entities that flow through the reasoning pipeline."""

from researchos.objects.attribution import Attribution, AttributionGraph
from researchos.objects.cognitive import Bias, CognitiveAssessment, LearningRecord
from researchos.objects.confidence import Confidence, ConfidenceReport
from researchos.objects.contradiction import Contradiction, ContradictionReport
from researchos.objects.evidence import Evidence, EvidenceRegistry
from researchos.objects.hypothesis import Hypothesis, HypothesisSet
from researchos.objects.interpretation import Interpretation, Narrative
from researchos.objects.knowledge import Knowledge, Lesson, Pattern
from researchos.objects.macro import (
    CentralBankDemand,
    DollarStrengthSnapshot,
    EconomicGrowthAssessment,
    FedPolicyAssessment,
    InflationAssessment,
    LaborMarketAssessment,
    MacroProbability,
    MacroRegime,
    MacroReport,
    MacroScore,
    PhysicalDemandSnapshot,
    PositioningAssessment,
    RealYieldSnapshot,
    SafeHavenAssessment,
)
from researchos.objects.observation import MacroState, MarketState, Observation
from researchos.objects.process import AuditEntry, ReasoningChain, ResearchCycle
from researchos.objects.research import Research, ResearchQuestion, ResearchReport
from researchos.objects.scenario import Scenario, ScenarioSet
from researchos.objects.validation import FailureAnalysis, Validation

__all__ = [
    "Observation",
    "MarketState",
    "MacroState",
    "Evidence",
    "EvidenceRegistry",
    "Interpretation",
    "Narrative",
    "Hypothesis",
    "HypothesisSet",
    "Scenario",
    "ScenarioSet",
    "Confidence",
    "ConfidenceReport",
    "Contradiction",
    "ContradictionReport",
    "Knowledge",
    "Pattern",
    "Lesson",
    "Research",
    "ResearchReport",
    "ResearchQuestion",
    "Validation",
    "FailureAnalysis",
    "Bias",
    "LearningRecord",
    "CognitiveAssessment",
    "ResearchCycle",
    "ReasoningChain",
    "AuditEntry",
    "Attribution",
    "AttributionGraph",
    "RealYieldSnapshot",
    "DollarStrengthSnapshot",
    "FedPolicyAssessment",
    "InflationAssessment",
    "LaborMarketAssessment",
    "EconomicGrowthAssessment",
    "SafeHavenAssessment",
    "CentralBankDemand",
    "PhysicalDemandSnapshot",
    "PositioningAssessment",
    "MacroScore",
    "MacroProbability",
    "MacroRegime",
    "MacroReport",
]
