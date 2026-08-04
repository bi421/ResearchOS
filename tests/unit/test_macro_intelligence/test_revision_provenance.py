"""
ResearchOS Macro Intelligence Layer - Revision & Provenance Tests
"""

import pytest
from datetime import datetime, timezone

UTC = timezone.utc


class TestRevisionState:
    """Tests for RevisionState enum."""
    
    def test_states_exist(self):
        """Test all revision states exist."""
        from macro_intelligence.revision.enums import RevisionState
        
        assert hasattr(RevisionState, 'ORIGINAL')
        assert hasattr(RevisionState, 'REVISED')
        assert hasattr(RevisionState, 'CORRECTED')
        assert hasattr(RevisionState, 'SUPERSEDED')
        assert hasattr(RevisionState, 'DEPRECATED')
    
    def test_is_terminal(self):
        """Test terminal state detection."""
        from macro_intelligence.revision.enums import RevisionState
        
        assert RevisionState.SUPERSEDED.is_terminal()
        assert RevisionState.DEPRECATED.is_terminal()
        assert not RevisionState.ORIGINAL.is_terminal()
    
    def test_is_intermediate(self):
        """Test intermediate state detection."""
        from macro_intelligence.revision.enums import RevisionState
        
        assert RevisionState.ORIGINAL.is_intermediate()
        assert RevisionState.REVISED.is_intermediate()
        assert RevisionState.CORRECTED.is_intermediate()
        assert not RevisionState.SUPERSEDED.is_intermediate()
    
    def test_can_transition_to(self):
        """Test state transition rules."""
        from macro_intelligence.revision.enums import RevisionState
        
        # ORIGINAL can transition to REVISED
        assert RevisionState.ORIGINAL.can_transition_to(RevisionState.REVISED)
        
        # SUPERSEDED cannot transition anywhere
        assert not RevisionState.SUPERSEDED.can_transition_to(RevisionState.REVISED)
        assert not RevisionState.DEPRECATED.can_transition_to(RevisionState.REVISED)


class TestRevisionRecord:
    """Tests for RevisionRecord."""
    
    def _create_base_record(self) -> dict:
        """Create base revision record data."""
        from macro_intelligence.revision.enums import RevisionState, RevisionType
        return {
            "revision_id": "REV_20260803_001",
            "object_id": "SER_20260803_001",
            "object_type": "NormalizedSeries",
            "revision_number": 1,
            "state": RevisionState.REVISED,
            "revision_type": RevisionType.DATA_UPDATE,
            "created_at": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            "effective_from": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            "previous_value": 4.25,
            "new_value": 4.30,
            "change_description": "Updated yield value",
            "parent_revision_id": None,
            "child_revision_ids": [],
        }
    
    def test_create_revision(self):
        """Test creating a revision record."""
        from macro_intelligence.revision.record import RevisionRecord
        
        data = self._create_base_record()
        record = RevisionRecord(**data)
        
        assert record.revision_id == "REV_20260803_001"
        assert record.revision_number == 1
        assert record.new_value == 4.30
    
    def test_revision_immutability(self):
        """Test that revision is immutable."""
        from macro_intelligence.revision.record import RevisionRecord
        
        data = self._create_base_record()
        record = RevisionRecord(**data)
        
        with pytest.raises(AttributeError):
            record.new_value = 5.0
    
    def test_revision_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        from macro_intelligence.revision.record import RevisionRecord
        
        original = RevisionRecord(**self._create_base_record())
        json_str = original.to_json()
        restored = RevisionRecord.from_json(json_str)
        
        assert restored.revision_id == original.revision_id
        assert restored.new_value == original.new_value
        assert restored.to_json() == json_str
    
    def test_revision_hash_deterministic(self):
        """Test that hash is deterministic."""
        from macro_intelligence.revision.record import RevisionRecord
        
        record1 = RevisionRecord(**self._create_base_record())
        record2 = RevisionRecord(**self._create_base_record())
        
        assert record1.compute_hash() == record2.compute_hash()
    
    def test_revision_validate(self):
        """Test revision validation."""
        from macro_intelligence.revision.record import RevisionRecord
        
        record = RevisionRecord(**self._create_base_record())
        is_valid, errors = record.validate()
        
        assert is_valid
        assert len(errors) == 0
    
    def test_revision_validate_invalid_id(self):
        """Test revision validation with invalid ID."""
        from macro_intelligence.revision.record import RevisionRecord
        
        data = self._create_base_record()
        data["revision_id"] = "INVALID"
        
        record = RevisionRecord(**data)
        is_valid, errors = record.validate()
        
        assert not is_valid
        assert any("revision_id" in e for e in errors)


