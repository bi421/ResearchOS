"""
ResearchOS Macro Intelligence Layer - Econometrics Engine
Version: ecm/v1
Status: FROZEN

Canonical deterministic econometrics engine. Owns ALL econometric algorithms
(multiple/polynomial/logistic regression, ACF/PACF, stationarity, cointegration,
causality, VIF, diagnostics, intervals, information criteria).

Single-variable OLS is delegated to the canonical Statistics owner; this
package never re-implements 1-D OLS.

MIL-ECM-001: Every econometric result is immutable and deterministic.
MIL-ECM-002: Provenance attaches via StatisticalProvenance.
MIL-ECM-004: Econometrics owns multiple/polynomial/logistic regression.
MIL-ECM-005: Econometrics never duplicates single-variable OLS.
"""

from macro_intelligence.econometrics.models import (
    RegressionResult,
    TestResult,
    ResidualDiagnostics,
    IntervalResult,
    InformationCriteria,
    ModelDiagnostics,
    deterministic_hash,
)

from macro_intelligence.econometrics.regression import (
    multiple_regression,
    polynomial_regression,
    logistic_regression,
    univariate_ols,
)

from macro_intelligence.econometrics.autocorrelation import (
    autocorrelation,
    partial_autocorrelation,
)

from macro_intelligence.econometrics.stationarity import (
    augmented_dickey_fuller,
    kpss,
)

from macro_intelligence.econometrics.cointegration import (
    engle_granger,
)

from macro_intelligence.econometrics.causality import (
    granger_causality,
)

from macro_intelligence.econometrics.vif import (
    variance_inflation_factor,
    vif,
)

from macro_intelligence.econometrics.heteroskedasticity import (
    breusch_pagan,
)

from macro_intelligence.econometrics.diagnostics import (
    durbin_watson,
    jarque_bera,
    residual_diagnostics,
    model_diagnostics,
)

from macro_intelligence.econometrics.intervals import (
    confidence_interval,
    prediction_interval,
)

from macro_intelligence.econometrics.information_criteria import (
    aic,
    bic,
    information_criteria,
)

__all__ = [
    # Models
    "RegressionResult",
    "TestResult",
    "ResidualDiagnostics",
    "IntervalResult",
    "InformationCriteria",
    "ModelDiagnostics",
    "deterministic_hash",
    # Regression
    "multiple_regression",
    "polynomial_regression",
    "logistic_regression",
    "univariate_ols",
    # Autocorrelation
    "autocorrelation",
    "partial_autocorrelation",
    # Stationarity
    "augmented_dickey_fuller",
    "kpss",
    # Cointegration
    "engle_granger",
    # Causality
    "granger_causality",
    # VIF
    "variance_inflation_factor",
    "vif",
    # Heteroskedasticity
    "breusch_pagan",
    # Diagnostics
    "durbin_watson",
    "jarque_bera",
    "residual_diagnostics",
    "model_diagnostics",
    # Intervals
    "confidence_interval",
    "prediction_interval",
    # Information criteria
    "aic",
    "bic",
    "information_criteria",
]
