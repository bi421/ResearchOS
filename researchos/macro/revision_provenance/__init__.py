"""
ResearchOS Macro Intelligence Layer - Revision & Provenance Package
"""

from __future__ import annotations

import importlib

from researchos.macro.provenance.chain import (
    EvidenceReference,
    ProcessingRecord,
    ProvenanceChain,
    SourceRecord,
)
from researchos.macro.revision.enums import (
    AuditAction,
    IntegrityLevel,
    ProvenanceSource,
    RevisionState,
    RevisionType,
)
from researchos.macro.revision.record import (
    RevisionChain,
    RevisionRecord,
)

# NOTE: `audit` (tier 12) is intentionally NOT imported eagerly here.
# `revision_provenance` (tier 5) is a lower-tier facade and must not import
# the higher-tier `audit` package at module load. The audit symbols are made
# available lazily via module-level ``__getattr__`` so callers that do live
# at/above the audit tier can still import them from this facade without
# creating a reverse-dependency import edge.

__all__ = [
    # Enums
    "RevisionState",
    "RevisionType",
    "ProvenanceSource",
    "AuditAction",
    "IntegrityLevel",
    # Revision
    "RevisionRecord",
    "RevisionChain",
    # Provenance
    "ProvenanceChain",
    "SourceRecord",
    "ProcessingRecord",
    "EvidenceReference",
    # Audit (lazy)
    "AuditLog",
    "AuditEntry",
    "IntegrityCheck",
    "AuditEngine",
    "AuditResult",
]

_LAZY_AUDIT_MODULES = {
    "AuditLog": "macro_intelligence.audit.log",
    "AuditEntry": "macro_intelligence.audit.log",
    "IntegrityCheck": "macro_intelligence.audit.log",
    "AuditEngine": "macro_intelligence.audit.engine",
    "AuditResult": "macro_intelligence.audit.engine",
}


def __getattr__(name: str):
    """Lazily resolve audit symbols to avoid a lower-tier -> higher-tier import."""
    module = _LAZY_AUDIT_MODULES.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = importlib.import_module(module)
    value = getattr(mod, name)
    # Cache the resolved attribute on the module for subsequent access.
    globals()[name] = value
    return value
