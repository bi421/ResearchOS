"""
OutcomeAnalysis — deterministic analysis of historical scenario outcomes.

For matched scenarios, computes:
    - Number of historical examples
    - Positive/negative outcome counts
    - Average price movement
    - Volatility response
    - Confidence score

All calculations are deterministic and based solely on the provided data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from researchos.memory.matcher import MatchResult
from researchos.memory.models import HistoricalScenario


@dataclass
class OutcomeAnalysisResult:
    """
    Computed outcome analysis from matched historical scenarios.

    Attributes:
        total_examples: Number of historical scenarios matched
        positive_outcomes: Count of scenarios with positive price outcome
        negative_outcomes: Count of scenarios with negative price outcome
        neutral_outcomes: Count of scenarios with neutral outcome
        positive_ratio: Ratio of positive outcomes (0.0-1.0)
        avg_price_outcome: Average price outcome across all matches
        avg_volatility_outcome: Average volatility outcome
        avg_max_favorable: Average maximum favorable movement
        avg_max_adverse: Average maximum adverse movement
        confidence_score: Statistical confidence in the analysis (0.0-1.0)
        calculation_method: Description of how results were computed
        matched_scenarios: List of scenario IDs used in analysis
    """

    total_examples: int = 0
    positive_outcomes: int = 0
    negative_outcomes: int = 0
    neutral_outcomes: int = 0
    positive_ratio: float = 0.0
    avg_price_outcome: float = 0.0
    avg_volatility_outcome: float = 0.0
    avg_max_favorable: float = 0.0
    avg_max_adverse: float = 0.0
    confidence_score: float = 0.0
    calculation_method: str = "HistoricalOutcomeAnalysis"
    matched_scenarios: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_examples": self.total_examples,
            "positive_outcomes": self.positive_outcomes,
            "negative_outcomes": self.negative_outcomes,
            "neutral_outcomes": self.neutral_outcomes,
            "positive_ratio": self.positive_ratio,
            "avg_price_outcome": self.avg_price_outcome,
            "avg_volatility_outcome": self.avg_volatility_outcome,
            "avg_max_favorable": self.avg_max_favorable,
            "avg_max_adverse": self.avg_max_adverse,
            "confidence_score": self.confidence_score,
            "calculation_method": self.calculation_method,
            "matched_scenarios": self.matched_scenarios,
        }


class OutcomeAnalysis:
    """
    Deterministic analysis of historical scenario outcomes.

    Analyzes matched scenarios to compute aggregate statistics
    about what happened after similar market conditions.

    Args:
        min_examples: Minimum number of examples required for confidence.
    """

    def __init__(self, min_examples: int = 3):
        self.min_examples = min_examples

    def analyze(
        self,
        match_results: list[MatchResult],
        scenarios: dict[str, HistoricalScenario],
    ) -> OutcomeAnalysisResult:
        """
        Analyze outcomes from matched scenarios.

        Args:
            match_results: List of matched scenario results.
            scenarios: Dict of scenario_id -> HistoricalScenario
                       for resolving outcome data.

        Returns:
            OutcomeAnalysisResult with computed statistics.
        """
        result = OutcomeAnalysisResult()

        positive = 0
        negative = 0
        neutral = 0
        price_sum = 0.0
        vol_sum = 0.0
        favorable_sum = 0.0
        adverse_sum = 0.0
        count = 0

        for match in match_results:
            scenario = scenarios.get(match.scenario_id)
            if not scenario:
                continue

            result.matched_scenarios.append(scenario.id)
            count += 1

            # Classify outcome direction
            if scenario.price_outcome > 0.0:
                positive += 1
            elif scenario.price_outcome < 0.0:
                negative += 1
            else:
                neutral += 1

            price_sum += scenario.price_outcome
            vol_sum += scenario.volatility_outcome
            favorable_sum += scenario.max_favorable_movement
            adverse_sum += scenario.max_adverse_movement

        result.total_examples = count
        result.positive_outcomes = positive
        result.negative_outcomes = negative
        result.neutral_outcomes = neutral

        if count > 0:
            result.positive_ratio = positive / count
            result.avg_price_outcome = price_sum / count
            result.avg_volatility_outcome = vol_sum / count
            result.avg_max_favorable = favorable_sum / count
            result.avg_max_adverse = adverse_sum / count

        # Compute confidence score
        # Based on: number of examples, diversity of outcomes, score strength
        result.confidence_score = self._compute_confidence(result)

        return result

    def _compute_confidence(self, result: OutcomeAnalysisResult) -> float:
        """
        Compute confidence score for the analysis.

        Factors:
            1. Sample size: More examples = higher confidence
            2. Outcome clarity: Clear positive/negative split = higher confidence
            3. Effect size: Larger magnitude movements = higher confidence

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if result.total_examples == 0:
            return 0.0

        # Sample size factor (logarithmic scaling)
        sample_factor = min(1.0, result.total_examples / self.min_examples)

        # Outcome clarity factor
        # Higher when one outcome dominates
        max_outcome = max(result.positive_outcomes, result.negative_outcomes, result.neutral_outcomes)
        clarity_factor = max_outcome / result.total_examples if result.total_examples > 0 else 0.0

        # Effect size factor
        abs_price = abs(result.avg_price_outcome)
        effect_factor = min(1.0, abs_price / 5.0)  # 5% = full effect

        # Combined score (weighted average)
        confidence = 0.4 * sample_factor + 0.3 * clarity_factor + 0.3 * effect_factor

        return max(0.0, min(1.0, confidence))
