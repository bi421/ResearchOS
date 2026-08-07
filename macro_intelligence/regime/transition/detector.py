"""
ResearchOS Macro Intelligence Layer - Regime Transition Detector

Main orchestrator for regime transition analysis.
Detects transitions, computes probabilities, and manages history.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from macro_intelligence.statistics.provenance import content_hash
from macro_intelligence.regime.classification.taxonomy import MacroRegime
from macro_intelligence.regime.classification.classifier import RegimeClassifier
from macro_intelligence.regime.detection.models import RegimeAssessment
from macro_intelligence.regime.transition.models import (
    ALGORITHM_VERSION,
    TransitionSignal,
    RegimeTransition,
    TransitionProbabilityMatrix,
    RegimePersistence,
    EarlyWarningSignal,
    TransitionAnalysisResult,
    TransitionType,
)
from macro_intelligence.regime.transition.transitions import (
    classify_transition_type,
    should_generate_early_warning,
    estimate_early_warning_horizon,
    calculate_continuation_probability,
)
from macro_intelligence.regime.transition.probability import TransitionProbabilityEngine
from macro_intelligence.regime.transition.history import TransitionHistory


class RegimeTransitionDetector:
    """
    Main orchestrator for regime transition analysis.
    
    Combines detection, classification, probability, and history
    to provide comprehensive transition analysis.
    """
    
    def __init__(self, history: TransitionHistory | None = None):
        self._version = ALGORITHM_VERSION
        self._history = history or TransitionHistory()
        self._probability_engine = TransitionProbabilityEngine()
        self._classifier = RegimeClassifier()
        self._analysis_counter = 0
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def history(self) -> TransitionHistory:
        return self._history
    
    @property
    def probability_engine(self) -> TransitionProbabilityEngine:
        return self._probability_engine
    
    def detect_transition(
        self,
        current_assessment: RegimeAssessment,
        previous_regime: MacroRegime | None = None,
    ) -> RegimeTransition | None:
        """
        Detect a regime transition from current assessment.
        
        Args:
            current_assessment: Current regime assessment
            previous_regime: Previous known regime (None = first assessment)
            
        Returns:
            RegimeTransition if a transition is detected, None otherwise
        """
        # Classify current regime
        classification = self._classifier.classify_macro_regime(current_assessment)
        current_regime = classification.primary_regime
        
        # No transition if no previous regime or same regime
        if previous_regime is None:
            return None
        if current_regime == previous_regime:
            return None
        
        # Build transition signals from detector evidence
        signals = self._build_transition_signals(current_assessment)
        
        # Compute confidence
        confidence = self._compute_transition_confidence(
            current_assessment, signals
        )
        
        # Classify transition type
        signal_strengths = [s.strength for s in signals]
        signal_agreement = self._compute_signal_agreement(signals)
        persistence = self._estimate_persistence(current_assessment)
        
        transition_type = classify_transition_type(
            signal_strengths, signal_agreement, confidence, persistence
        )
        
        # Generate transition ID.
        # Content-derived deterministic ID: identical scientific inputs produce
        # an identical transition_id (no wall-clock time).
        self._analysis_counter += 1
        transition_id = "TRANS-" + content_hash(
            {
                "previous": previous_regime.value,
                "current": current_regime.value,
                "type": transition_type,
                "confidence": confidence,
            }
        )
        
        # Build explanation
        explanation = self._build_transition_explanation(
            previous_regime, current_regime, transition_type, signals
        )
        
        return RegimeTransition(
            transition_id=transition_id,
            previous_regime=previous_regime,
            current_regime=current_regime,
            transition_type=transition_type,
            confidence=confidence,
            detected_at=datetime.now(timezone.utc),
            signals=signals,
            signal_evidence_refs=self._collect_evidence_refs(signals),
            explanation=explanation,
        )
    
    def analyze_transitions(
        self,
        current_assessment: RegimeAssessment,
        previous_assessment: RegimeAssessment | None = None,
    ) -> TransitionAnalysisResult:
        """
        Full transition analysis combining detection, probability, and history.
        
        Args:
            current_assessment: Current regime assessment
            previous_assessment: Previous regime assessment
            
        Returns:
            Complete TransitionAnalysisResult
        """
        # Classify current and previous regimes
        current_classification = self._classifier.classify_macro_regime(current_assessment)
        current_regime = current_classification.primary_regime
        
        previous_regime = None
        if previous_assessment is not None:
            prev_classification = self._classifier.classify_macro_regime(previous_assessment)
            previous_regime = prev_classification.primary_regime
        
        # Detect transition
        transition = self.detect_transition(current_assessment, previous_regime)
        
        # Check for early warnings
        early_warnings = self._detect_early_warnings(
            current_assessment, current_regime
        )
        
        # Get persistence
        persistence = self._analyze_persistence(current_assessment, current_regime)
        
        # Get probability matrix
        prob_matrix = self._probability_engine.to_dict()
        
        # Build result.
        # Content-derived deterministic analysis_id: identical scientific
        # inputs produce an identical analysis_id (no wall-clock time).
        result = TransitionAnalysisResult(
            analysis_id="ANALYSIS-" + content_hash(
                {
                    "current": current_regime.value,
                    "previous": previous_regime.value if previous_regime else None,
                    "transition": transition.transition_id if transition else None,
                    "warnings": [w.warning_id for w in early_warnings],
                }
            ),
            current_regime=current_regime,
            previous_regime=previous_regime,
            analysis_time=datetime.now(timezone.utc),
            transition_detected=transition is not None,
            transition=transition,
            early_warnings=early_warnings,
            persistence=persistence,
            probability_matrix=TransitionProbabilityMatrix.from_dict(prob_matrix) if prob_matrix else None,
            evidence_refs=self._collect_all_evidence_refs(current_assessment, early_warnings),
        )
        
        # Record in history if transition detected
        if transition is not None:
            self._history.add_transition(transition)
        
        return result
    
    def _build_transition_signals(
        self,
        assessment: RegimeAssessment,
    ) -> list[TransitionSignal]:
        """Build transition signals from detector evidence."""
        signals = []
        
        # Inflation signal
        signals.append(TransitionSignal(
            detector_name="inflation_detector",
            signal_id="TRANS-INF-001",
            signal_type=self._signal_type_from_confidence(assessment.inflation_signal.confidence),
            strength=assessment.inflation_signal.confidence,
            direction=self._detect_direction(assessment.inflation_signal.signal),
            contributing_factors=assessment.inflation_signal.contributing_factors,
            evidence_refs=assessment.inflation_signal.evidence_refs,
            details=f"Inflation: {assessment.inflation_signal.signal}",
        ))
        
        # Growth signal
        signals.append(TransitionSignal(
            detector_name="growth_detector",
            signal_id="TRANS-GRW-001",
            signal_type=self._signal_type_from_confidence(assessment.growth_signal.confidence),
            strength=assessment.growth_signal.confidence,
            direction=self._detect_direction(assessment.growth_signal.signal),
            contributing_factors=assessment.growth_signal.contributing_factors,
            evidence_refs=assessment.growth_signal.evidence_refs,
            details=f"Growth: {assessment.growth_signal.signal}",
        ))
        
        # Monetary signal
        signals.append(TransitionSignal(
            detector_name="monetary_detector",
            signal_id="TRANS-MON-001",
            signal_type=self._signal_type_from_confidence(assessment.monetary_signal.confidence),
            strength=assessment.monetary_signal.confidence,
            direction=self._detect_direction(assessment.monetary_signal.signal),
            contributing_factors=assessment.monetary_signal.contributing_factors,
            evidence_refs=assessment.monetary_signal.evidence_refs,
            details=f"Monetary: {assessment.monetary_signal.signal}",
        ))
        
        # Liquidity signal
        signals.append(TransitionSignal(
            detector_name="liquidity_detector",
            signal_id="TRANS-LIQ-001",
            signal_type=self._signal_type_from_confidence(assessment.liquidity_signal.confidence),
            strength=assessment.liquidity_signal.confidence,
            direction=self._detect_direction(assessment.liquidity_signal.signal),
            contributing_factors=assessment.liquidity_signal.contributing_factors,
            evidence_refs=assessment.liquidity_signal.evidence_refs,
            details=f"Liquidity: {assessment.liquidity_signal.signal}",
        ))
        
        # Employment signal
        signals.append(TransitionSignal(
            detector_name="employment_detector",
            signal_id="TRANS-EMP-001",
            signal_type=self._signal_type_from_confidence(assessment.employment_signal.confidence),
            strength=assessment.employment_signal.confidence,
            direction=self._detect_direction(assessment.employment_signal.signal),
            contributing_factors=assessment.employment_signal.contributing_factors,
            evidence_refs=assessment.employment_signal.evidence_refs,
            details=f"Employment: {assessment.employment_signal.signal}",
        ))
        
        # Risk signal
        signals.append(TransitionSignal(
            detector_name="risk_detector",
            signal_id="TRANS-RSK-001",
            signal_type=self._signal_type_from_confidence(assessment.risk_signal.confidence),
            strength=assessment.risk_signal.confidence,
            direction=self._detect_direction(assessment.risk_signal.signal),
            contributing_factors=assessment.risk_signal.contributing_factors,
            evidence_refs=assessment.risk_signal.evidence_refs,
            details=f"Risk: {assessment.risk_signal.signal}",
        ))
        
        return signals
    
    def _compute_transition_confidence(
        self,
        assessment: RegimeAssessment,
        signals: list[TransitionSignal],
    ) -> float:
        """Compute transition confidence from signals."""
        if not signals:
            return 0.0
        
        # Weighted average of signal strengths
        weights = {
            "inflation_detector": 1.2,
            "growth_detector": 1.3,
            "monetary_detector": 1.0,
            "liquidity_detector": 0.9,
            "employment_detector": 1.1,
            "risk_detector": 1.2,
        }
        
        total_weight = 0.0
        weighted_sum = 0.0
        for signal in signals:
            weight = weights.get(signal.detector_name, 1.0)
            weighted_sum += signal.strength * weight
            total_weight += weight
        
        confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
        return round(max(0.0, min(1.0, confidence)), 2)
    
    def _compute_signal_agreement(self, signals: list[TransitionSignal]) -> float:
        """Compute the fraction of signals that agree on transition direction."""
        if not signals:
            return 0.0
        
        # Count signals with strength > 0.5 (active signals)
        active = [s for s in signals if s.strength > 0.5]
        if not active:
            return 0.0
        
        # Count signals pointing in same direction
        directions = [s.direction for s in active]
        from collections import Counter
        dir_counts = Counter(directions)
        most_common_count = dir_counts.most_common(1)[0][1]
        
        return round(most_common_count / len(active), 2)
    
    def _estimate_persistence(self, assessment: RegimeAssessment) -> int:
        """Estimate current regime persistence in periods."""
        # Simple heuristic: lower confidence in all detectors suggests shorter persistence
        avg_confidence = sum([
            assessment.inflation_signal.confidence,
            assessment.growth_signal.confidence,
            assessment.monetary_signal.confidence,
            assessment.liquidity_signal.confidence,
            assessment.employment_signal.confidence,
            assessment.risk_signal.confidence,
        ]) / 6.0
        
        # Map confidence to estimated persistence periods
        # Higher confidence = more stable = longer persistence
        if avg_confidence > 0.8:
            return 12
        elif avg_confidence > 0.6:
            return 8
        elif avg_confidence > 0.4:
            return 5
        else:
            return 3
    
    def _detect_early_warnings(
        self,
        assessment: RegimeAssessment,
        current_regime: MacroRegime,
    ) -> list[EarlyWarningSignal]:
        """Detect early warning signals for potential transitions."""
        warnings = []
        signals = self._build_transition_signals(assessment)
        signal_strengths = [s.strength for s in signals]
        
        # Get next regime probabilities
        probs = self._probability_engine.get_next_regime_probabilities(current_regime)
        
        for target_regime, prob in probs.items():
            if target_regime == current_regime:
                continue
            
            # Check if probability is significant
            if prob < 0.15:
                continue
            
            # Check if signals support this transition
            confidence = prob * max(signal_strengths) if signal_strengths else 0
            
            if should_generate_early_warning(confidence, 0, signal_strengths):
                horizon = estimate_early_warning_horizon(signal_strengths, confidence)
                
                warning = EarlyWarningSignal(
                    warning_id=f"WARN-{current_regime.value}-{target_regime.value}-{len(warnings)+1:03d}",
                    current_regime=current_regime,
                    predicted_regime=target_regime,
                    confidence=round(confidence, 2),
                    horizon_periods=horizon,
                    contributing_signals=[
                        s.detector_name for s in signals if s.strength > 0.5
                    ],
                    evidence_refs=self._collect_evidence_refs(signals),
                    explanation=f"Transition from {current_regime.value} to {target_regime.value} "
                                f"with confidence {confidence:.2f}",
                )
                warnings.append(warning)
        
        # Sort by confidence descending
        warnings.sort(key=lambda w: w.confidence, reverse=True)
        return warnings
    
    def _analyze_persistence(
        self,
        assessment: RegimeAssessment,
        current_regime: MacroRegime,
    ) -> RegimePersistence:
        """Analyze regime persistence."""
        signals = self._build_transition_signals(assessment)
        signal_strengths = [s.strength for s in signals]
        
        persistence_periods = self._estimate_persistence(assessment)
        
        # Get historical average persistence for this regime
        historical_avg = self._get_historical_avg_persistence(current_regime)
        
        continuation_prob = calculate_continuation_probability(
            persistence_periods, historical_avg, signal_strengths
        )
        
        return RegimePersistence(
            regime=current_regime,
            persistence_periods=persistence_periods,
            avg_persistence=historical_avg,
            continuation_probability=continuation_prob,
            days_since_last_transition=persistence_periods * 5,  # Approximate
            signals=[s.signal_id for s in signals if s.strength > 0.5],
        )
    
    def _get_historical_avg_persistence(self, regime: MacroRegime) -> float:
        """Get historical average persistence for a regime from history."""
        entries = self._history.get_transitions()
        
        # Count appearances of this regime as target.
        # O(n) single pass: use enumerate to avoid O(n) index() per entry.
        appearances = 0
        total_persistence = 0
        for idx, entry in enumerate(entries):
            if entry.current_regime == regime:
                appearances += 1
                # Estimate persistence from time since detection
                if idx > 0:
                    time_diff = (entries[idx - 1].detected_at - entry.detected_at).days
                    total_persistence += max(1, time_diff // 5)
        
        if appearances > 0:
            return round(total_persistence / appearances, 1)
        
        # Default values based on regime
        defaults = {
            MacroRegime.GOLDILOCKS: 10.0,
            MacroRegime.INFLATIONARY_GROWTH: 6.0,
            MacroRegime.STAGFLATION: 4.0,
            MacroRegime.DISINFLATION: 5.0,
            MacroRegime.DEFLATIONARY_SLOWDOWN: 7.0,
            MacroRegime.RECESSION: 8.0,
        }
        return defaults.get(regime, 6.0)
    
    def _signal_type_from_confidence(self, confidence: float) -> str:
        """Map confidence to signal type."""
        if confidence >= 0.8:
            return TransitionType.ACCELERATED_SHIFT
        elif confidence >= 0.6:
            return TransitionType.GRADUAL_SHIFT
        elif confidence >= 0.4:
            return TransitionType.GRADUAL_SHIFT
        else:
            return TransitionType.STABLE
    
    def _detect_direction(self, signal: str) -> str:
        """Detect transition direction from signal."""
        # Signals indicating economic tightening/restriction
        tightening = {"high", "hawkish", "contracting", "stressed", "crisis", "rising", "recession"}
        # Signals indicating economic easing
        easing = {"low", "dovish", "expanding", "strong", "risk_on", "falling", "recovery"}
        
        if signal in tightening:
            return "UP"  # Pressure upward (inflation, rates, stress)
        elif signal in easing:
            return "DOWN"  # Pressure downward
        else:
            return "NEUTRAL"
    
    def _build_transition_explanation(
        self,
        previous: MacroRegime,
        current: MacroRegime,
        transition_type: str,
        signals: list[TransitionSignal],
    ) -> str:
        """Build human-readable transition explanation."""
        parts = [
            f"Regime transition: {previous.value} → {current.value}",
            f"Type: {transition_type}",
        ]
        
        # Add top contributing signals
        top_signals = sorted(signals, key=lambda s: s.strength, reverse=True)[:3]
        signal_descs = [f"{s.detector_name}: {s.signal_type} ({s.strength:.2f})" for s in top_signals]
        if signal_descs:
            parts.append("Signals: " + "; ".join(signal_descs))
        
        return ". ".join(parts)
    
    def _collect_evidence_refs(self, signals: list[TransitionSignal]) -> list[str]:
        """Collect all evidence references from signals."""
        refs = []
        for signal in signals:
            refs.extend(signal.evidence_refs)
        return sorted(set(refs))
    
    def _collect_all_evidence_refs(
        self,
        assessment: RegimeAssessment,
        warnings: list[EarlyWarningSignal],
    ) -> list[str]:
        """Collect all evidence references from assessment and warnings."""
        refs = list(assessment.evidence_refs) if hasattr(assessment, 'evidence_refs') else []
        for warning in warnings:
            refs.extend(warning.evidence_refs)
        return sorted(set(refs))
    
    def to_dict(self) -> dict[str, Any]:
        """Return detector metadata."""
        return {
            "version": self._version,
            "history_count": self._history.count,
            "observation_count": self._probability_engine.observation_count,
        }
