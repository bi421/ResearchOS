"""
Econometrics Engine — deterministic time-series research analytics.

Pure Python, no external dependencies. Research-only.
"""

from researchos.quant_engine.econometrics.contracts import (
    AcfResult,
    CointegrationTestResult,
    FittedModel,
    JohansenTestResult,
    ModelFamily,
    StationarityResult,
    StationarityTestResult,
    VolatilityModelResult,
)
from researchos.quant_engine.econometrics.core import (
    autocorrelation,
    partial_autocorrelation,
    compute_acf,
    adf_test,
    kpss_test,
    fit_ar,
    fit_ma,
    fit_arma,
    fit_arima,
    fit_sarima,
    fit_var,
    engle_granger_cointegration,
    johansen_test,
    fit_garch,
    fit_egarch,
    fit_tgarch,
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
