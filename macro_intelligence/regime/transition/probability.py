"""
ResearchOS Macro Intelligence Layer - Transition Probability Engine

Computes transition probabilities using empirical and prior-based methods.
All computations are deterministic and stateless.
"""

from __future__ import annotations

from typing import Any
from macro_intelligence.regime.classification.taxonomy import MacroRegime
from macro_intelligence.regime.transition.transitions import (
    DEFAULT_TRANSITION_PROBS,
    normalize_transition_probs,
    get_default_transition_probs,
    update_transition_probs,
)


class TransitionProbabilityEngine:
    """
    Computes regime transition probabilities.
    
    Pure, deterministic, stateless engine.
    """
    
    def __init__(self):
        self._prior_probs = get_default_transition_probs()
        self._observation_count = 0
    
    @property
    def prior_probs(self) -> dict[str, dict[str, float]]:
        """Get the current prior probability matrix."""
        return self._prior_probs
    
    @property
    def observation_count(self) -> int:
        """Get the number of observed transitions."""
        return self._observation_count
    
    def get_transition_probability(
        self,
        from_regime: MacroRegime,
        to_regime: MacroRegime,
   ) -> float:
        """
        Get the probability of transitioning from one regime to another.
        
        Args:
            from_regime: Current regime
            to_regime: Target regime
            
        Returns:
            Probability (0.0 to 1.0)
        """
        from_key = from_regime.value
        to_key = to_regime.value
        
        probs = self._prior_probs.get(from_key, {})
        return probs.get(to_key, 0.0)
    
    def get_all_transition_probabilities(
        self,
        from_regime: MacroRegime,
   ) -> dict[str, float]:
        """
        Get all transition probabilities from a given regime.
        
        Args:
            from_regime: Source regime
            
        Returns:
            Dict mapping target regime values to probabilities
        """
        from_key = from_regime.value
        probs = self._prior_probs.get(from_key, {})
        return dict(probs)
    
    def get_next_regime_probabilities(
        self,
        current_regime: MacroRegime,
        exclude_current: bool = True,
   ) -> dict[MacroRegime, float]:
        """
        Get probabilities for next regime, excluding current.
        
        Args:
            current_regime: Current regime
            exclude_current: Whether to exclude the current regime
            
        Returns:
            Dict mapping MacroRegime to probability
        """
        all_probs = self.get_all_transition_probabilities(current_regime)
        
        result = {}
        for regime_str, prob in all_probs.items():
            if exclude_current and regime_str == current_regime.value:
                continue
            result[MacroRegime(regime_str)] = prob
        
        # Re-normalize after exclusion
        total = sum(result.values())
        if total > 0:
            result = {k: v / total for k, v in result.items()}
        
        return result
    
    def get_most_likely_next_regime(
        self,
        current_regime: MacroRegime,
   ) -> tuple[MacroRegime, float]:
        """
        Get the most likely next regime and its probability.
        
        Args:
            current_regime: Current regime
            
        Returns:
            (most_likely_regime, probability)
        """
        probs = self.get_next_regime_probabilities(current_regime, exclude_current=True)
        
        if not probs:
            # All probabilities are for staying in current regime
            return current_regime, 0.0
        
        most_likely = max(probs, key=probs.get)
        return most_likely, probs[most_likely]
    
    def get_transition_risk_score(
        self,
        from_regime: MacroRegime,
   ) -> float:
        """
        Get a risk score for transitioning FROM a regime.
        
        Risk score = 1 - P(stay in current regime)
        
        Args:
            from_regime: Current regime
            
        Returns:
            Risk score (0.0 to 1.0)
        """
        stay_prob = self.get_transition_probability(
            from_regime, from_regime
        )
        return round(1.0 - stay_prob, 4)
    
    def get_stability_score(
        self,
        from_regime: MacroRegime,
   ) -> float:
        """
        Get a stability score for a regime.
        
        Stability score = P(stay in current regime)
        
        Args:
            from_regime: Regime to evaluate
            
        Returns:
            Stability score (0.0 to 1.0)
        """
        return round(self.get_transition_probability(
            from_regime, from_regime
        ), 4)
    
    def update_with_observations(
        self,
        observations: list[tuple[str, str]],
        alpha: float = 0.1,
    ) -> None:
        """
        Update transition probabilities with new observations.
        
        Args:
            observations: List of (from_regime, to_regime) tuples
            alpha: Smoothing factor
        """
        self._prior_probs = update_transition_probs(
            self._prior_probs, observations, alpha
        )
        self._observation_count += len(observations)
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize engine state."""
        return {
            "prior_probs": self._prior_probs,
            "observation_count": self._observation_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransitionProbabilityEngine:
        """Deserialize engine state."""
        engine = cls()
        engine._prior_probs = data.get("prior_probs", get_default_transition_probs())
        engine._observation_count = data.get("observation_count", 0)
        return engine
