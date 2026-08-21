from datetime import datetime, timezone
from researchos import (
    Confidence,
    ConfidenceReport,
    Contradiction,
    ContradictionReport,
    Evidence,
    Hypothesis,
    Observation,
    Research,
    Scenario,
    ScenarioSet,
)


def test_full_pipeline():
    research = Research(question="Will inflation moderate?", time_horizon="Monthly", asset="US")
    obs = Observation(
        source="MACRO:CPI_YOY",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
        value=3.2,
        unit="percent",
    )
    obs.validate()
    ev = Evidence(
        observation_id=obs.id,
        hypothesis_id="hyp1",
        interpretation="Inflation moderating",
        direction="Supporting",
    )
    ev.validate()
    hyp = Hypothesis(
        research_id=research.id,
        type="Primary",
        statement="Inflation will moderate",
        evidence_strength=0.8,
        coherence=0.7,
        plausibility=0.9,
        falsifiability=0.6,
    )
    hyp.validate()
    ss = ScenarioSet(research_id=research.id)
    ss.add_scenario(Scenario(hypothesis_id=hyp.id, type="Base", probability=0.5))
    ss.add_scenario(Scenario(hypothesis_id=hyp.id, type="Bull", probability=0.3))
    ss.add_scenario(Scenario(hypothesis_id=hyp.id, type="Bear", probability=0.2))
    ss.normalize_probabilities()
    conf = Confidence(target_id=hyp.id, score=0.75, rationale="Strong evidence")
    report = ConfidenceReport(research_id=research.id)
    report.add(conf)
    assert ev.observation_id == obs.id
    assert hyp.research_id == research.id
    assert abs(sum(s.probability for s in ss.scenarios) - 1.0) < 1e-9
    assert report.aggregate_score == 0.75
    research.complete()


def test_deterministic():
    for _ in range(50):
        o1 = Observation(
            source="DET:test",
            timestamp=datetime(2024, 6, 15, tzinfo=timezone.utc).isoformat(),
            value=1.0,
            unit="test",
        )
        o2 = Observation(
            source="DET:test",
            timestamp=datetime(2024, 6, 15, tzinfo=timezone.utc).isoformat(),
            value=1.0,
            unit="test",
        )
        assert o1.id == o2.id


def test_contradiction():
    obs_up = Observation(source="A", timestamp="2024-01-01T00:00:00+00:00", value=100.0, unit="usd")
    obs_down = Observation(
        source="B", timestamp="2024-01-01T00:00:00+00:00", value=100.0, unit="usd"
    )
    ev_up = Evidence(
        observation_id=obs_up.id,
        hypothesis_id="h1",
        interpretation="Bullish",
        direction="Supporting",
    )
    ev_down = Evidence(
        observation_id=obs_down.id,
        hypothesis_id="h1",
        interpretation="Bearish",
        direction="Contradicting",
    )
    contra = Contradiction(
        evidence_id_a=ev_up.id, evidence_id_b=ev_down.id, description="Bull vs Bear", severity=0.8
    )
    contra.validate()
    report = ContradictionReport(research_id="r1")
    report.add(contra)
    assert report.has_contradictions


def test_falsifiability():
    un = Hypothesis(
        research_id="r1",
        type="Primary",
        statement="Market will do something",
        evidence_strength=0.5,
        coherence=0.5,
        plausibility=0.5,
        falsifiability=0.1,
    )
    fa = Hypothesis(
        research_id="r1",
        type="Primary",
        statement="BTC above 100k by March 2026",
        evidence_strength=0.5,
        coherence=0.5,
        plausibility=0.5,
        falsifiability=0.9,
    )
    assert fa.falsifiability > un.falsifiability


def test_scenario_normalize():
    ss1 = ScenarioSet(research_id="r1")
    ss1.add_scenario(Scenario(hypothesis_id="h1", type="Base", probability=0.5))
    ss1.add_scenario(Scenario(hypothesis_id="h1", type="Bull", probability=0.3))
    ss1.add_scenario(Scenario(hypothesis_id="h1", type="Bear", probability=0.2))
    ss1.normalize_probabilities()
    assert abs(sum(s.probability for s in ss1.scenarios) - 1.0) < 1e-9
    ss3 = ScenarioSet(research_id="r1")
    ss3.add_scenario(Scenario(hypothesis_id="h1", type="Base", probability=0.0))
    ss3.add_scenario(Scenario(hypothesis_id="h1", type="Bull", probability=0.0))
    raised = False
    try:
        ss3.normalize_probabilities()
    except ValueError:
        raised = True
    assert raised
