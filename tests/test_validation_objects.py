"""
Tests for Validation Layer objects.

Based on Article XVII: Object Model — Validation Layer.
Covers: Validation, FailureAnalysis
"""

from researchos.objects.validation import FailureAnalysis, Validation


class TestValidation:
    """Tests for the Validation object."""

    def test_create_validation(self):
        v = Validation(
            research_id="res_001",
            research_report_id="rr_001",
            time_horizon="1M",
        )
        assert v.research_id == "res_001"
        assert v.research_report_id == "rr_001"
        assert v.overall_status == "In Progress"
        assert v.quality_score == 0.0
        assert v.lifecycle.current_stage.name == "IN_PROGRESS"
        assert v.id is not None and v.id != ""

    def test_validation_deterministic_id(self):
        v1 = Validation("res_001", "rr_001", "1M")
        v2 = Validation("res_001", "rr_001", "1M")
        assert v1.id == v2.id

    def test_complete_validation(self):
        v = Validation("res_001", "rr_001", "1M")
        v.complete(0.85, "Accurate")
        assert v.quality_score == 0.85
        assert v.overall_status == "Accurate"
        assert v.lifecycle.current_stage.name == "COMPLETE"

    def test_add_scenario_result(self):
        v = Validation("res_001", "rr_001", "1M")
        result = {"scenario_id": "sc_001", "accuracy": 0.9}
        v.add_scenario_result(result)
        assert len(v.scenario_results) == 1
        assert v.scenario_results[0]["scenario_id"] == "sc_001"

    def test_add_target_result(self):
        v = Validation("res_001", "rr_001", "1M")
        result = {"target": "SPX 5000", "actual": "SPX 5100", "error": 0.02}
        v.add_target_result(result)
        assert len(v.target_results) == 1
        assert v.target_results[0]["target"] == "SPX 5000"

    def test_validation_serialization(self):
        v = Validation("res_001", "rr_001", "1M")
        d = v.to_dict()
        assert d["research_id"] == "res_001"
        assert d["quality_score"] == 0.0
        assert d["object_type"] == "Validation"

    def test_validation_with_failure_analysis(self):
        v = Validation("res_001", "rr_001", "1M", failure_analysis_id="fa_001")
        assert v.failure_analysis_id == "fa_001"


class TestFailureAnalysis:
    """Tests for the FailureAnalysis object."""

    def test_create_failure_analysis(self):
        fa = FailureAnalysis(
            validation_id="val_001",
            research_id="res_001",
        )
        assert fa.validation_id == "val_001"
        assert fa.research_id == "res_001"
        assert fa.lifecycle.current_stage.name == "INITIATED"

    def test_failure_analysis_deterministic_id(self):
        fa1 = FailureAnalysis("val_001", "res_001")
        fa2 = FailureAnalysis("val_001", "res_001")
        assert fa1.id == fa2.id

    def test_add_failure(self):
        fa = FailureAnalysis("val_001", "res_001")
        fa.add_failure(
            description="Incorrect trend prediction",
            category="Directional",
            severity=0.7,
            root_cause="Misread momentum indicators",
            preventable=True,
        )
        assert len(fa.failures) == 1
        assert len(fa.root_causes) == 1
        assert fa.failures[0]["preventable"] is True

    def test_add_multiple_failures(self):
        fa = FailureAnalysis("val_001", "res_001")
        fa.add_failure("Failure A", "Category 1", 0.5, "Cause A")
        fa.add_failure("Failure B", "Category 2", 0.8, "Cause B")
        assert len(fa.failures) == 2
        assert len(fa.root_causes) == 2

    def test_duplicate_root_cause(self):
        fa = FailureAnalysis("val_001", "res_001")
        fa.add_failure("F1", "C1", 0.5, "Same Cause")
        fa.add_failure("F2", "C2", 0.6, "Same Cause")
        assert len(fa.failures) == 2
        assert len(fa.root_causes) == 1

    def test_complete_failure_analysis(self):
        fa = FailureAnalysis("val_001", "res_001")
        fa.add_failure("Test failure", "Test", 0.5, "Test cause")
        fa.complete()
        assert fa.lifecycle.current_stage.name == "COMPLETE"

    def test_failure_analysis_serialization(self):
        fa = FailureAnalysis("val_001", "res_001")
        fa.add_failure("Test", "Cat", 0.5, "Root")
        d = fa.to_dict()
        assert d["validation_id"] == "val_001"
        assert len(d["failures"]) == 1
        assert d["object_type"] == "FailureAnalysis"

    def test_severity_scores(self):
        fa = FailureAnalysis("val_001", "res_001")
        fa.add_failure("F1", "Cat", 0.7, "Cause")
        assert len(fa.severity_scores) == 1
        assert fa.severity_scores[0]["severity"] == 0.7

    def test_improvement_areas(self):
        fa = FailureAnalysis("val_001", "res_001", improvement_areas=["Signal processing", "Risk assessment"])
        assert len(fa.improvement_areas) == 2
