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

import hashlib
import json
from typing import Any

from researchos.market_memory.event_schema import EvidenceRecord, EvidenceStatus


def compute_evidence_provenance_digest(
    *,
    dataset_id: str,
    dataset_version: str,
    finding_name: str,
    event_definition: str,
    condition_definition: str,
    sample_size: int,
    time_range: tuple[str, str],
    computation_method: str,
    statistical_method: str,
    validation_method: str,
    random_seed: int | None,
    result: dict[str, Any],
) -> str:
    """Return a deterministic SHA-256 identity for an evidence computation.

    The digest binds the finding identity to the dataset content/version and
    to the exact research inputs/results represented by the record.  Callers
    should supply a content hash as ``dataset_version`` when certifying real
    evidence; the function itself never invents a data identity.
    """
    payload = {
        "dataset_id": dataset_id,
        "dataset_version": dataset_version,
        "finding_name": finding_name,
        "event_definition": event_definition,
        "condition_definition": condition_definition,
        "sample_size": sample_size,
        "time_range": list(time_range),
        "computation_method": computation_method,
        "statistical_method": statistical_method,
        "validation_method": validation_method,
        "random_seed": random_seed,
        "result": result,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
    """Create an evidence record with a content-bound provenance identity."""
    provenance_digest = compute_evidence_provenance_digest(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        finding_name=finding_name,
        event_definition=event_definition,
        condition_definition=condition_definition,
        sample_size=sample_size,
        time_range=time_range,
        computation_method=computation_method,
        statistical_method=statistical_method,
        validation_method=validation_method,
        random_seed=random_seed,
        result=result,
    )
    finding_id = f"EVIDENCE|{dataset_id}|{finding_name}|{condition_definition}|{time_range[0]}|{provenance_digest[:16]}"
    record_uncertainty = dict(uncertainty or {})
    record_uncertainty["provenance"] = {
        "algorithm": "sha256",
        "evidence_computation_digest": provenance_digest,
        "dataset_version_bound": dataset_version,
    }
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
        uncertainty=record_uncertainty,
        status=status,
    )
