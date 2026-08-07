"""
Tests for Process Layer objects.

Based on Article XVII: Object Model â€” Process Layer.
Covers: ResearchCycle, ReasoningChain, AuditEntry
"""


from researchos.objects.process import ResearchCycle, ReasoningChain, AuditEntry


class TestResearchCycle:
    """Tests for the ResearchCycle object."""

    def test_create_research_cycle(self):
        rc = ResearchCycle(research_id="res_001")
        assert rc.research_id == "res_001"
        assert rc.start_time is not None
        assert rc.duration == 0.0
        assert rc.cycle_hash == ""
        assert rc.lifecycle.current_stage.name == "STARTED"

    def test_research_cycle_deterministic_id(self):
        rc1 = ResearchCycle("res_001")
        rc2 = ResearchCycle("res_001")
        assert rc1.id == rc2.id

    def test_add_stage(self):
        rc = ResearchCycle("res_001")
        rc.add_stage("Data Collection", 120.5, status="Complete")
        rc.add_stage("Analysis", 300.0, status="Complete")
        assert len(rc.stages) == 2
        assert rc.duration == 420.5

    def test_add_quality_metric(self):
        rc = ResearchCycle("res_001")
        rc.add_quality_metric("accuracy", 0.85, weight=1.0)
        assert len(rc.quality_metrics) == 1
        assert rc.quality_metrics[0]["name"] == "accuracy"

    def test_complete_research_cycle(self):
        rc = ResearchCycle("res_001")
        rc.add_stage("Collection", 100.0)
        rc.complete()
        assert rc.end_time is not None
        assert rc.cycle_hash != ""
        assert rc.lifecycle.current_stage.name == "COMPLETE"

    def test_research_cycle_serialization(self):
        rc = ResearchCycle("res_001")
        rc.add_stage("Stage 1", 50.0)
        rc.complete()
        d = rc.to_dict()
        assert d["research_id"] == "res_001"
        assert len(d["stages"]) == 1
        assert d["cycle_hash"] != ""
        assert d["object_type"] == "ResearchCycle"

    def test_cycle_with_inputs_outputs(self):
        rc = ResearchCycle("res_001", inputs=["obs_001"], outputs=["hyp_001"])
        assert "obs_001" in rc.inputs
        assert "hyp_001" in rc.outputs


class TestReasoningChain:
    """Tests for the ReasoningChain object."""

    def test_create_reasoning_chain(self):
        rc = ReasoningChain(research_id="res_001")
        assert rc.research_id == "res_001"
        assert len(rc.steps) == 0
        assert rc.confidence == 0.0
        assert rc.lifecycle.current_stage.name == "CREATED"

    def test_reasoning_chain_deterministic_id(self):
        rc1 = ReasoningChain("res_001")
        rc2 = ReasoningChain("res_001")
        assert rc1.id == rc2.id

    def test_add_step(self):
        rc = ReasoningChain("res_001")
        rc.add_step(
            rule="Rule_001",
            inputs=["ev_001", "ev_002"],
            outputs=["obs_001"],
            description="Combined evidence",
        )
        assert len(rc.steps) == 1
        assert "Rule_001" in rc.rules_applied
        assert "ev_001" in rc.evidence_used

    def test_add_multiple_steps(self):
        rc = ReasoningChain("res_001")
        rc.add_step("R1", ["ev_001"], ["obs_001"])
        rc.add_step("R2", ["obs_001"], ["hyp_001"])
        assert len(rc.steps) == 2
        assert rc.steps[1]["order"] == 2

    def test_verify_valid_chain(self):
        rc = ReasoningChain("res_001")
        rc.add_step("R1", ["ev_001"], ["obs_001"])
        rc.add_step("R2", ["obs_001"], ["hyp_001"])
        assert rc.verify() is True
        assert rc.lifecycle.current_stage.name == "VERIFIED"
        assert rc.chain_hash != ""

    def test_verify_empty_chain(self):
        rc = ReasoningChain("res_001")
        assert rc.verify() is False

    def test_verify_disconnected_chain(self):
        rc = ReasoningChain("res_001")
        rc.add_step("R1", ["ev_001"], ["obs_001"])
        rc.add_step("R2", ["ev_002"], ["hyp_001"])  # ev_002 not in previous outputs
        assert rc.verify() is False

    def test_reasoning_chain_serialization(self):
        rc = ReasoningChain("res_001")
        rc.add_step("R1", ["ev_001"], ["obs_001"])
        rc.verify()
        d = rc.to_dict()
        assert d["research_id"] == "res_001"
        assert len(d["steps"]) == 1
        assert d["chain_hash"] != ""
        assert d["object_type"] == "ReasoningChain"

    def test_confidence_propagation(self):
        rc = ReasoningChain("res_001", confidence=0.85)
        assert rc.confidence == 0.85


