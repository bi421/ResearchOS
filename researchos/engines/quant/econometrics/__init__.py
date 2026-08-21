"""
Econometrics Engine — deterministic time-series research analytics.

Pure Python, no external dependencies. Research-only.
"""

from researchos.engines.quant.econometrics.contracts import (
    AcfResult,
    CointegrationTestResult,
    FittedModel,
    JohansenTestResult,
    ModelFamily,
    StationarityResult,
    StationarityTestResult,
    VolatilityModelResult,
)
from researchos.engines.quant.econometrics.core import (
    adf_test,
    autocorrelation,
    compute_acf,
    engle_granger_cointegration,
    fit_ar,
    fit_arima,
    fit_arma,
    fit_egarch,
    fit_garch,
    fit_ma,
    fit_sarima,
    fit_tgarch,
    fit_var,
    johansen_test,
    kpss_test,
    partial_autocorrelation,
)

__all__ = [
    "AcfResult",
    "CointegrationTestResult",
    "FittedModel",
    "JohansenTestResult",
    "ModelFamily",
    "StationarityResult",
    "StationarityTestResult",
    "VolatilityModelResult",
    "autocorrelation",
    "partial_autocorrelation",
    "compute_acf",
    "adf_test",
    "kpss_test",
    "fit_ar",
    "fit_ma",
    "fit_arma",
    "fit_arima",
    "fit_sarima",
    "fit_var",
    "engle_granger_cointegration",
    "johansen_test",
    "fit_garch",
    "fit_egarch",
    "fit_tgarch",
]
