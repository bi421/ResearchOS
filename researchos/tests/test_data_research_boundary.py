from datetime import datetime, timezone

import pytest

from researchos.data_engine.boundary import (
    DATA_BOUNDARY_SCHEMA_VERSION,
    ValidatedDatasetRef,
    validated_dataset_ref,
)
from researchos.data_engine.candle import Candle
from researchos.data_engine.contracts import ValidationReport
from researchos.data_engine.dataset import HistoricalDataset
from researchos.research_boundary import (
    RESEARCH_BOUNDARY_SCHEMA_VERSION,
    ResearchEvidenceLink,
    ResearchInput,
)


def _dataset() -> HistoricalDataset:
    dataset = HistoricalDataset("XAUUSD", "1h", source="test")
    dataset.add_record(
        Candle(
            symbol="XAUUSD",
            timeframe="1h",
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            open=2000,
            high=2010,
            low=1990,
            close=2005,
            volume=100,
        )
    )
    dataset.mark_ready()
    dataset.mark_validated()
    return dataset


def test_validated_dataset_ref_contains_content_identity() -> None:
    dataset = _dataset()
    validation = ValidationReport(total_records=1, valid_records=1)

    ref = validated_dataset_ref(dataset, validation)

    assert ref.schema_version == DATA_BOUNDARY_SCHEMA_VERSION
    assert ref.dataset_id == dataset.id
    assert ref.dataset_content_hash == dataset.dataset_content_hash
    assert ref.dataset_hash == dataset.dataset_hash
    assert ref.is_valid is True


def test_unvalidated_dataset_cannot_cross_boundary() -> None:
    dataset = HistoricalDataset("XAUUSD", "1h", source="test")
    validation = ValidationReport(total_records=0)

    with pytest.raises(ValueError, match="DatasetStatus.VALIDATED"):
        validated_dataset_ref(dataset, validation)


def test_validation_errors_cannot_cross_boundary() -> None:
    dataset = _dataset()
    validation = ValidationReport(total_records=1, valid_records=0, errors=["bad OHLC"])

    with pytest.raises(ValueError, match="validation errors"):
        validated_dataset_ref(dataset, validation)


def test_validation_record_count_must_match_dataset() -> None:
    dataset = _dataset()
    validation = ValidationReport(total_records=2, valid_records=2)

    with pytest.raises(ValueError, match="record count"):
        validated_dataset_ref(dataset, validation)


def test_research_input_round_trip_is_deterministic() -> None:
    dataset = _dataset()
    ref = validated_dataset_ref(dataset, ValidationReport(total_records=1, valid_records=1))
    request = ResearchInput(
        schema_version=RESEARCH_BOUNDARY_SCHEMA_VERSION,
        research_id="research-001",
        question="Does XAUUSD exhibit a repeatable H1 event response?",
        methodology_version="event-study.v1",
        dataset=ref,
    )

    restored = ResearchInput.from_dict(request.to_dict())

    assert restored == request
    assert restored.dataset.dataset_content_hash == dataset.dataset_content_hash


def test_research_input_rejects_invalid_dataset_reference() -> None:
    ref = ValidatedDatasetRef(
        schema_version=DATA_BOUNDARY_SCHEMA_VERSION,
        dataset_id="dataset-001",
        dataset_content_hash="content-hash",
        dataset_hash="dataset-hash",
        symbol="XAUUSD",
        timeframe="1h",
        data_type="candle",
        record_count=1,
        validation_quality_score=0.0,
        validation_errors=("bad OHLC",),
    )

    with pytest.raises(ValueError, match="valid validated-dataset"):
        ResearchInput(
            schema_version=RESEARCH_BOUNDARY_SCHEMA_VERSION,
            research_id="research-001",
            question="test",
            methodology_version="v1",
            dataset=ref,
        )


def test_research_evidence_link_preserves_lineage() -> None:
    link = ResearchEvidenceLink(
        schema_version=RESEARCH_BOUNDARY_SCHEMA_VERSION,
        research_id="research-001",
        dataset_id="dataset-001",
        dataset_content_hash="content-hash",
        evidence_collection_id="evidence-001",
        assessment_hash="assessment-hash",
        methodology_version="event-study.v1",
    )

    assert ResearchEvidenceLink.from_dict(link.to_dict()) == link