class TestProvenanceChain:
    """Tests for ProvenanceChain."""
    
    def _create_base_provenance(self) -> dict:
        """Create base provenance data."""
        from macro_intelligence.provenance.chain import SourceRecord, ProcessingRecord
        from macro_intelligence.revision.enums import ProvenanceSource
        
        return {
            "source_record": SourceRecord(
                source_id="FRED",
                source_type=ProvenanceSource.FRED,
                source_version="2026.08",
                source_quality_score=0.95,
                ingestion_timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
                batch_id="BATCH_20260803_001",
                adapter_version="v1.0.0",
            ),
            "processing_record": ProcessingRecord(
                normalization_version="v1.0.0",
                validation_version="v1.0.0",
                quality_score_before=0.90,
                quality_score_after=0.95,
                transformations_applied=["unit_conversion"],
            ),
            "schema_version": "ms/v1",
            "object_type": "NormalizedSeries",
        }
    
    def test_create_provenance(self):
        """Test creating a provenance chain."""
        from macro_intelligence.provenance.chain import ProvenanceChain
        
        data = self._create_base_provenance()
        chain = ProvenanceChain(**data)
        
        assert chain.schema_version == "ms/v1"
        assert chain.source_record.source_id == "FRED"
    
    def test_provenance_immutability(self):
        """Test that provenance is immutable."""
        from macro_intelligence.provenance.chain import ProvenanceChain
        
        data = self._create_base_provenance()
        chain = ProvenanceChain(**data)
        
        with pytest.raises(AttributeError):
            chain.schema_version = "v2"
    
    def test_provenance_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        from macro_intelligence.provenance.chain import ProvenanceChain
        
        original = ProvenanceChain(**self._create_base_provenance())
        json_str = original.to_json()
        restored = ProvenanceChain.from_json(json_str)
        
        assert restored.schema_version == original.schema_version
        assert restored.source_record.source_id == original.source_record.source_id
        assert restored.to_json() == json_str
    
    def test_provenance_hash_deterministic(self):
        """Test that hash is deterministic."""
        from macro_intelligence.provenance.chain import ProvenanceChain
        
        chain1 = ProvenanceChain(**self._create_base_provenance())
        chain2 = ProvenanceChain(**self._create_base_provenance())
        
        assert chain1.compute_hash() == chain2.compute_hash()
    
    def test_provenance_validate(self):
        """Test provenance validation."""
        from macro_intelligence.provenance.chain import ProvenanceChain
        
        chain = ProvenanceChain(**self._create_base_provenance())
        is_valid, errors = chain.validate()
        
        assert is_valid
        assert len(errors) == 0


