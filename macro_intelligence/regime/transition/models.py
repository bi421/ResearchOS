"""
ResearchOS Macro Intelligence Layer - Regime Transition Models

Defines the data structures used by the regime transition analysis engine.
All models are frozen (immutable) dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from macro_intelligence.regime.classification.taxonomy import MacroRegime


ALGORITHM_VERSION = "trans-det/v4.0.0"


class TransitionType:
    STABLE = "stable"
    GRADUAL_SHIFT = "gradual_shift"
    ACCELERATED_SHIFT = "accelerated_shift"
    REVERSAL = "reversal"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TransitionSignal:
    detector_name: str
    signal_id: str
    signal_type: str
    strength: float
    direction: str
    contributing_factors: dict[str, float] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    details: str = ""
    algorithm_version: str = ALGORITHM_VERSION
    detection_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "detector_name": self.detector_name,
            "signal_id": self.signal_id,
            "signal_type": self.signal_type,
            "strength": self.strength,
            "direction": self.direction,
            "contributing_factors": dict(sorted(self.contributing_factors.items())),
            "evidence_refs": sorted(self.evidence_refs),
            "details": self.details,
            "algorithm_version": self.algorithm_version,
            "detection_timestamp": self.detection_timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransitionSignal:
        return cls(
            detector_name=data["detector_name"],
            signal_id=data["signal_id"],
            signal_type=data["signal_type"],
            strength=data["strength"],
            direction=data["direction"],
            contributing_factors=data.get("contributing_factors", {}),
            evidence_refs=data.get("evidence_refs", []),
            details=data.get("details", ""),
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            detection_timestamp=datetime.fromisoformat(
                data.get("detection_timestamp", datetime.now(timezone.utc).isoformat())
            ),
        )

    def compute_hash(self) -> str:
        import hashlib
        import json
        h = {"detector_name": self.detector_name, "signal_id": self.signal_id,
             "signal_type": self.signal_type, "strength": self.strength, "direction": self.direction}
        return hashlib.sha256(json.dumps(h, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class RegimeTransition:
    transition_id: str
    previous_regime: MacroRegime
    current_regime: MacroRegime
    transition_type: str
    confidence: float
    detected_at: datetime
    algorithm_version: str = ALGORITHM_VERSION
    duration_estimate: int | None = None
    signals: list[TransitionSignal] = field(default_factory=list)
    signal_evidence_refs: list[str] = field(default_factory=list)
    explanation: str = ""
    early_warning: bool = False
    early_warning_horizon: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "algorithm_version": self.algorithm_version,
            "previous_regime": self.previous_regime.value,
            "current_regime": self.current_regime.value,
            "transition_type": self.transition_type,
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat(),
            "duration_estimate": self.duration_estimate,
            "signals": [s.to_dict() for s in self.signals],
            "signal_evidence_refs": sorted(self.signal_evidence_refs),
            "explanation": self.explanation,
            "early_warning": self.early_warning,
            "early_warning_horizon": self.early_warning_horizon,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegimeTransition:
        signals = [TransitionSignal.from_dict(s) for s in data.get("signals", [])]
        return cls(
            transition_id=data["transition_id"],
            previous_regime=MacroRegime(data["previous_regime"]),
            current_regime=MacroRegime(data["current_regime"]),
            transition_type=data["transition_type"],
            confidence=data["confidence"],
            detected_at=datetime.fromisoformat(data["detected_at"]),
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            duration_estimate=data.get("duration_estimate"),
            signals=signals,
            signal_evidence_refs=data.get("signal_evidence_refs", []),
            explanation=data.get("explanation", ""),
            early_warning=data.get("early_warning", False),
            early_warning_horizon=data.get("early_warning_horizon"),
        )

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))

    @classmethod
    def from_json(cls, json_str: str) -> RegimeTransition:
        import json
        return cls.from_dict(json.loads(json_str))

    def compute_hash(self) -> str:
        import hashlib
        import json
        h = {"transition_id": self.transition_id,
             "previous_regime": self.previous_regime.value,
             "current_regime": self.current_regime.value,
             "transition_type": self.transition_type,
             "confidence": self.confidence,
             "signals": [s.compute_hash() for s in self.signals]}
        return hashlib.sha256(json.dumps(h, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class TransitionHistoryEntry:
    transition_id: str
    detected_at: datetime
    previous_regime: MacroRegime
    current_regime: MacroRegime
    transition_type: str
    confidence: float
    signals_count: int
    duration_observed: int | None = None
    outcome: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "detected_at": self.detected_at.isoformat(),
            "previous_regime": self.previous_regime.value,
            "current_regime": self.current_regime.value,
            "transition_type": self.transition_type,
            "confidence": self.confidence,
            "signals_count": self.signals_count,
            "duration_observed": self.duration_observed,
            "outcome": self.outcome,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransitionHistoryEntry:
        return cls(
            transition_id=data["transition_id"],
            detected_at=datetime.fromisoformat(data["detected_at"]),
            previous_regime=MacroRegime(data["previous_regime"]),
            current_regime=MacroRegime(data["current_regime"]),
            transition_type=data["transition_type"],
            confidence=data["confidence"],
            signals_count=data["signals_count"],
            duration_observed=data.get("duration_observed"),
            outcome=data.get("outcome"),
        )

    def compute_hash(self) -> str:
        import hashlib
        import json
        h = {"transition_id": self.transition_id,
             "previous_regime": self.previous_regime.value,
             "current_regime": self.current_regime.value,
             "transition_type": self.transition_type,
             "confidence": self.confidence}
        return hashlib.sha256(json.dumps(h, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class TransitionProbabilityMatrix:
    observation_count: int = 0
    transition_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    algorithm_version: str = ALGORITHM_VERSION
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    transition_probs: dict[str, dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm_version": self.algorithm_version,
            "last_updated": self.last_updated.isoformat(),
            "transition_probs": self.transition_probs,
            "observation_count": self.observation_count,
            "transition_counts": self.transition_counts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransitionProbabilityMatrix:
        return cls(
            observation_count=data.get("observation_count", 0),
            transition_counts=data.get("transition_counts", {}),
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now(timezone.utc).isoformat())),
            transition_probs=data.get("transition_probs", {}),
        )

    def compute_hash(self) -> str:
        import hashlib
        import json
        h = {"algorithm_version": self.algorithm_version,
             "transition_probs": self.transition_probs,
             "observation_count": self.observation_count}
        return hashlib.sha256(json.dumps(h, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class RegimePersistence:
    regime: MacroRegime
    persistence_periods: int
    avg_persistence: float
    continuation_probability: float
    days_since_last_transition: int
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "regime": self.regime.value,
            "persistence_periods": self.persistence_periods,
            "avg_persistence": self.avg_persistence,
            "continuation_probability": self.continuation_probability,
            "days_since_last_transition": self.days_since_last_transition,
            "signals": self.signals,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegimePersistence:
        return cls(
            regime=MacroRegime(data["regime"]),
            persistence_periods=data["persistence_periods"],
            avg_persistence=data["avg_persistence"],
            continuation_probability=data["continuation_probability"],
            days_since_last_transition=data["days_since_last_transition"],
            signals=data.get("signals", []),
        )

    def compute_hash(self) -> str:
        import hashlib
        import json
        h = {"regime": self.regime.value,
             "persistence_periods": self.persistence_periods,
             "continuation_probability": self.continuation_probability}
        return hashlib.sha256(json.dumps(h, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class EarlyWarningSignal:
    warning_id: str
    current_regime: MacroRegime
    predicted_regime: MacroRegime
    confidence: float
    horizon_periods: int
    algorithm_version: str = ALGORITHM_VERSION
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    contributing_signals: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "warning_id": self.warning_id,
            "algorithm_version": self.algorithm_version,
            "detected_at": self.detected_at.isoformat(),
            "current_regime": self.current_regime.value,
            "predicted_regime": self.predicted_regime.value,
            "confidence": self.confidence,
            "horizon_periods": self.horizon_periods,
            "contributing_signals": sorted(self.contributing_signals),
            "evidence_refs": sorted(self.evidence_refs),
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EarlyWarningSignal:
        return cls(
            warning_id=data["warning_id"],
            current_regime=MacroRegime(data["current_regime"]),
            predicted_regime=MacroRegime(data["predicted_regime"]),
            confidence=data["confidence"],
            horizon_periods=data["horizon_periods"],
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            detected_at=datetime.fromisoformat(data["detected_at"]),
            contributing_signals=data.get("contributing_signals", []),
            evidence_refs=data.get("evidence_refs", []),
            explanation=data.get("explanation", ""),
        )

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))

    @classmethod
    def from_json(cls, json_str: str) -> EarlyWarningSignal:
        import json
        return cls.from_dict(json.loads(json_str))

    def compute_hash(self) -> str:
        import hashlib
        import json
        h = {"warning_id": self.warning_id,
             "current_regime": self.current_regime.value,
             "predicted_regime": self.predicted_regime.value,
             "confidence": self.confidence,
             "horizon_periods": self.horizon_periods}
        return hashlib.sha256(json.dumps(h, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class TransitionAnalysisResult:
    analysis_id: str
    current_regime: MacroRegime
    previous_regime: MacroRegime | None = None
    algorithm_version: str = ALGORITHM_VERSION
    analysis_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    transition_detected: bool = False
    transition: RegimeTransition | None = None
    early_warnings: list[EarlyWarningSignal] = field(default_factory=list)
    persistence: RegimePersistence | None = None
    probability_matrix: TransitionProbabilityMatrix | None = None
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "analysis_id": self.analysis_id,
            "algorithm_version": self.algorithm_version,
            "analysis_time": self.analysis_time.isoformat(),
            "current_regime": self.current_regime.value,
            "previous_regime": self.previous_regime.value if self.previous_regime else None,
            "transition_detected": self.transition_detected,
            "early_warnings_count": len(self.early_warnings),
            "evidence_refs": sorted(self.evidence_refs),
        }
        if self.transition:
            result["transition"] = self.transition.to_dict()
        if self.early_warnings:
            result["early_warnings"] = [w.to_dict() for w in self.early_warnings]
        if self.persistence:
            result["persistence"] = self.persistence.to_dict()
        if self.probability_matrix:
            result["probability_matrix"] = self.probability_matrix.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransitionAnalysisResult:
        transition = RegimeTransition.from_dict(data["transition"]) if data.get("transition") else None
        early_warnings = [EarlyWarningSignal.from_dict(w) for w in data.get("early_warnings", [])]
        persistence = RegimePersistence.from_dict(data["persistence"]) if data.get("persistence") else None
        prob_matrix = TransitionProbabilityMatrix.from_dict(data["probability_matrix"]) if data.get("probability_matrix") else None
        prev = MacroRegime(data["previous_regime"]) if data.get("previous_regime") else None
        return cls(
            analysis_id=data["analysis_id"],
            current_regime=MacroRegime(data["current_regime"]),
            previous_regime=prev,
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            analysis_time=datetime.fromisoformat(data["analysis_time"]),
            transition_detected=data.get("transition_detected", False),
            transition=transition,
            early_warnings=early_warnings,
            persistence=persistence,
            probability_matrix=prob_matrix,
            evidence_refs=data.get("evidence_refs", []),
        )

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))

    @classmethod
    def from_json(cls, json_str: str) -> TransitionAnalysisResult:
        import json
        return cls.from_dict(json.loads(json_str))

    def compute_hash(self) -> str:
        import hashlib
        import json
        h = {"analysis_id": self.analysis_id,
             "current_regime": self.current_regime.value,
             "previous_regime": self.previous_regime.value if self.previous_regime else None,
             "transition_detected": self.transition_detected,
             "transition_id": self.transition.transition_id if self.transition else None}
        return hashlib.sha256(json.dumps(h, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
