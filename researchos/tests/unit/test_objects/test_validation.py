import pytest
from researchos import Evidence, Hypothesis, Observation, Scenario, ScenarioSet


def test_observation_valid():
    o = Observation(source="A", timestamp="2024-01-01T00:00:00+00:00", value=1.0, unit="t")
    o.validate()


def test_observation_invalid_empty_source():
    o = Observation(source="", timestamp="2024-01-01T00:00:00+00:00", value=1.0, unit="t")
    with pytest.raises(ValueError, match="source"):
        o.validate()


def test_evidence_invalid_direction():
    e = Evidence(observation_id="o1", hypothesis_id="h1", interpretation="test", direction="Maybe")
    with pytest.raises(ValueError, match="direction"):
        e.validate()


def test_hypothesis_scores_clamped():
    with pytest.raises(ValueError, match="evidence_strength"):
        Hypothesis(
            research_id="r1",
            type="Primary",
            statement="test",
            evidence_strength=1.5,
            coherence=0.5,
            plausibility=0.5,
            falsifiability=0.5,
        )


def test_scenario_invalid_type():
    s = Scenario(hypothesis_id="h1", type="Sideways", probability=0.5)
    with pytest.raises(ValueError, match="type"):
        s.validate()


def test_scenario_normalize_empty_raises():
    ss = ScenarioSet(research_id="r1")
    with pytest.raises(ValueError, match="empty"):
        ss.normalize_probabilities()
