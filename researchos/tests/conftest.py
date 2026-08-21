from datetime import datetime, timezone
import pytest
from researchos import Observation, Hypothesis, Research, Scenario, ScenarioSet


@pytest.fixture
def sample_research():
    return Research(question="Test?", time_horizon="Monthly", asset="TEST")


@pytest.fixture
def sample_observation():
    return Observation(
        source="TEST:SOURCE",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
        value=42.0,
        unit="test",
    )


@pytest.fixture
def sample_hypothesis(sample_research):
    return Hypothesis(
        research_id=sample_research.id,
        type="Primary",
        statement="Test",
        evidence_strength=0.7,
        coherence=0.8,
        plausibility=0.9,
        falsifiability=0.6,
    )


@pytest.fixture
def sample_scenario_set(sample_research, sample_hypothesis):
    ss = ScenarioSet(research_id=sample_research.id)
    ss.add_scenario(Scenario(hypothesis_id=sample_hypothesis.id, type="Base", probability=0.5))
    ss.add_scenario(Scenario(hypothesis_id=sample_hypothesis.id, type="Bull", probability=0.3))
    ss.add_scenario(Scenario(hypothesis_id=sample_hypothesis.id, type="Bear", probability=0.2))
    ss.normalize_probabilities()
    return ss
