from researchos.experiments.phase52 import FEATURE_SET_NAMES


def test_feature_set_count_guardrail():
    assert len(FEATURE_SET_NAMES) == 5