class TestAuditEntry:
    """Tests for the AuditEntry object."""

    def test_create_audit_entry(self):
        ae = AuditEntry(
            actor="system",
            action="CREATE",
            object_id="obs_001",
            object_type="Observation",
        )
        assert ae.actor == "system"
        assert ae.action == "CREATE"
        assert ae.object_id == "obs_001"
        assert ae.object_type == "Observation"
        assert ae.entry_hash == ""  # hash computed at save time by save_audit_entry()
        assert ae.lifecycle.current_stage.name == "CREATED"

    def test_audit_entry_deterministic_id(self):
        ae1 = AuditEntry("system", "CREATE", "obs_001", "Observation")
        ae2 = AuditEntry("system", "CREATE", "obs_001", "Observation")
        assert ae1.id == ae2.id

    def test_audit_entry_with_state(self):
        ae = AuditEntry(
            "trader", "UPDATE",
            "hyp_001", "Hypothesis",
            before_state="confidence=0.5",
            after_state="confidence=0.7",
        )
        assert ae.before_state == "confidence=0.5"
        assert ae.after_state == "confidence=0.7"

    def test_audit_entry_with_reasoning_chain(self):
        ae = AuditEntry(
            "system", "VERIFY",
            "rc_001", "ReasoningChain",
            reasoning_chain_id="chain_001",
        )
        assert ae.reasoning_chain_id == "chain_001"

    def test_audit_entry_chain_link(self):
        ae1 = AuditEntry("system", "CREATE", "obs_001", "Observation")
        ae2 = AuditEntry(
            "system", "UPDATE", "obs_001", "Observation",
            previous_entry=ae1.entry_hash,  # both empty until save
        )
        assert ae2.previous_entry == ae1.entry_hash  # both ""

    def test_chain_integrity_first_entry(self):
        ae = AuditEntry("system", "CREATE", "obs_001", "Observation")
        assert ae.is_chain_intact("") is True

    def test_chain_integrity_valid(self):
        AuditEntry("system", "CREATE", "obs_001", "Observation")
        ae2 = AuditEntry(
            "system", "UPDATE", "obs_001", "Observation",
            previous_entry="valid_hash_placeholder",
        )
        assert ae2.is_chain_intact("valid_hash_placeholder") is True

    def test_chain_integrity_invalid(self):
        AuditEntry("system", "CREATE", "obs_001", "Observation")
        ae2 = AuditEntry(
            "system", "UPDATE", "obs_001", "Observation",
            previous_entry="expected_hash",
        )
        assert ae2.is_chain_intact("wrong_hash") is False

    def test_audit_entry_serialization(self):
        ae = AuditEntry("system", "CREATE", "obs_001", "Observation")
        d = ae.to_dict()
        assert d["actor"] == "system"
        assert d["action"] == "CREATE"
        assert d["object_id"] == "obs_001"
        assert d["entry_hash"] == ""  # hash computed at save time
        assert d["object_type"] == "AuditEntry"

    def test_immutable_entry_hash(self):
        ae = AuditEntry("system", "CREATE", "obs_001", "Observation")
        original_hash = ae.entry_hash
        d = ae.to_dict()
        assert d["entry_hash"] == original_hash  # both empty until save

