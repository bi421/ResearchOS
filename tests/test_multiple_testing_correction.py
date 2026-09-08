from researchos.market_memory.pipeline_v1 import _PIPELINE_ALPHA
from researchos.market_memory.statistical_evidence import bonferroni_alpha, wilson_proportion_ci


def test_bonferroni_alpha_controls_family_wise_error_rate() -> None:
    assert bonferroni_alpha(0.05, 5) == 0.01


def test_bonferroni_adjusted_confidence_is_deterministic() -> None:
    alpha = bonferroni_alpha(_PIPELINE_ALPHA, 5)
    ci_a = wilson_proportion_ci(60, 100, confidence_level=1.0 - alpha)
    ci_b = wilson_proportion_ci(60, 100, confidence_level=1.0 - alpha)
    assert ci_a == ci_b
    assert ci_a.confidence_level == 0.99


def test_bonferroni_adjusted_ci_is_wider_than_nominal_ci() -> None:
    nominal = wilson_proportion_ci(60, 100, confidence_level=0.95)
    corrected = wilson_proportion_ci(60, 100, confidence_level=0.99)
    nominal_width = nominal.confidence_interval[1] - nominal.confidence_interval[0]
    corrected_width = corrected.confidence_interval[1] - corrected.confidence_interval[0]
    assert corrected_width > nominal_width
