"""
ResearchOS Macro Intelligence Layer - Revision Object
Version: rev/obj/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from macro_intelligence.revision.enums import (
    RevisionState,
    RevisionType,
)
# NOTE: `ProvenanceChain` is intentionally NOT imported eagerly here.
# `revision` (tier 3) must not import `provenance` (tier 4) at module load;
# the reverse-dependency invariant is preserved by lazy importlib inside
# `from_dict`. The annotation below remains a string thanks to
# `from __future__ import annotations`.


@dataclass(frozen=True)
class RevisionRecord:
    """
    Immutable revision record for any macro object.
    
    MIL-REV-001: Objects are immutable. Revisions create new objects only.
    MIL-REV-002: Revision history is append-only.
    
    Each revision:
    - Preserves the original object data
    - Creates a new immutable revision record
    - Maintains a complete revision chain
    - Supports deterministic serialization
    """
    
    # Identity
    revision_id: str
    object_id: str
    object_type: str
    
    # Revision metadata
    revision_number: int
    state: RevisionState
    revision_type: RevisionType
    
    # Timestamps
    created_at: datetime
    effective_from: datetime
    effective_to: Optional[datetime] = None
    
    # Data changes
    previous_value: Any = None
    new_value: Any = None
    change_description: str = ""
    
    # Lineage
    parent_revision_id: Optional[str] = None
    child_revision_ids: list[str] = field(default_factory=list)
    
    # Provenance
    provenance: Optional[ProvenanceChain] = None
    
    # Metadata
    metadata: dict = field(default_factory=dict)
    
    # Generated
    version: str = "rev/obj/v1"
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary with deterministic ordering."""
        return {
            "revision_id": self.revision_id,
            "object_id": self.object_id,
            "object_type": self.object_type,
            "revision_number": self.revision_number,
            "state": self.state.value,
            "revision_type": self.revision_type.value,
            "created_at": self.created_at.isoformat(),
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "change_description": self.change_description,
            "parent_revision_id": self.parent_revision_id,
            "child_revision_ids": sorted(self.child_revision_ids),
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "metadata": self.metadata,
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RevisionRecord:
        """Deserialize from dictionary."""
        provenance = None
        if data.get("provenance"):
            import importlib
            prov_mod = importlib.import_module("macro_intelligence.provenance.chain")
            provenance = prov_mod.ProvenanceChain.from_dict(data["provenance"])
        
        return cls(
            revision_id=data["revision_id"],
            object_id=data["object_id"],
            object_type=data["object_type"],
            revision_number=data["revision_number"],
            state=RevisionState(data["state"]),
            revision_type=RevisionType(data["revision_type"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            effective_from=datetime.fromisoformat(data["effective_from"]),
            effective_to=datetime.fromisoformat(data["effective_to"]) if data.get("effective_to") else None,
            previous_value=data.get("previous_value"),
            new_value=data.get("new_value"),
            change_description=data.get("change_description", ""),
            parent_revision_id=data.get("parent_revision_id"),
            child_revision_ids=data.get("child_revision_ids", []),
            provenance=provenance,
            metadata=data.get("metadata", {}),
            version=data.get("version", "rev/obj/v1"),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
    
    @classmethod
    def from_json(cls, json_str: str) -> RevisionRecord:
        """Deserialize from JSON."""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def compute_hash(self) -> str:
        """
        Compute deterministic hash for the revision record.
        
        MIL-DET-001: Hash depends only on semantic content.
        
        Returns:
            SHA-256 hex digest
        """
        import hashlib
        # Exclude runtime metadata from hash
        hash_data = {
            "revision_id": self.revision_id,
            "object_id": self.object_id,
            "object_type": self.object_type,
            "revision_number": self.revision_number,
            "state": self.state.value,
            "revision_type": self.revision_type.value,
            "effective_from": self.effective_from.isoformat(),
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "change_description": self.change_description,
            "parent_revision_id": self.parent_revision_id,
        }
        canonical = __import__('json').dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the revision record.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate revision_id format
        if not self.revision_id.startswith("REV_"):
            errors.append("revision_id must start with 'REV_'")
        
        # Validate object_id format
        if not self.object_id.startswith(("SER_", "EV_", "EVNT_", "KN_")):
            errors.append("object_id must start with valid prefix")
        
        # Validate revision number
        if self.revision_number < 1:
            errors.append("revision_number must be >= 1")
        
        # Validate timestamps
        if self.effective_from > self.created_at:
            errors.append("effective_from cannot be after created_at")
        
        if self.effective_to and self.effective_to < self.effective_from:
            errors.append("effective_to cannot be before effective_from")
        
        # Validate lineage
        if self.parent_revision_id and self.parent_revision_id == self.revision_id:
            errors.append("parent_revision_id cannot be same as revision_id (circular)")
        
        # Validate provenance
        if self.provenance:
            is_valid, prov_errors = self.provenance.validate()
            if not is_valid:
                errors.extend(prov_errors)
        
        return (len(errors) == 0, errors)
    
    def get_lineage(self) -> dict[str, Any]:
        """
        Get complete lineage information.
        
        Returns:
            Dict with lineage details
        """
        return {
            "revision_id": self.revision_id,
            "object_id": self.object_id,
            "revision_number": self.revision_number,
            "state": self.state.value,
            "parent_revision_id": self.parent_revision_id,
            "child_revision_ids": sorted(self.child_revision_ids),
            "created_at": self.created_at.isoformat(),
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
        }


@dataclass(frozen=True)
class RevisionChain:
    """
    Immutable revision chain for an object.
    
    Provides navigation methods for traversing the revision history.
    """
    
    object_id: str
    object_type: str
    root_revision_id: str
    latest_revision_id: str
    revisions: list[RevisionRecord] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the revision chain."""
        if not self.revisions:
            raise ValueError("RevisionChain must have at least one revision")
        
        # Sort by revision number
        sorted_revisions = sorted(self.revisions, key=lambda r: r.revision_number)
        object.__setattr__(self, 'revisions', sorted_revisions)
        
        # Verify no circular references
        self._verify_no_cycles()
    
    def _verify_no_cycles(self) -> None:
        """Verify no circular references in revision chain."""
        visited = set()
        current_id = self.latest_revision_id
        
        while current_id:
            if current_id in visited:
                raise ValueError(f"Circular reference detected at revision {current_id}")
            visited.add(current_id)
            
            # Find parent
            current_rev = next((r for r in self.revisions if r.revision_id == current_id), None)
            if current_rev:
                current_id = current_rev.parent_revision_id
            else:
                break
    
    def get_revision(self, revision_number: int) -> Optional[RevisionRecord]:
        """Get revision by number."""
        for rev in self.revisions:
            if rev.revision_number == revision_number:
                return rev
        return None
    
    def get_latest(self) -> RevisionRecord:
        """Get latest revision."""
        return self.revisions[-1]
    
    def get_root(self) -> RevisionRecord:
        """Get root revision."""
        return self.revisions[0]
    
    def get_revision_count(self) -> int:
        """Get total number of revisions."""
        return len(self.revisions)
    
    def get_revisions_in_range(
        self,
        start_number: int,
        end_number: int,
    ) -> list[RevisionRecord]:
        """Get revisions in a number range."""
        return [
            rev for rev in self.revisions
            if start_number <= rev.revision_number <= end_number
        ]
