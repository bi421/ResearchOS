"""
Econometrics Engine — contracts, enums, and dataclass models.

Architecture for AR / MA / ARMA / ARIMA / SARIMA / VAR / cointegration /
Johansen / ADF / KPSS / GARCH / EGARCH / TGARCH / ARCH diagnostics /
volatility forecasting / ACF / PACF / residual diagnostics / stationarity.

Deterministic research-only computation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class StationarityResult(str, Enum):
    STATIONARY = "stationary"
    NON_STATIONARY = "non_stationary"
    INSUFFICIENT_DATA = "insufficient_data"


class ModelFamily(str, Enum):
    AR = "AR"
    MA = "MA"
    ARMA = "ARMA"
    ARIMA = "ARIMA"
    SARIMA = "SARIMA"
    VAR = "VAR"
    GARCH = "GARCH"
    EGARCH = "EGARCH"
    TGARCH = "TGARCH"


@dataclass(frozen=True)
class StationarityTestResult:
    """Result of a unit-root / stationarity test."""

    statistic: float
    critical_values: Dict[str, float] = field(default_factory=dict)
    p_value: float = 0.0
    is_stationary: bool = False
    test_name: str = ""
    conclusion: StationarityResult = StationarityResult.INSUFFICIENT_DATA

    def to_dict(self) -> Dict[str, Any]:
        return {
            "statistic": self.statistic,
            "critical_values": self.critical_values,
            "p_value": self.p_value,
            "is_stationary": self.is_stationary,
            "test_name": self.test_name,
            "conclusion": self.conclusion.value,
        }


@dataclass(frozen=True)
class FittedModel:
    """A fitted time-series model."""

    family: ModelFamily
    coefficients: Dict[str, float] = field(default_factory=dict)
    residuals: List[float] = field(default_factory=list)
    log_likelihood: float = 0.0
    aic: float = 0.0
    bic: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def predict(self, history: List[float], steps: int = 1) -> List[float]:
        """Deterministic recursive forecast."""
        out: List[float] = []
        work = list(history)
        for _ in range(steps):
            pred = 0.0
            keys = self.coefficients
            p_order = int(self.metadata.get("p_order", 0))
            q_order = int(self.metadata.get("q_order", 0))
            for i in range(1, p_order + 1):
                if len(work) - i >= 0:
                    pred += keys.get(f"ar_{i}", 0.0) * work[-i]
            for j in range(1, q_order + 1):
                if len(self.residuals) - j >= 0:
                    pred += keys.get(f"ma_{j}", 0.0) * self.residuals[-j]
            pred += keys.get("const", 0.0)
            out.append(pred)
            work.append(pred)
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family": self.family.value,
            "coefficients": dict(sorted(self.coefficients.items())),
            "log_likelihood": self.log_likelihood,
            "aic": self.aic,
            "bic": self.bic,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class VolatilityModelResult:
    """Result of a GARCH-family volatility model."""

    family: ModelFamily
    omega: float = 0.0
    alpha: float = 0.0
    beta: float = 0.0
    gamma: float = 0.0
    conditional_volatility: List[float] = field(default_factory=list)
    log_likelihood: float = 0.0
    forecast_volatility: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family": self.family.value,
            "omega": self.omega,
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "log_likelihood": self.log_likelihood,
            "forecast_volatility": self.forecast_volatility,
        }


@dataclass(frozen=True)
class AcfResult:
    """Autocorrelation, partial autocorrelation, and Ljung-Box statistics."""

    autocorrelations: List[float] = field(default_factory=list)
    partial_autocorrelations: List[float] = field(default_factory=list)
    ljung_box_q: float = 0.0
    ljung_box_p: float = 0.0
    max_lag: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "autocorrelations": self.autocorrelations,
            "partial_autocorrelations": self.partial_autocorrelations,
            "ljung_box_q": self.ljung_box_q,
            "ljung_box_p": self.ljung_box_p,
            "max_lag": self.max_lag,
        }


@dataclass(frozen=True)
class CointegrationTestResult:
    """Result of Engle-Granger two-step cointegration test."""

    alpha: float = 0.0
    beta: float = 0.0
    adf_statistic: float = 0.0
    p_value: float = 0.0
    is_cointegrated: bool = False
    residuals: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "adf_statistic": self.adf_statistic,
            "p_value": self.p_value,
            "is_cointegrated": self.is_cointegrated,
            "residuals": self.residuals,
        }


@dataclass(frozen=True)
class JohansenTestResult:
    """Result of Johansen vector cointegration test."""

    trace_statistics: List[float] = field(default_factory=list)
    eigenvalues: List[float] = field(default_factory=list)
    critical_values_95: List[float] = field(default_factory=list)
    cointegration_rank: int = 0
    is_cointegrated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_statistics": self.trace_statistics,
            "eigenvalues": self.eigenvalues,
            "critical_values_95": self.critical_values_95,
            "cointegration_rank": self.cointegration_rank,
            "is_cointegrated": self.is_cointegrated,
        }
