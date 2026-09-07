"""Evidence & Lineage — append-only evidence storage and certification.

The evidence package provides immutable artifact envelopes, append-only
persistence, lineage emission, and certification of the canonical
Experiment → Run → Result → Validation → Finding chain. It is a trust layer
only and computes no trading decisions.
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
from researchos.evidence.finding_emission import (
    FINDING_ARTIFACT_TYPE,
    FINDING_EVIDENCE_VERSION,
    VALIDATION_TO_FINDING_RELATION,
    build_finding_envelope,
    certify_finding,
    emit_finding,
    finding_hash,
    finding_payload,
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
from researchos.evidence.runtime_certification import RuntimeCertification, certify_runtime
from researchos.evidence.validation_certification import (
    ValidationCertification,
    certify_validation,
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
    "DATASET_ARTIFACT_TYPE",
    "DATASET_EVIDENCE_VERSION",
    "build_dataset_envelope",
    "emit_dataset",
    "make_dataset_envelope_from_payload",
    "research_dataset_payload",
    "EXPERIMENT_ARTIFACT_TYPE",
    "EXPERIMENT_EVIDENCE_VERSION",
    "attach_dataset_parent",
    "build_experiment_envelope",
    "emit_experiment",
    "emit_experiment_with_dataset",
    "experiment_payload",
    "EXPERIMENT_TO_RUN_RELATION",
    "RUN_ARTIFACT_TYPE",
    "RUN_EVIDENCE_VERSION",
    "attach_experiment_parent",
    "build_run_envelope",
    "emit_run",
    "emit_run_for_experiment",
    "run_payload",
    "RESULT_ARTIFACT_TYPE",
    "RESULT_EVIDENCE_VERSION",
    "RUN_TO_RESULT_RELATION",
    "attach_run_parent",
    "build_result_envelope",
    "emit_result",
    "emit_result_for_run",
    "result_payload",
    "RuntimeCertification",
    "certify_runtime",
    "RESULT_TO_VALIDATION_RELATION",
    "VALIDATION_ARTIFACT_TYPE",
    "VALIDATION_EVIDENCE_VERSION",
    "attach_result_parent",
    "build_validation_envelope",
    "emit_validation",
    "emit_validation_for_result",
    "validation_hash",
    "validation_payload",
    "ValidationCertification",
    "certify_validation",
    "FINDING_ARTIFACT_TYPE",
    "FINDING_EVIDENCE_VERSION",
    "VALIDATION_TO_FINDING_RELATION",
    "build_finding_envelope",
    "certify_finding",
    "emit_finding",
    "finding_hash",
    "finding_payload",
]
