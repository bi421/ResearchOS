"""Tests for the explicit experiment-learning boundary."""

from researchos.experiments.learning import ExperimentLearningRecord, LearningRecord
from researchos.objects.cognitive import LearningRecord as CognitiveLearningRecord


def test_experiment_learning_has_explicit_type_name() -> None:
    record = ExperimentLearningRecord(
        experiment_id="exp-1",
        validation_id="val-1",
        hypothesis_id="hyp-1",
    )

    assert isinstance(record, ExperimentLearningRecord)
    assert record.__class__.__name__ == "ExperimentLearningRecord"
    assert LearningRecord is ExperimentLearningRecord


def test_experiment_and_cognitive_learning_are_distinct_domains() -> None:
    experiment_learning = ExperimentLearningRecord(
        experiment_id="exp-1",
        validation_id="val-1",
        hypothesis_id="hyp-1",
    )
    cognitive_learning = CognitiveLearningRecord(
        trader_id="trader-1",
        dimension="Knowledge",
    )

    assert type(experiment_learning) is not type(cognitive_learning)
    assert experiment_learning.id != cognitive_learning.id