class TestAuditLog:
    """Tests for AuditLog."""
    
    def test_create_audit_log(self):
        """Test creating an audit log."""
        from macro_intelligence.audit.log import AuditLog
        
        log = AuditLog(log_id="LOG_001")
        
        assert log.log_id == "LOG_001"
        assert len(log.entries) == 0
    
    def test_add_audit_entry(self):
        """Test adding an audit entry."""
        from macro_intelligence.audit.log import AuditLog, AuditEntry
        from macro_intelligence.revision.enums import AuditAction
        
        log = AuditLog(log_id="LOG_001")
        
        entry = AuditEntry(
            audit_id="AUDIT_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            action=AuditAction.CREATE,
            object_type="NormalizedSeries",
            object_id="SER_20260803_001",
            revision_id=None,
            actor="adapter",
            success=True,
        )
        
        new_log = log.add_entry(entry)
        
        assert len(new_log.entries) == 1
        assert new_log.entries[0].audit_id == "AUDIT_001"
    
    def test_audit_log_immutability(self):
        """Test that audit log is immutable."""
        from macro_intelligence.audit.log import AuditLog, AuditEntry
        from macro_intelligence.revision.enums import AuditAction
        
        log = AuditLog(log_id="LOG_001")
        
        entry = AuditEntry(
            audit_id="AUDIT_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            action=AuditAction.CREATE,
            object_type="NormalizedSeries",
            object_id="SER_20260803_001",
            revision_id=None,
            actor="adapter",
            success=True,
        )
        
        new_log = log.add_entry(entry)
        
        # Original log should be unchanged
        assert len(log.entries) == 0
        # New log should have the entry
        assert len(new_log.entries) == 1
    
    def test_get_entries_for_object(self):
        """Test filtering entries by object."""
        from macro_intelligence.audit.log import AuditLog, AuditEntry
        from macro_intelligence.revision.enums import AuditAction
        
        log = AuditLog(log_id="LOG_001")
        
        entry1 = AuditEntry(
            audit_id="AUDIT_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            action=AuditAction.CREATE,
            object_type="NormalizedSeries",
            object_id="SER_001",
            revision_id=None,
            actor="adapter",
            details={},
            success=True,
        )
        
        entry2 = AuditEntry(
            audit_id="AUDIT_002",
            timestamp=datetime(2026, 8, 3, 12, 1, tzinfo=UTC),
            action=AuditAction.CREATE,
            object_type="NormalizedSeries",
            object_id="SER_002",
            revision_id=None,
            actor="adapter",
            details={},
            success=True,
        )
        
        new_log = log.add_entry(entry1).add_entry(entry2)
        
        # Get entries for SER_001
        entries = new_log.get_entries_for_object("NormalizedSeries", "SER_001")
        assert len(entries) == 1
        assert entries[0].object_id == "SER_001"
        
        # Get entries for SER_002
        entries = new_log.get_entries_for_object("NormalizedSeries", "SER_002")
        assert len(entries) == 1
        assert entries[0].object_id == "SER_002"


