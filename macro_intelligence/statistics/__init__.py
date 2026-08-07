"""
ResearchOS Macro Intelligence Layer - Statistical Computation Engine
Version: stat/v1
Status: FROZEN
"""

from macro_intelligence.statistics.descriptive import (
    mean,
    median,
    variance as desc_variance,
    std,
    skewness,
    kurtosis,
    min as desc_min,
    max as desc_max,
    percentile,
    descriptive_statistics,
)

from macro_intelligence.statistics.rolling import (
    rolling_mean,
    rolling_std,
    rolling_variance,
    rolling_zscore,
    rolling_statistics,
)

from macro_intelligence.statistics.correlation import (
    pearson_correlation,
    spearman_correlation,
    rolling_correlation,
)

from macro_intelligence.statistics.covariance import (
    covariance,
    rolling_covariance,
)

from macro_intelligence.statistics.regression import (
    linear_regression,
    slope,
    intercept,
    r_squared,
    RegressionResult,
)

from macro_intelligence.statistics.normalization import (
    min_max_normalize,
    zscore_normalize,
    robust_scale,
    normalize,
)

from macro_intelligence.statistics.trend import (
    moving_average,
    exponential_moving_average,
    trend_strength,
    momentum,
    trend_analysis,
)

from macro_intelligence.statistics.volatility import (
    rolling_volatility,
    realized_volatility,
    volatility_analysis,
)

from macro_intelligence.statistics.change_point import (
    cusum,
    detect_change_points,
)

from macro_intelligence.statistics.distributions import (
    empirical_distribution,
    quantiles,
    distribution_analysis,
    normal_cdf,
    incomplete_beta,
    t_distribution_p_value,
    p_value_from_correlation,
)

from macro_intelligence.statistics.provenance import (
    StatisticalProvenance,
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
