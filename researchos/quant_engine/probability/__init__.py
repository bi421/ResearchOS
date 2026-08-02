"""
Probability & Statistics Engine — pure statistical computation.

Research-only. No ML. All random processes are seeded and reproducible.
"""

from researchos.quant_engine.probability.contracts import (
    ConfidenceInterval,
    DistributionFit,
    DistributionType,
    HypothesisTestResult,
    MonteCarloResult,
    TestStatistic,
)
from researchos.quant_engine.probability.statistics import (
    normal_pdf,
    normal_cdf,
    student_t_pdf,
    student_t_cdf,
    log_normal_pdf,
    empirical_cdf,
    fit_normal,
    fit_log_normal,
    fit_student_t,
    kernel_density_estimate,
    confidence_interval_mean,
    one_sample_t_test,
    z_test,
    bootstrap_mean,
    monte_carlo_normal,
    monte_carlo_return_paths,
    probability_calibration,
)
from researchos.quant_engine.probability.bayesian import (
    BetaPosterior,
    MarkovChain,
    HiddenMarkovModel,
    estimate_markov_chain,
)
from researchos.quant_engine.probability.mle import (
    mle_normal,
    mle_log_normal,
    mle_student_t,
    generic_grid_mle,
)

__all__ = [
    "ConfidenceInterval",
    "DistributionFit",
    "DistributionType",
    "HypothesisTestResult",
    "MonteCarloResult",
    "TestStatistic",
    "normal_pdf",
    "normal_cdf",
    "student_t_pdf",
    "student_t_cdf",
    "log_normal_pdf",
    "empirical_cdf",
    "fit_normal",
    "fit_log_normal",
    "fit_student_t",
    "kernel_density_estimate",
    "confidence_interval_mean",
    "one_sample_t_test",
    "z_test",
    "bootstrap_mean",
    "monte_carlo_normal",
    "monte_carlo_return_paths",
    "probability_calibration",
    "BetaPosterior",
    "MarkovChain",
    "HiddenMarkovModel",
    "estimate_markov_chain",
    "mle_normal",
    "mle_log_normal",
    "mle_student_t",
    "generic_grid_mle",
]

