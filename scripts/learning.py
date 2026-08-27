"""
ResearchOS Learning Layer

Research-only learning and probability calibration.

Responsibilities:
- Learn from score/outcome observations
- Maintain Beta-Bernoulli posterior
- Convert evidence scores to probabilities
- Calibrate probabilities using isotonic or Platt scaling
- Report calibration metrics
- Persist and restore learner state

No broker integration.
No autonomous trading.
No ML model training beyond probability calibration.
"""

from __future__ import annotations

import json
import math
from typing import Any

from researchos.quant_engine.probability.statistics import (
    probability_calibration,
)


class BayesianLearner:
    """
    Deterministic Bayesian learning layer.

    The learner maintains a Beta posterior over binary outcomes and
    optionally calibrates evidence scores into probabilities.
    """

    def __init__(
        self,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
    ) -> None:
        if prior_alpha <= 0:
            raise ValueError("prior_alpha must be positive")
        if prior_beta <= 0:
            raise ValueError("prior_beta must be positive")

        self.alpha = float(prior_alpha)
        self.beta = float(prior_beta)

        self._calibration_model: Any = None
        self._calibration_type: str | None = None
        self._is_calibrated = False

        self._history: list[tuple[float, int]] = []

    # ------------------------------------------------------------------
    # Core learning
    # ------------------------------------------------------------------

    def learn(
        self,
        scores: list[float],
        outcomes: list[int],
    ) -> dict[str, float]:
        """
        Learn from evidence scores and binary outcomes.

        scores:
            Evidence scores associated with observations.

        outcomes:
            Binary outcomes:
                1 = UP / success
                0 = DOWN / failure
        """
        if len(scores) != len(outcomes):
            raise ValueError("scores and outcomes must have equal length")

        if not scores:
            raise ValueError("scores and outcomes must be non-empty")

        if any(o not in (0, 1) for o in outcomes):
            raise ValueError("outcomes must contain only 0 or 1")

        # Store observations.
        self._history.extend((float(score), int(outcome)) for score, outcome in zip(scores, outcomes))

        # Update Bayesian posterior.
        wins = sum(outcomes)
        losses = len(outcomes) - wins

        self.alpha += wins
        self.beta += losses

        # Calibrate if enough observations are available.
        if len(scores) >= 10:
            self.calibrate(
                scores,
                outcomes,
                method="isotonic",
            )

        return {
            "samples": float(len(outcomes)),
            "wins": float(wins),
            "losses": float(losses),
            "posterior_mean": self.get_posterior_winrate(),
        }

    # ------------------------------------------------------------------
    # Bayesian update
    # ------------------------------------------------------------------

    def update(
        self,
        outcomes: list[float],
    ) -> dict[str, float]:
        """
        Update Beta posterior from signed outcomes.

        Positive values are treated as wins.
        Zero or negative values are treated as losses.
        """
        if not outcomes:
            raise ValueError("outcomes must be non-empty")

        wins = sum(1 for outcome in outcomes if outcome > 0)
        losses = len(outcomes) - wins

        self.alpha += wins
        self.beta += losses

        posterior_mean = self.get_posterior_winrate()

        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "posterior_mean": posterior_mean,
            "wins": float(wins),
            "losses": float(losses),
            "total_trades": float(len(outcomes)),
        }

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(
        self,
        evidence_score: float,
    ) -> float:
        """
        Convert evidence score into probability.

        If calibrated, use the fitted calibration model.
        Otherwise use a deterministic logistic mapping.
        """
        score = float(evidence_score)

        if self._is_calibrated and self._calibration_model is not None:
            if self._calibration_type == "isotonic":
                probability = float(self._calibration_model.predict([score])[0])

            elif self._calibration_type == "platt":
                slope, intercept = self._calibration_model
                probability = self._sigmoid(slope * score + intercept)

            else:
                probability = self._sigmoid(2.5 * score)

        else:
            # Explicit baseline mapping.
            probability = self._sigmoid(2.5 * score)

        return self._clip_probability(probability)

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def calibrate(
        self,
        scores: list[float],
        outcomes: list[float],
        method: str = "isotonic",
    ) -> None:
        """
        Fit a probability calibration model.

        Supported methods:
        - isotonic
        - platt
        """
        if len(scores) != len(outcomes):
            raise ValueError("scores and outcomes must have equal length")

        if len(scores) < 10:
            raise ValueError("Need at least 10 samples for calibration.")

        y = [1 if outcome > 0 else 0 for outcome in outcomes]

        if any(value not in (0, 1) for value in y):
            raise ValueError("outcomes must be binary")

        method = method.lower().strip()

        if method == "isotonic":
            from sklearn.isotonic import IsotonicRegression

            model = IsotonicRegression(
                y_min=0.0,
                y_max=1.0,
                increasing=True,
                out_of_bounds="clip",
            )

            model.fit(
                [float(score) for score in scores],
                y,
            )

            self._calibration_model = model
            self._calibration_type = "isotonic"

        elif method == "platt":
            from sklearn.linear_model import LogisticRegression

            model = LogisticRegression(
                C=1e10,
                solver="lbfgs",
            )

            X = [[float(score)] for score in scores]

            model.fit(X, y)

            slope = float(model.coef_[0][0])
            intercept = float(model.intercept_[0])

            self._calibration_model = (
                slope,
                intercept,
            )

            self._calibration_type = "platt"

        else:
            raise ValueError("method must be 'isotonic' or 'platt'")

        self._is_calibrated = True

    # ------------------------------------------------------------------
    # Calibration metrics
    # ------------------------------------------------------------------

    def calibration_metrics(
        self,
        scores: list[float],
        outcomes: list[int],
    ) -> dict[str, Any]:
        """
        Evaluate probability calibration.

        Returns:
        - Brier score
        - classification accuracy
        - mean predicted probability
        - observed frequency
        - calibration table
        """
        if len(scores) != len(outcomes):
            raise ValueError("scores and outcomes must have equal length")

        if not scores:
            raise ValueError("scores and outcomes must be non-empty")

        if any(o not in (0, 1) for o in outcomes):
            raise ValueError("outcomes must contain only 0 or 1")

        predictions = [self.predict(score) for score in scores]

        brier_score = sum((prediction - outcome) ** 2 for prediction, outcome in zip(predictions, outcomes)) / len(outcomes)

        accuracy = sum((prediction >= 0.5) == bool(outcome) for prediction, outcome in zip(predictions, outcomes)) / len(outcomes)

        calibration = probability_calibration(
            predictions,
            outcomes,
            num_bins=10,
        )

        return {
            "brier_score": float(brier_score),
            "accuracy": float(accuracy),
            "mean_predicted_probability": (sum(predictions) / len(predictions)),
            "observed_frequency": (sum(outcomes) / len(outcomes)),
            "samples": len(outcomes),
            "calibration": calibration,
        }

    # ------------------------------------------------------------------
    # Bayesian state
    # ------------------------------------------------------------------

    def get_posterior_winrate(self) -> float:
        total = self.alpha + self.beta

        if total <= 0:
            return 0.0

        return self.alpha / total

    def get_credible_interval(
        self,
        confidence: float = 0.95,
    ) -> tuple[float, float]:
        """
        Return Bayesian credible interval for posterior win rate.
        """
        if not 0.0 < confidence < 1.0:
            raise ValueError("confidence must be between 0 and 1")

        from scipy.stats import beta

        lower = float(
            beta.ppf(
                (1.0 - confidence) / 2.0,
                self.alpha,
                self.beta,
            )
        )

        upper = float(
            beta.ppf(
                (1.0 + confidence) / 2.0,
                self.alpha,
                self.beta,
            )
        )

        return lower, upper

    # ------------------------------------------------------------------
    # State / history
    # ------------------------------------------------------------------

    def get_history(self) -> list[tuple[float, int]]:
        return list(self._history)

    @property
    def is_calibrated(self) -> bool:
        return self._is_calibrated

    @property
    def calibration_type(self) -> str | None:
        return self._calibration_type

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(
        self,
        filepath: str,
    ) -> None:
        """
        Save learner state as JSON.
        """
        data: dict[str, Any] = {
            "version": "1.0",
            "alpha": self.alpha,
            "beta": self.beta,
            "is_calibrated": self._is_calibrated,
            "calibration_type": self._calibration_type,
            "history": [[score, outcome] for score, outcome in self._history],
        }

        if self._is_calibrated and self._calibration_type == "platt" and self._calibration_model is not None:
            slope, intercept = self._calibration_model

            data["calibration_model"] = {
                "slope": slope,
                "intercept": intercept,
            }

        with open(
            filepath,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                sort_keys=True,
            )

    def load(
        self,
        filepath: str,
    ) -> None:
        """
        Restore learner state from JSON.
        """
        with open(
            filepath,
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        self.alpha = float(data["alpha"])
        self.beta = float(data["beta"])

        self._history = [(float(score), int(outcome)) for score, outcome in data.get("history", [])]

        self._is_calibrated = bool(data.get("is_calibrated", False))

        self._calibration_type = data.get("calibration_type")

        self._calibration_model = None

        if not self._is_calibrated:
            return

        calibration_type = self._calibration_type

        if calibration_type == "platt":
            model = data.get("calibration_model")

            if model is not None:
                self._calibration_model = (
                    float(model["slope"]),
                    float(model["intercept"]),
                )

        elif calibration_type == "isotonic":
            if len(self._history) >= 10:
                scores = [score for score, _ in self._history]

                outcomes = [outcome for _, outcome in self._history]

                self.calibrate(
                    scores,
                    outcomes,
                    method="isotonic",
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sigmoid(value: float) -> float:
        """
        Numerically stable logistic function.
        """
        if value >= 0:
            z = math.exp(-value)
            return 1.0 / (1.0 + z)

        z = math.exp(value)
        return z / (1.0 + z)

    @staticmethod
    def _clip_probability(
        probability: float,
    ) -> float:
        return max(
            0.001,
            min(
                0.999,
                float(probability),
            ),
        )


__all__ = [
    "BayesianLearner",
]


if __name__ == "__main__":
    learner = BayesianLearner()

    scores = [
        -0.2,
        -0.1,
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
    ]

    outcomes = [
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
    ]

    result = learner.learn(
        scores,
        outcomes,
    )

    print("Learning:", result)
    print("P(0.5):", learner.predict(0.5))
    print(
        "Metrics:",
        learner.calibration_metrics(
            scores,
            outcomes,
        ),
    )
