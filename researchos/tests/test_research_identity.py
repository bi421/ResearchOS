import pytest

from researchos.research_identity import DatasetIdentity


def test_dataset_identity_matches_exact_content_identity():
    identity = DatasetIdentity("xauusd", "content-a", "dataset-a")
    assert identity.matches(
        dataset_id="xauusd",
        dataset_content_hash="content-a",
        dataset_hash="dataset-a",
    )


def test_dataset_identity_rejects_content_hash_mismatch():
    identity = DatasetIdentity("xauusd", "content-a", "dataset-a")
    with pytest.raises(ValueError, match="dataset identity mismatch"):
        identity.assert_matches(
            dataset_id="xauusd",
            dataset_content_hash="content-b",
            dataset_hash="dataset-a",
        )


def test_dataset_identity_rejects_dataset_hash_mismatch():
    identity = DatasetIdentity("xauusd", "content-a", "dataset-a")
    with pytest.raises(ValueError, match="dataset identity mismatch"):
        identity.assert_matches(
            dataset_id="xauusd",
            dataset_content_hash="content-a",
            dataset_hash="dataset-b",
        )
