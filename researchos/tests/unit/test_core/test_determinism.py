from datetime import datetime, timezone
from researchos import Evidence, Observation


def test_same_observation_same_id():
    ids = set()
    for _ in range(100):
        o = Observation(
            source="A",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
            value=1.0,
            unit="t",
        )
        ids.add(o.id)
    assert len(ids) == 1


def test_different_observations_different_ids():
    o1 = Observation(source="A", timestamp="2024-01-01T00:00:00+00:00", value=1.0, unit="t")
    o2 = Observation(source="B", timestamp="2024-01-01T00:00:00+00:00", value=1.0, unit="t")
    o3 = Observation(source="A", timestamp="2024-01-02T00:00:00+00:00", value=1.0, unit="t")
    o4 = Observation(source="A", timestamp="2024-01-01T00:00:00+00:00", value=2.0, unit="t")
    assert len({o1.id, o2.id, o3.id, o4.id}) == 4


def test_evidence_deterministic():
    ids = set()
    for _ in range(100):
        e = Evidence(
            observation_id="obs1",
            hypothesis_id="hyp1",
            interpretation="test",
            direction="Supporting",
        )
        ids.add(e.id)
    assert len(ids) == 1
