"""
Tests for Cognitive Layer objects.

Based on Article XVII: Object Model â€” Cognitive Layer.
Covers: Bias, LearningRecord, CognitiveAssessment
"""

import pytest

from researchos.objects.cognitive import Bias, LearningRecord, CognitiveAssessment


class TestBias:
    """Tests for the Bias object."""

    def test_create_bias(self):
        b = Bias(
            type="Confirmation",
            trader_id="trader_001",
            description="Seeks confirming evidence",
        )
        assert b.type == "Confirmation"
        assert b.trader_id == "trader_001"
        assert b.lifecycle.current_stage.name == "DETECTED"

    def test_bias_deterministic_id(self):
        b1 = Bias("Confirmation", "trader_001", "dec_001")
        b2 = Bias("Confirmation", "trader_001", "dec_001")
        assert b1.id == b2.id

    def test_bias_update_occurrence(self):
        b = Bias("Overconfidence", "trader_001")
        b.update_occurrence(frequency=0.8, trend=-0.1, severity=0.6)
        assert b.frequency == 0.8
        assert b.trend == -0.1
        assert b.severity == 0.6
        assert b.lifecycle.current_stage.name == "UPDATED"

    def test_bias_with_evidence(self):
        b = Bias(
            "Recency", "trader_001",
            evidence=["Recent trade log shows overweighting of last 3 trades"],
        )
        assert len(b.evidence) == 1

    def test_bias_timestamps(self):
        b = Bias("Anchoring", "trader_001")
        assert b.first_detected is not None
        assert b.last_detected is not None

    def test_bias_serialization(self):
        b = Bias(
            "Loss_Aversion", "trader_001", decision_id="dec_001",
            severity=0.4, frequency=0.6,
        )
        d = b.to_dict()
        assert d["type"] == "Loss_Aversion"
        assert d["severity"] == 0.4
        assert d["frequency"] == 0.6
        assert d["object_type"] == "Bias"

    def test_bias_trend_not_updated_at_creation(self):
        b = Bias("Hindsight", "trader_001", trend=0.0)
        assert b.trend == 0.0


class TestLearningRecord:
    """Tests for the LearningRecord object."""

    def test_create_learning_record(self):
        lr = LearningRecord(
            trader_id="trader_001",
            dimension="Knowledge",
            score=0.75,
        )
        assert lr.trader_id == "trader_001"
        assert lr.dimension == "Knowledge"
        assert lr.score == 0.75

    def test_learning_record_deterministic_id(self):
        lr1 = LearningRecord("trader_001", "Reasoning", 0.8)
        lr2 = LearningRecord("trader_001", "Reasoning", 0.8)
        assert lr1.id == lr2.id

    def test_update_learning_record(self):
        lr = LearningRecord("trader_001", "Bias", score=0.3)
        lr.update(score=0.6, trend=0.2, trajectory="Accelerating")
        assert lr.score == 0.6
        assert lr.trend == 0.2
        assert lr.trajectory == "Accelerating"
        assert lr.lifecycle.current_stage.name == "UPDATED"

    def test_update_with_recommendations(self):
        lr = LearningRecord("trader_001", "Discipline", score=0.4)
        lr.update(0.5, 0.1, "Steady", ["Practice risk management"])
        assert "Practice risk management" in lr.recommendations

    def test_progress_computation(self):
        lr = LearningRecord("trader_001", "Knowledge", score=0.5, baseline_score=0.3)
        lr.update(score=0.7, trend=0.2, trajectory="Accelerating")
        assert lr.progress == 0.4  # 0.7 - 0.3

    def test_learning_record_serialization(self):
        lr = LearningRecord(
            "trader_001", "Reflection", score=0.6,
            recommendations=["Journal daily"],
        )
        d = lr.to_dict()
        assert d["dimension"] == "Reflection"
        assert d["score"] == 0.6
        assert d["object_type"] == "LearningRecord"

    def test_default_trajectory(self):
        lr = LearningRecord("trader_001", "Knowledge")
        assert lr.trajectory == "Steady"


class TestCognitiveAssessment:
    """Tests for the CognitiveAssessment object."""

    def test_create_assessment(self):
        ca = CognitiveAssessment(
            trader_id="trader_001",
            knowledge_score=0.7,
            reasoning_score=0.6,
            discipline_score=0.5,
            reflection_score=0.4,
            learning_progress=0.3,
        )
        assert ca.trader_id == "trader_001"
        assert ca.knowledge_score == 0.7

    def test_cognitive_assessment_deterministic_id(self):
        ca1 = CognitiveAssessment("trader_001", "res_001")
        ca2 = CognitiveAssessment("trader_001", "res_001")
        assert ca1.id == ca2.id

    def test_compute_overall_score(self):
        ca = CognitiveAssessment(
            "trader_001",
            knowledge_score=1.0,
            reasoning_score=1.0,
            discipline_score=1.0,
            reflection_score=1.0,
            learning_progress=1.0,
        )
        score = ca.compute_overall_score()
        assert score == pytest.approx(1.0, rel=0.01)

    def test_overall_score_with_bias_penalty(self):
        ca = CognitiveAssessment(
            "trader_001",
            knowledge_score=1.0,
            reasoning_score=1.0,
            discipline_score=1.0,
            reflection_score=1.0,
            learning_progress=1.0,
            bias_profile=["bias_001", "bias_002", "bias_003"],
        )
        score = ca.compute_overall_score()
        # 1.0 * 0.25 + 1.0 * 0.25 + (1.0 - 3*0.05) * 0.10 + 1.0*0.15 + 1.0*0.15 + 1.0*0.10
        # = 0.25 + 0.25 + 0.085 + 0.15 + 0.15 + 0.10 = 0.985
        assert score == pytest.approx(0.985, rel=0.01)

    def test_complete_assessment(self):
        ca = CognitiveAssessment(
            "trader_001",
            knowledge_score=0.8,
            reasoning_score=0.7,
            discipline_score=0.6,
            reflection_score=0.5,
            learning_progress=0.4,
        )
        ca.complete()
        assert ca.overall_score > 0.0
        assert ca.lifecycle.current_stage.name == "COMPLETE"

    def test_assessment_with_bias_profile(self):
        ca = CognitiveAssessment(
            "trader_001",
            bias_profile=["bias_confirmation", "bias_recency"],
        )
        assert len(ca.bias_profile) == 2

    def test_assessment_with_feedback(self):
        ca = CognitiveAssessment(
            "trader_001",
            feedback=["Good reasoning quality", "Reduce overconfidence"],
        )
        assert len(ca.feedback) == 2

    def test_assessment_serialization(self):
        ca = CognitiveAssessment(
            "trader_001", "res_001",
            knowledge_score=0.9,
            reasoning_score=0.8,
        )
        ca.complete()
        d = ca.to_dict()
        assert d["trader_id"] == "trader_001"
        assert d["knowledge_score"] == 0.9
        assert d["object_type"] == "CognitiveAssessment"

    def test_overall_score_bounds(self):
        ca = CognitiveAssessment("trader_001")
        ca.knowledge_score = 2.0  # Unreasonable, but shouldn't break
        ca.reasoning_score = 2.0
        ca.discipline_score = 2.0
        ca.reflection_score = 2.0
        ca.learning_progress = 2.0
        score = ca.compute_overall_score()
        assert score <= 1.0  # Clamped

