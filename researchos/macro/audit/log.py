"""
ResearchOS Macro Intelligence Layer - Audit Log
Version: audit/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from researchos.macro.revision.enums import AuditAction, IntegrityLevel


@dataclass(frozen=True)
class AuditEntry:
    """
    Immutable audit log entry.

    Records every significant operation on macro objects:
    - Object creation
    - Revision creation
    - Validation events
    - Integrity checks
    - Reconstruct operations
    """

    # Identity
    audit_id: str
    timestamp: datetime

    # Action
    action: AuditAction
    object_type: str
    object_id: str
    revision_id: str | None

    # Details
    actor: str
    success: bool
    details: dict = field(default_factory=dict)

    # Optional fields
    error_message: str | None = None
    session_id: str | None = None
    batch_id: str | None = None

    # Generated
    version: str = "audit/v1"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "revision_id": self.revision_id,
            "actor": self.actor,
            "details": self.details,
            "success": self.success,
            "error_message": self.error_message,
            "session_id": self.session_id,
            "batch_id": self.batch_id,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEntry:
        """Deserialize from dictionary."""
        return cls(
            audit_id=data["audit_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            action=AuditAction(data["action"]),
            object_type=data["object_type"],
            object_id=data["object_id"],
            revision_id=data.get("revision_id"),
            actor=data["actor"],
            details=data.get("details", {}),
            success=data["success"],
            error_message=data.get("error_message"),
            session_id=data.get("session_id"),
            batch_id=data.get("batch_id"),
            version=data.get("version", "audit/v1"),
        )

    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> AuditEntry:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """Compute deterministic hash."""
        import hashlib

        hash_data = {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "revision_id": self.revision_id,
            "actor": self.actor,
        }
        canonical = __import__("json").dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IntegrityCheck:
    """
    Result of an integrity verification check.
    """

    check_id: str
    timestamp: datetime
    object_type: str
    object_id: str
    revision_id: str | None
    level: IntegrityLevel
    passed: bool
    checks_performed: list[str]
    checks_passed: list[str]
    checks_failed: list[str]
    error_details: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    version: str = "audit/v1"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "check_id": self.check_id,
            "timestamp": self.timestamp.isoformat(),
            "object_type": self.object_type,
            "object_id": self.object_id,
            "revision_id": self.revision_id,
            "level": self.level.value,
            "passed": self.passed,
            "checks_performed": sorted(self.checks_performed),
            "checks_passed": sorted(self.checks_passed),
            "checks_failed": sorted(self.checks_failed),
            "error_details": self.error_details,
            "warnings": self.warnings,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IntegrityCheck:
        """Deserialize from dictionary."""
        return cls(
            check_id=data["check_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            object_type=data["object_type"],
            object_id=data["object_id"],
            revision_id=data.get("revision_id"),
            level=IntegrityLevel(data["level"]),
            passed=data["passed"],
            checks_performed=data.get("checks_performed", []),
            checks_passed=data.get("checks_passed", []),
            checks_failed=data.get("checks_failed", []),
            error_details=data.get("error_details", []),
            warnings=data.get("warnings", []),
            version=data.get("version", "audit/v1"),
        )

    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class AuditLog:
    """
    Immutable audit log for tracking all operations.

    MIL-AUDIT-001: Historical reconstruction must be deterministic.
    """

    log_id: str
    created_at: datetime = field(default_factory=lambda: datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc))
    entries: list[AuditEntry] = field(default_factory=list)
    integrity_checks: list[IntegrityCheck] = field(default_factory=list)

    # Metadata
    version: str = "audit/v1"

    def add_entry(self, entry: AuditEntry) -> AuditLog:
        """Add an audit entry (returns new immutable log)."""
        return AuditLog(
            log_id=self.log_id,
            created_at=self.created_at,
            entries=sorted(self.entries + [entry], key=lambda e: e.timestamp),
            integrity_checks=self.integrity_checks,
            version=self.version,
        )

    def add_check(self, check: IntegrityCheck) -> AuditLog:
        """Add an integrity check (returns new immutable log)."""
        return AuditLog(
            log_id=self.log_id,
            created_at=self.created_at,
            entries=self.entries,
            integrity_checks=sorted(self.integrity_checks + [check], key=lambda c: c.timestamp),
            version=self.version,
        )

    def get_entries_for_object(
        self,
        object_type: str,
        object_id: str,
    ) -> list[AuditEntry]:
        """Get all audit entries for a specific object."""
        return [entry for entry in self.entries if entry.object_type == object_type and entry.object_id == object_id]

    def get_latest_entry(
        self,
        object_type: str,
        object_id: str,
    ) -> AuditEntry | None:
        """Get the latest audit entry for an object."""
        entries = self.get_entries_for_object(object_type, object_id)
        return entries[-1] if entries else None

    def get_integrity_checks_for_object(
        self,
        object_type: str,
        object_id: str,
    ) -> list[IntegrityCheck]:
        """Get all integrity checks for a specific object."""
        return [check for check in self.integrity_checks if check.object_type == object_type and check.object_id == object_id]

    def get_latest_integrity_check(
        self,
        object_type: str,
        object_id: str,
    ) -> IntegrityCheck | None:
        """Get the latest integrity check for an object."""
        checks = self.get_integrity_checks_for_object(object_type, object_id)
        return checks[-1] if checks else None

    def to_json(self) -> str:
        """Serialize to JSON."""
        import json

        return json.dumps(
            {
                "log_id": self.log_id,
                "created_at": self.created_at.isoformat(),
                "entries": [e.to_dict() for e in self.entries],
                "integrity_checks": [c.to_dict() for c in self.integrity_checks],
                "version": self.version,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> AuditLog:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        entries = [AuditEntry.from_dict(e) for e in data.get("entries", [])]
        checks = [IntegrityCheck.from_dict(c) for c in data.get("integrity_checks", [])]
        return cls(
            log_id=data["log_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            entries=entries,
            integrity_checks=checks,
            version=data.get("version", "audit/v1"),
        )
