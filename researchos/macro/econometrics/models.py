"""
ResearchOS Macro Intelligence Layer - Econometrics Engine Models
Version: ecm/models/v1
Status: FROZEN

Defines the immutable result contracts for the Econometrics Engine.

Every econometric result carries the institution-wide provenance envelope
(``StatisticalProvenance``) plus a deterministic result hash. All contracts
are frozen dataclasses; no mutable defaults; no random / uuid / wall-clock
in any hash.

MIL-ECM-001: Every econometric result is immutable and deterministic.
MIL-ECM-002: Provenance attaches to every result via StatisticalProvenance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, List, Optional

from researchos.macro.statistics.provenance import StatisticalProvenance


def _canonical(data: Any) -> str:
    """Deterministic canonical JSON (sorted keys, compact separators)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def deterministic_hash(data: Any) -> str:
    """Deterministic SHA-256 over canonical JSON. Never uses hash()/random."""
    return hashlib.sha256(_canonical(data).encode("utf-8")).hexdigest()


def _freeze_dict(d: Optional[Dict[str, Any]]) -> MappingProxyType:
    """Return an immutable mapping view of a dict (empty if None)."""
    if not d:
        return MappingProxyType({})
    return MappingProxyType(d)


@dataclass(frozen=True)
class RegressionResult:
    """
    Immutable result of a regression fit.

    Attributes:
        coefficients: Estimated coefficients (intercept first, then predictors).
        r_squared: Coefficient of determination (R^2).
        adjusted_r_squared: Adjusted R^2.
        standard_errors: Standard errors of the coefficients.
        t_stats: t-statistics of the coefficients.
        p_values: p-values of the coefficients.
        fitted_values: Model predictions for the training observations.
        residuals: Residuals (y - fitted).
        n_observations: Number of observations.
        n_features: Number of predictor features (excl. intercept).
        method: The regression method name (e.g. "ols", "multiple", "polynomial", "logistic").
        method_version: Version identifier of the algorithm.
        converged: Whether iterative fitting converged (True for closed-form OLS).
        iterations: Number of iterations used (0 for closed-form).
        provenance: Institution-wide provenance envelope.
        result_hash: Deterministic SHA-256 over the result content.
    """

    coefficients: List[float]
    r_squared: float
    adjusted_r_squared: float
    standard_errors: List[float]
    t_stats: List[float]
    p_values: List[float]
    fitted_values: List[float]
    residuals: List[float]
    n_observations: int
    n_features: int
    method: str
    method_version: str
    converged: bool = True
    iterations: int = 0
    provenance: StatisticalProvenance = field(default_factory=StatisticalProvenance)
    result_hash: str = ""

    def __post_init__(self) -> None:
        # Freeze the coefficient lists (replace mutable lists with tuples).
        object.__setattr__(self, "coefficients", tuple(self.coefficients))
        object.__setattr__(self, "standard_errors", tuple(self.standard_errors))
        object.__setattr__(self, "t_stats", tuple(self.t_stats))
        object.__setattr__(self, "p_values", tuple(self.p_values))
        object.__setattr__(self, "fitted_values", tuple(self.fitted_values))
        object.__setattr__(self, "residuals", tuple(self.residuals))
        # Compute the deterministic result hash if not already set.
        if not self.result_hash:
            content = {
                "coefficients": list(self.coefficients),
                "r_squared": self.r_squared,
                "adjusted_r_squared": self.adjusted_r_squared,
                "standard_errors": list(self.standard_errors),
                "t_stats": list(self.t_stats),
                "p_values": list(self.p_values),
                "n_observations": self.n_observations,
                "n_features": self.n_features,
                "method": self.method,
                "method_version": self.method_version,
                "converged": self.converged,
                "iterations": self.iterations,
                "provenance": self.provenance.to_dict(),
            }
            object.__setattr__(self, "result_hash", deterministic_hash(content))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary (stable ordering)."""
        return {
            "coefficients": list(self.coefficients),
            "r_squared": self.r_squared,
            "adjusted_r_squared": self.adjusted_r_squared,
            "standard_errors": list(self.standard_errors),
            "t_stats": list(self.t_stats),
            "p_values": list(self.p_values),
            "fitted_values": list(self.fitted_values),
            "residuals": list(self.residuals),
            "n_observations": self.n_observations,
            "n_features": self.n_features,
            "method": self.method,
            "method_version": self.method_version,
            "converged": self.converged,
            "iterations": self.iterations,
            "provenance": self.provenance.to_dict(),
            "result_hash": self.result_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RegressionResult:
        """Deserialize from a dictionary."""
        return cls(
            coefficients=list(data["coefficients"]),
            r_squared=data["r_squared"],
            adjusted_r_squared=data["adjusted_r_squared"],
            standard_errors=list(data["standard_errors"]),
            t_stats=list(data["t_stats"]),
            p_values=list(data["p_values"]),
            fitted_values=list(data.get("fitted_values", [])),
            residuals=list(data.get("residuals", [])),
            n_observations=data["n_observations"],
            n_features=data["n_features"],
            method=data["method"],
            method_version=data["method_version"],
            converged=data.get("converged", True),
            iterations=data.get("iterations", 0),
            provenance=StatisticalProvenance.from_dict(data.get("provenance", {})),
            result_hash=data.get("result_hash", ""),
        )

    def evidence_metadata(self) -> Dict[str, Any]:
        """Return structured evidence metadata for future EvidenceGraph integration.

        Exposes provenance and diagnostic metadata sufficient for the
        EvidenceGraph consumer without creating the EvidenceGraph itself
        (Phase 3.5 preparation only). All values are deterministic and derived
        from the immutable result state. Returns a plain dict (safe to extend).
        """
        return {
            "artifact_type": "regression_result",
            "algorithm_id": self.method_version,
            "computation_method": self.provenance.computation_method,
            "method": self.method,
            "n_observations": self.n_observations,
            "n_features": self.n_features,
            "r_squared": self.r_squared,
            "adjusted_r_squared": self.adjusted_r_squared,
            "converged": self.converged,
            "iterations": self.iterations,
            "n_coefficients": len(self.coefficients),
            "n_significant_pvalues": sum(1 for p in self.p_values if p is not None and p < 0.05),
            "is_deterministic": True,
            "provenance": self.provenance.to_dict(),
            "result_hash": self.result_hash,
        }


@dataclass(frozen=True)
class TestResult:
    """
    Immutable result of a hypothesis / specification test.

    Attributes:
        test_name: Name of the test (e.g. "adf", "kpss", "engle_granger", "granger").
        statistic: Test statistic value.
        p_value: p-value (may be None if not computable).
        critical_values: Dict of critical values at significance levels.
        is_significant: Whether the test rejects at the default significance level.
        parameters: The input parameters used for the test.
        provenance: Institution-wide provenance envelope.
        result_hash: Deterministic SHA-256 over the result content.
    """

    test_name: str
    statistic: float
    p_value: Optional[float]
    critical_values: Dict[str, float]
    is_significant: bool
    parameters: Dict[str, Any]
    provenance: StatisticalProvenance = field(default_factory=StatisticalProvenance)
    result_hash: str = ""

    def __post_init__(self) -> None:
        # Freeze critical_values and parameters.
        object.__setattr__(self, "critical_values", MappingProxyType(dict(self.critical_values)))
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
        if not self.result_hash:
            content = {
                "test_name": self.test_name,
                "statistic": self.statistic,
                "p_value": self.p_value,
                "critical_values": dict(self.critical_values),
                "is_significant": self.is_significant,
                "parameters": dict(self.parameters),
                "provenance": self.provenance.to_dict(),
            }
            object.__setattr__(self, "result_hash", deterministic_hash(content))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary (stable ordering)."""
        return {
            "test_name": self.test_name,
            "statistic": self.statistic,
            "p_value": self.p_value,
            "critical_values": dict(self.critical_values),
            "is_significant": self.is_significant,
            "parameters": dict(self.parameters),
            "provenance": self.provenance.to_dict(),
            "result_hash": self.result_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TestResult:
        """Deserialize from a dictionary."""
        return cls(
            test_name=data["test_name"],
            statistic=data["statistic"],
            p_value=data.get("p_value"),
            critical_values=data.get("critical_values", {}),
            is_significant=data.get("is_significant", False),
            parameters=data.get("parameters", {}),
            provenance=StatisticalProvenance.from_dict(data.get("provenance", {})),
            result_hash=data.get("result_hash", ""),
        )


@dataclass(frozen=True)
class ResidualDiagnostics:
    """
    Immutable diagnostics computed from model residuals.

    Attributes:
        mean: Mean of residuals.
        std: Standard deviation of residuals.
        skewness: Skewness of residuals.
        kurtosis: Excess kurtosis of residuals.
        jarque_bera: Jarque-Bera test statistic.
        jarque_bera_p_value: p-value of the Jarque-Bera test.
        durbin_watson: Durbin-Watson statistic.
        breusch_pagan_statistic: Breusch-Pagan test statistic.
        breusch_pagan_p_value: p-value of the Breusch-Pagan test.
        n_observations: Number of residuals.
        provenance: Institution-wide provenance envelope.
        result_hash: Deterministic SHA-256 over the result content.
    """

    mean: float
    std: float
    skewness: float
    kurtosis: float
    jarque_bera: float
    jarque_bera_p_value: float
    durbin_watson: float
    breusch_pagan_statistic: float
    breusch_pagan_p_value: float
    n_observations: int
    provenance: StatisticalProvenance = field(default_factory=StatisticalProvenance)
    result_hash: str = ""

    def __post_init__(self) -> None:
        if not self.result_hash:
            content = {
                "mean": self.mean,
                "std": self.std,
                "skewness": self.skewness,
                "kurtosis": self.kurtosis,
                "jarque_bera": self.jarque_bera,
                "jarque_bera_p_value": self.jarque_bera_p_value,
                "durbin_watson": self.durbin_watson,
                "breusch_pagan_statistic": self.breusch_pagan_statistic,
                "breusch_pagan_p_value": self.breusch_pagan_p_value,
                "n_observations": self.n_observations,
                "provenance": self.provenance.to_dict(),
            }
            object.__setattr__(self, "result_hash", deterministic_hash(content))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary (stable ordering)."""
        return {
            "mean": self.mean,
            "std": self.std,
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
            "jarque_bera": self.jarque_bera,
            "jarque_bera_p_value": self.jarque_bera_p_value,
            "durbin_watson": self.durbin_watson,
            "breusch_pagan_statistic": self.breusch_pagan_statistic,
            "breusch_pagan_p_value": self.breusch_pagan_p_value,
            "n_observations": self.n_observations,
            "provenance": self.provenance.to_dict(),
            "result_hash": self.result_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ResidualDiagnostics:
        """Deserialize from a dictionary."""
        return cls(
            mean=data["mean"],
            std=data["std"],
            skewness=data["skewness"],
            kurtosis=data["kurtosis"],
            jarque_bera=data["jarque_bera"],
            jarque_bera_p_value=data["jarque_bera_p_value"],
            durbin_watson=data["durbin_watson"],
            breusch_pagan_statistic=data["breusch_pagan_statistic"],
            breusch_pagan_p_value=data["breusch_pagan_p_value"],
            n_observations=data["n_observations"],
            provenance=StatisticalProvenance.from_dict(data.get("provenance", {})),
            result_hash=data.get("result_hash", ""),
        )


@dataclass(frozen=True)
class IntervalResult:
    """
    Immutable confidence or prediction interval.

    Attributes:
        level: Confidence level (e.g. 0.95).
        lower: Lower bound.
        upper: Upper bound.
        kind: "confidence" or "prediction".
        deterministic: Whether the interval is deterministic (always True).
        provenance: Institution-wide provenance envelope.
        result_hash: Deterministic SHA-256 over the result content.
    """

    level: float
    lower: float
    upper: float
    kind: str
    deterministic: bool = True
    provenance: StatisticalProvenance = field(default_factory=StatisticalProvenance)
    result_hash: str = ""

    def __post_init__(self) -> None:
        if not self.result_hash:
            content = {
                "level": self.level,
                "lower": self.lower,
                "upper": self.upper,
                "kind": self.kind,
                "deterministic": self.deterministic,
                "provenance": self.provenance.to_dict(),
            }
            object.__setattr__(self, "result_hash", deterministic_hash(content))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary (stable ordering)."""
        return {
            "level": self.level,
            "lower": self.lower,
            "upper": self.upper,
            "kind": self.kind,
            "deterministic": self.deterministic,
            "provenance": self.provenance.to_dict(),
            "result_hash": self.result_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IntervalResult:
        """Deserialize from a dictionary."""
        return cls(
            level=data["level"],
            lower=data["lower"],
            upper=data["upper"],
            kind=data["kind"],
            deterministic=data.get("deterministic", True),
            provenance=StatisticalProvenance.from_dict(data.get("provenance", {})),
            result_hash=data.get("result_hash", ""),
        )


@dataclass(frozen=True)
class InformationCriteria:
    """
    Immutable information criteria for model comparison.

    Attributes:
        aic: Akaike Information Criterion.
        bic: Bayesian Information Criterion.
        log_likelihood: Maximized log-likelihood.
        n_observations: Number of observations.
        n_parameters: Number of estimated parameters.
        provenance: Institution-wide provenance envelope.
        result_hash: Deterministic SHA-256 over the result content.
    """

    aic: float
    bic: float
    log_likelihood: float
    n_observations: int
    n_parameters: int
    provenance: StatisticalProvenance = field(default_factory=StatisticalProvenance)
    result_hash: str = ""

    def __post_init__(self) -> None:
        if not self.result_hash:
            content = {
                "aic": self.aic,
                "bic": self.bic,
                "log_likelihood": self.log_likelihood,
                "n_observations": self.n_observations,
                "n_parameters": self.n_parameters,
                "provenance": self.provenance.to_dict(),
            }
            object.__setattr__(self, "result_hash", deterministic_hash(content))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary (stable ordering)."""
        return {
            "aic": self.aic,
            "bic": self.bic,
            "log_likelihood": self.log_likelihood,
            "n_observations": self.n_observations,
            "n_parameters": self.n_parameters,
            "provenance": self.provenance.to_dict(),
            "result_hash": self.result_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InformationCriteria:
        """Deserialize from a dictionary."""
        return cls(
            aic=data["aic"],
            bic=data["bic"],
            log_likelihood=data["log_likelihood"],
            n_observations=data["n_observations"],
            n_parameters=data["n_parameters"],
            provenance=StatisticalProvenance.from_dict(data.get("provenance", {})),
            result_hash=data.get("result_hash", ""),
        )


@dataclass(frozen=True)
class ModelDiagnostics:
    """
    Immutable aggregate of model + residual diagnostics.

    Attributes:
        regression: The regression result (or None if not applicable).
        residual: Residual diagnostics.
        information_criteria: Information criteria (or None).
        provenance: Institution-wide provenance envelope.
        result_hash: Deterministic SHA-256 over the result content.
    """

    regression: Optional[RegressionResult]
    residual: ResidualDiagnostics
    information_criteria: Optional[InformationCriteria]
    provenance: StatisticalProvenance = field(default_factory=StatisticalProvenance)
    result_hash: str = ""

    def __post_init__(self) -> None:
        if not self.result_hash:
            content = {
                "regression": self.regression.to_dict() if self.regression else None,
                "residual": self.residual.to_dict(),
                "information_criteria": (
                    self.information_criteria.to_dict() if self.information_criteria else None
                ),
                "provenance": self.provenance.to_dict(),
            }
            object.__setattr__(self, "result_hash", deterministic_hash(content))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary (stable ordering)."""
        return {
            "regression": self.regression.to_dict() if self.regression else None,
            "residual": self.residual.to_dict(),
            "information_criteria": (
                self.information_criteria.to_dict() if self.information_criteria else None
            ),
            "provenance": self.provenance.to_dict(),
            "result_hash": self.result_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelDiagnostics:
        """Deserialize from a dictionary."""
        regression = None
        if data.get("regression"):
            regression = RegressionResult.from_dict(data["regression"])
        residual = ResidualDiagnostics.from_dict(data["residual"])
        information_criteria = None
        if data.get("information_criteria"):
            information_criteria = InformationCriteria.from_dict(data["information_criteria"])
        return cls(
            regression=regression,
            residual=residual,
            information_criteria=information_criteria,
            provenance=StatisticalProvenance.from_dict(data.get("provenance", {})),
            result_hash=data.get("result_hash", ""),
        )


__all__ = [
    "deterministic_hash",
    "RegressionResult",
    "TestResult",
    "ResidualDiagnostics",
    "IntervalResult",
    "InformationCriteria",
    "ModelDiagnostics",
]