class TestRevisionChain:
    """Tests for RevisionChain."""
    
    def test_create_revision_chain(self):
        """Test creating a revision chain."""
        from macro_intelligence.revision.record import RevisionChain, RevisionRecord
        from macro_intelligence.revision.enums import RevisionState, RevisionType
        
        revisions = [
            RevisionRecord(
                revision_id="REV_001",
                object_id="SER_001",
                object_type="NormalizedSeries",
                revision_number=1,
                state=RevisionState.ORIGINAL,
                revision_type=RevisionType.DATA_UPDATE,
                created_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
                effective_from=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
            RevisionRecord(
                revision_id="REV_002",
                object_id="SER_001",
                object_type="NormalizedSeries",
                revision_number=2,
                state=RevisionState.REVISED,
                revision_type=RevisionType.DATA_UPDATE,
                created_at=datetime(2026, 8, 3, 13, 0, tzinfo=UTC),
                effective_from=datetime(2026, 8, 3, 13, 0, tzinfo=UTC),
                parent_revision_id="REV_001",
            ),
        ]
        
        chain = RevisionChain(
            object_id="SER_001",
            object_type="NormalizedSeries",
            root_revision_id="REV_001",
            latest_revision_id="REV_002",
            revisions=revisions,
        )
        
        assert chain.get_revision_count() == 2
        assert chain.get_root().revision_number == 1
        assert chain.get_latest().revision_number == 2
    
    def test_revision_chain_sorting(self):
        """Test that revisions are sorted by number."""
        from macro_intelligence.revision.record import RevisionChain, RevisionRecord
        from macro_intelligence.revision.enums import RevisionState, RevisionType
        
        # Create revisions out of order
        revisions = [
            RevisionRecord(
                revision_id="REV_003",
                object_id="SER_001",
                object_type="NormalizedSeries",
                revision_number=3,
                state=RevisionState.REVISED,
                revision_type=RevisionType.DATA_UPDATE,
                created_at=datetime(2026, 8, 3, 14, 0, tzinfo=UTC),
                effective_from=datetime(2026, 8, 3, 14, 0, tzinfo=UTC),
            ),
            RevisionRecord(
                revision_id="REV_001",
                object_id="SER_001",
                object_type="NormalizedSeries",
                revision_number=1,
                state=RevisionState.ORIGINAL,
                revision_type=RevisionType.DATA_UPDATE,
                created_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
                effective_from=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
            RevisionRecord(
                revision_id="REV_002",
                object_id="SER_001",
                object_type="NormalizedSeries",
                revision_number=2,
                state=RevisionState.REVISED,
                revision_type=RevisionType.DATA_UPDATE,
                created_at=datetime(2026, 8, 3, 13, 0, tzinfo=UTC),
                effective_from=datetime(2026, 8, 3, 13, 0, tzinfo=UTC),
            ),
        ]
        
        chain = RevisionChain(
            object_id="SER_001",
            object_type="NormalizedSeries",
            root_revision_id="REV_001",
            latest_revision_id="REV_003",
            revisions=revisions,
        )
        
        # Should be sorted
        assert chain.revisions[0].revision_number == 1
        assert chain.revisions[1].revision_number == 2
        assert chain.revisions[2].revision_number == 3


class TestMILRevInvariants:
    """Tests for MIL-REV invariants."""
    
    def test_mil_rev_001_immutability(self):
        """MIL-REV-001: Objects are immutable. Revisions create new objects only."""
        from macro_intelligence.revision.record import RevisionRecord
        from macro_intelligence.revision.enums import RevisionState, RevisionType
        
        record = RevisionRecord(
            revision_id="REV_001",
            object_id="SER_001",
            object_type="NormalizedSeries",
            revision_number=1,
            state=RevisionState.ORIGINAL,
            revision_type=RevisionType.DATA_UPDATE,
            created_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            effective_from=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )
        
        # Should raise AttributeError on modification
        with pytest.raises(AttributeError):
            record.new_value = 5.0
    
    def test_mil_rev_002_append_only(self):
        """MIL-REV-002: Revision history is append-only."""
        from macro_intelligence.revision.record import RevisionChain, RevisionRecord
        from macro_intelligence.revision.enums import RevisionState, RevisionType
        
        revisions = [
            RevisionRecord(
                revision_id="REV_001",
                object_id="SER_001",
                object_type="NormalizedSeries",
                revision_number=1,
                state=RevisionState.ORIGINAL,
                revision_type=RevisionType.DATA_UPDATE,
                created_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
                effective_from=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        ]
        
        chain = RevisionChain(
            object_id="SER_001",
            object_type="NormalizedSeries",
            root_revision_id="REV_001",
            latest_revision_id="REV_001",
            revisions=revisions,
        )
        
        # Should not be able to modify existing revision
        with pytest.raises(AttributeError):
            chain.revisions[0].new_value = 5.0


class TestMILProvInvariant:
    """Tests for MIL-PROV-001 invariant."""
    
    def test_mil_prov_001_complete_provenance(self):
        """MIL-PROV-001: Every stored object must preserve complete provenance."""
        from macro_intelligence.provenance.chain import ProvenanceChain, SourceRecord, ProcessingRecord
        from macro_intelligence.revision.enums import ProvenanceSource
        
        provenance = ProvenanceChain(
            source_record=SourceRecord(
                source_id="FRED",
                source_type=ProvenanceSource.FRED,
                source_version="2026.08",
                source_quality_score=0.95,
                ingestion_timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
                batch_id="BATCH_001",
                adapter_version="v1.0.0",
            ),
            processing_record=ProcessingRecord(
                normalization_version="v1.0.0",
                validation_version="v1.0.0",
                quality_score_before=0.90,
                quality_score_after=0.95,
                transformations_applied=[],
            ),
            schema_version="ms/v1",
            object_type="NormalizedSeries",
        )
        
        # Verify all required fields are present
        assert provenance.source_record.source_id
        assert provenance.processing_record.normalization_version
        assert provenance.schema_version
        assert provenance.object_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
