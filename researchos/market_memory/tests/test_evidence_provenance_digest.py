from researchos.market_memory.evidence import compute_evidence_provenance_digest, create_evidence_record


def _kwargs(dataset_version: str = "sha256:abc", result=None):
    return {
        "dataset_id": "XAUUSD_D1_sha256:abc",
        "dataset_version": dataset_version,
        "finding_name": "bullish_crossover",
        "event_definition": "SMA20/100 crossover",
        "condition_definition": "{'direction':'bullish'}",
        "sample_size": 100,
        "time_range": ("2021-01-01T00:00:00+00:00", "2021-12-31T00:00:00+00:00"),
        "computation_method": "forward_return_analysis",
        "statistical_method": "wilson",
        "validation_method": "walk_forward",
        "random_seed": 42,
        "result": result or {"mean_return": 0.01},
    }


def test_provenance_digest_is_deterministic():
    assert compute_evidence_provenance_digest(**_kwargs()) == compute_evidence_provenance_digest(**_kwargs())


def test_dataset_version_changes_provenance_digest():
    assert compute_evidence_provenance_digest(**_kwargs("sha256:abc")) != compute_evidence_provenance_digest(**_kwargs("sha256:def"))


def test_result_changes_finding_identity_and_provenance():
    first = create_evidence_record(result={"mean_return": 0.01}, **{k: v for k, v in _kwargs().items() if k != "result"})
    second = create_evidence_record(result={"mean_return": 0.02}, **{k: v for k, v in _kwargs().items() if k != "result"})
    assert first.finding_id != second.finding_id
    assert first.uncertainty["provenance"]["evidence_computation_digest"] != second.uncertainty["provenance"]["evidence_computation_digest"]
