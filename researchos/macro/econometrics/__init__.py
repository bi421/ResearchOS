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

from researchos.macro.econometrics.autocorrelation import (
    autocorrelation,
    partial_autocorrelation,
)
from researchos.macro.econometrics.causality import (
    granger_causality,
)
from researchos.macro.econometrics.cointegration import (
    engle_granger,
)
from researchos.macro.econometrics.diagnostics import (
    durbin_watson,
    jarque_bera,
    model_diagnostics,
    residual_diagnostics,
)
from researchos.macro.econometrics.heteroskedasticity import (
    breusch_pagan,
)
from researchos.macro.econometrics.information_criteria import (
    aic,
    bic,
    information_criteria,
)
from researchos.macro.econometrics.intervals import (
    confidence_interval,
    prediction_interval,
)
from researchos.macro.econometrics.models import (
    InformationCriteria,
    IntervalResult,
    ModelDiagnostics,
    RegressionResult,
    ResidualDiagnostics,
    TestResult,
    deterministic_hash,
)
from researchos.macro.econometrics.regression import (
    logistic_regression,
    multiple_regression,
    polynomial_regression,
    univariate_ols,
)
from researchos.macro.econometrics.stationarity import (
    augmented_dickey_fuller,
    kpss,
)
from researchos.macro.econometrics.vif import (
    variance_inflation_factor,
    vif,
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
