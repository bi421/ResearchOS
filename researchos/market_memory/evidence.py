"""
Evidence — provenance and evidence tracking for market memory research.

Every important research finding must contain provenance:
  - dataset identity
  - dataset version/hash
  - event definition
  - condition definition
  - sample size
  - time range
  - computation method
  - code/module responsible
  - statistical method
  - random seed where applicable
  - validation method
  - result
  - uncertainty
  - status
"""

from __future__ import annotations

from typing import Any

from researchos.market_memory.event_schema import EvidenceRecord, EvidenceStatus


def create_evidence_record(
    finding_name: str,
    dataset_id: str,
    dataset_version: str,
    event_definition: str,
    condition_definition: str,
    sample_size: int,
    time_range: tuple[str, str],
    computation_method: str,
    code_module: str,
    statistical_method: str,
    result: dict[str, Any],
    uncertainty: dict[str, Any] | None = None,
    validation_method: str = "",
    random_seed: int | None = None,
    status: str = EvidenceStatus.EXPLORATORY.value,
) -> EvidenceRecord:
    """
    Create an evidence record for a research finding.

    Args:
        finding_name: Human-readable name
        dataset_id: Dataset identifier
        dataset_version: Dataset version/hash
        event_definition: How events were defined
        condition_definition: What condition was tested
        sample_size: Number of events in the analysis
        time_range: (start, end) timestamps
        computation_method: How results were computed
        code_module: Python module responsible
        statistical_method: Statistical method used
        result: Computed results
        uncertainty: Uncertainty quantification
        validation_method: Validation approach
        random_seed: Random seed if applicable
        status: Evidence status

    Returns:
        EvidenceRecord
    """
    finding_id = f"EVIDENCE|{dataset_id}|{finding_name}|{condition_definition}|{time_range[0]}"
    return EvidenceRecord(
        finding_id=finding_id,
        finding_name=finding_name,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        event_definition=event_definition,
        condition_definition=condition_definition,
        sample_size=sample_size,
        time_range=time_range,
        computation_method=computation_method,
        code_module=code_module,
        statistical_method=statistical_method,
        random_seed=random_seed,
        validation_method=validation_method,
        result=result,
        uncertainty=uncertainty or {},
        status=status,
    )
