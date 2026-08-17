"""
Evidence & Lineage — Phase 5.3a storage foundation.

Additive, append-only evidence repository and lineage graph layered on the
existing ``ResearchRepository``.  This module provides:

    - ``EvidenceEnvelope`` — the uniform, immutable artifact envelope.
    - ``EvidenceRepository`` — the append-only facade for artifacts and edges.

Constraints honored:
    - Append-only (no delete API, no update).
    - No modification of the existing experiment flow.
    - No artifact emission hooks yet.
    - No Model Registry implementation.
    - No replay execution.

This is a certification/trust layer only — it computes no trading decisions.
"""

from researchos.evidence.dataset_emission import (
    DATASET_ARTIFACT_TYPE,
    DATASET_EVIDENCE_VERSION,
    build_dataset_envelope,
    emit_dataset,
    make_dataset_envelope_from_payload,
    research_dataset_payload,
)
from researchos.evidence.envelope import (
    ARTIFACT_TYPES,
    ARTIFACT_TYPES_TUPLE,
    HASH_SCHEME_VERSION,
    EvidenceEnvelope,
    build_envelope,
    compute_artifact_hash,
    compute_lineage_hash,
)
from researchos.evidence.experiment_emission import (
    EXPERIMENT_ARTIFACT_TYPE,
    EXPERIMENT_EVIDENCE_VERSION,
    attach_dataset_parent,
    build_experiment_envelope,
    emit_experiment,
    emit_experiment_with_dataset,
    experiment_payload,
)
from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.result_emission import (
    RESULT_ARTIFACT_TYPE,
    RESULT_EVIDENCE_VERSION,
    RUN_TO_RESULT_RELATION,
    attach_run_parent,
    build_result_envelope,
    emit_result,
    emit_result_for_run,
    result_payload,
)
from researchos.evidence.run_emission import (
    EXPERIMENT_TO_RUN_RELATION,
    RUN_ARTIFACT_TYPE,
    RUN_EVIDENCE_VERSION,
    attach_experiment_parent,
    build_run_envelope,
    emit_run,
    emit_run_for_experiment,
    run_payload,
)
from researchos.evidence.validation_emission import (
    RESULT_TO_VALIDATION_RELATION,
    VALIDATION_ARTIFACT_TYPE,
    VALIDATION_EVIDENCE_VERSION,
    attach_result_parent,
    build_validation_envelope,
    emit_validation,
    emit_validation_for_result,
    validation_hash,
    validation_payload,
)

__all__ = [
    "ARTIFACT_TYPES",
    "ARTIFACT_TYPES_TUPLE",
    "HASH_SCHEME_VERSION",
    "EvidenceEnvelope",
    "EvidenceRepository",
    "build_envelope",
    "compute_artifact_hash",
    "compute_lineage_hash",
    # Dataset evidence emission (Phase 5.3b.1)
    "DATASET_ARTIFACT_TYPE",
    "DATASET_EVIDENCE_VERSION",
    "build_dataset_envelope",
    "emit_dataset",
    "make_dataset_envelope_from_payload",
    "research_dataset_payload",
    # Experiment evidence emission (Phase 5.3b.2)
    "EXPERIMENT_ARTIFACT_TYPE",
    "EXPERIMENT_EVIDENCE_VERSION",
    "attach_dataset_parent",
    "build_experiment_envelope",
    "emit_experiment",
    "emit_experiment_with_dataset",
    "experiment_payload",
    # Run evidence emission (Phase 5.3b.3)
    "EXPERIMENT_TO_RUN_RELATION",
    "RUN_ARTIFACT_TYPE",
    "RUN_EVIDENCE_VERSION",
    "attach_experiment_parent",
    "build_run_envelope",
    "emit_run",
    "emit_run_for_experiment",
    "run_payload",
    # Result evidence emission (Phase 5.3b.4)
    "RESULT_ARTIFACT_TYPE",
    "RESULT_EVIDENCE_VERSION",
    "RUN_TO_RESULT_RELATION",
    "attach_run_parent",
    "build_result_envelope",
    "emit_result",
    "emit_result_for_run",
    "result_payload",
    # Validation evidence emission (Phase 5.3b.5)
    "RESULT_TO_VALIDATION_RELATION",
    "VALIDATION_ARTIFACT_TYPE",
    "VALIDATION_EVIDENCE_VERSION",
    "attach_result_parent",
    "build_validation_envelope",
    "emit_validation",
    "emit_validation_for_result",
    "validation_hash",
    "validation_payload",
]
