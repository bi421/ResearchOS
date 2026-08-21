"""
ResearchOS Macro Intelligence Layer - Statistical Computation Engine
Version: stat/v1
Status: FROZEN
"""

from researchos.macro.statistics.change_point import (
    cusum,
    detect_change_points,
)
from researchos.macro.statistics.correlation import (
    pearson_correlation,
    rolling_correlation,
    spearman_correlation,
)
from researchos.macro.statistics.covariance import (
    covariance,
    rolling_covariance,
)
from researchos.macro.statistics.descriptive import (
    descriptive_statistics,
    kurtosis,
    mean,
    median,
    percentile,
    skewness,
    std,
)
from researchos.macro.statistics.descriptive import (
    max as desc_max,
)
from researchos.macro.statistics.descriptive import (
    min as desc_min,
)
from researchos.macro.statistics.descriptive import (
    variance as desc_variance,
)
from researchos.macro.statistics.distributions import (
    distribution_analysis,
    empirical_distribution,
    incomplete_beta,
    normal_cdf,
    p_value_from_correlation,
    quantiles,
    t_distribution_p_value,
)
from researchos.macro.statistics.normalization import (
    min_max_normalize,
    normalize,
    robust_scale,
    zscore_normalize,
)
from researchos.macro.statistics.provenance import (
    StatisticalProvenance,
)
from researchos.macro.statistics.regression import (
    RegressionResult,
    intercept,
    linear_regression,
    r_squared,
    slope,
)
from researchos.macro.statistics.rolling import (
    rolling_mean,
    rolling_statistics,
    rolling_std,
    rolling_variance,
    rolling_zscore,
)
from researchos.macro.statistics.trend import (
    exponential_moving_average,
    momentum,
    moving_average,
    trend_analysis,
    trend_strength,
)
from researchos.macro.statistics.volatility import (
    realized_volatility,
    rolling_volatility,
    volatility_analysis,
)

__all__ = [
    # Descriptive
    "mean",
    "median",
    "variance",
    "desc_variance",
    "std",
    "skewness",
    "kurtosis",
    "min",
    "desc_min",
    "max",
    "desc_max",
    "percentile",
    "descriptive_statistics",
    # Rolling
    "rolling_mean",
    "rolling_std",
    "rolling_variance",
    "rolling_zscore",
    "rolling_statistics",
    # Correlation
    "pearson_correlation",
    "spearman_correlation",
    "rolling_correlation",
    # Covariance
    "covariance",
    "rolling_covariance",
    # Regression
    "linear_regression",
    "slope",
    "intercept",
    "r_squared",
    "RegressionResult",
    "regression_result",
    "desc_variance",
    "desc_min",
    "desc_max",
    "RegressionResult",
    # Normalization
    "min_max_normalize",
    "zscore_normalize",
    "robust_scale",
    "normalize",
    # Trend
    "moving_average",
    "exponential_moving_average",
    "trend_strength",
    "momentum",
    "trend_analysis",
    # Volatility
    "rolling_volatility",
    "realized_volatility",
    "volatility_analysis",
    # Change Point
    "cusum",
    "detect_change_points",
    # Distributions
    "empirical_distribution",
    "quantiles",
    "distribution_analysis",
    "normal_cdf",
    "incomplete_beta",
    "t_distribution_p_value",
    "p_value_from_correlation",
    # Provenance
    "StatisticalProvenance",
]
