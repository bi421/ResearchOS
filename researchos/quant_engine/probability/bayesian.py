"""
Probability & Statistics Engine — Bayesian inference, Markov chains, HMM.

Deterministic implementations. All random processes use explicit seeds.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class BetaPosterior:
    """Posterior of a Beta-Bernoulli / Beta-Binomial model."""

    alpha: float
    beta: float
    prior_alpha: float = 1.0
    prior_beta: float = 1.0

    @property
    def posterior_mean(self) -> float:
        return self.alpha / (self.alpha + self.beta) if (self.alpha + self.beta) > 0 else 0.0

    def update(self, successes: int, failures: int) -> "BetaPosterior":
        return BetaPosterior(
            alpha=self.alpha + successes,
            beta=self.beta + failures,
            prior_alpha=self.prior_alpha,
            prior_beta=self.prior_beta,
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "posterior_mean": self.posterior_mean,
        }


@dataclass(frozen=True)
class MarkovChain:
    """A discrete-time, finite-state Markov chain."""

    transition_matrix: List[List[float]] = field(default_factory=list)
    states: List[str] = field(default_factory=list)

    @property
    def num_states(self) -> int:
        return len(self.states)

    def transition_probability(self, from_state: int, to_state: int) -> float:
        return self.transition_matrix[from_state][to_state]

    def simulate(
        self,
        num_steps: int = 100,
        start_state: int = 0,
        seed: int = 42,
    ) -> List[int]:
        rng = random.Random(seed)
        path = [start_state]
        state = start_state
        for _ in range(num_steps - 1):
            probs = self.transition_matrix[state]
            r = rng.random()
            cumulative = 0.0
            next_state = state
            for i, p in enumerate(probs):
                cumulative += p
                if r <= cumulative:
                    next_state = i
                    break
            path.append(next_state)
            state = next_state
        return path

    def to_dict(self) -> Dict[str, object]:
        return {
            "states": self.states,
            "transition_matrix": self.transition_matrix,
        }


def estimate_markov_chain(
    observations: Sequence[int],
    num_states: int,
) -> MarkovChain:
    """Estimate a Markov chain transition matrix from a state sequence."""
    if len(observations) < 2:
        raise ValueError("need at least 2 observations")
    counts = [[0.0] * num_states for _ in range(num_states)]
    for i in range(len(observations) - 1):
        f = observations[i]
        t = observations[i + 1]
        if f < num_states and t < num_states:
            counts[f][t] += 1.0
    matrix = []
    for i in range(num_states):
        row_sum = sum(counts[i])
        if row_sum == 0:
            matrix.append([1.0 / num_states] * num_states)
        else:
            matrix.append([c / row_sum for c in counts[i]])
    return MarkovChain(
        transition_matrix=matrix,
        states=[str(i) for i in range(num_states)],
    )


class HiddenMarkovModel:
    """
    A simple categorical Hidden Markov Model with forward/backward inference.

    Research-only. Deterministic given fixed data.
    """

    def __init__(
        self,
        num_states: int,
        num_observations: int,
        seed: int = 42,
    ) -> None:
        rng = random.Random(seed)
        self.num_states = num_states
        self.num_observations = num_observations
        self.start_prob = [1.0 / num_states] * num_states
        self.transition = [
            [1.0 / num_states] * num_states for _ in range(num_states)
        ]
        self.emission = [
            [1.0 / num_observations] * num_observations for _ in range(num_states)
        ]

    def forward(self, observations: Sequence[int]) -> List[List[float]]:
        """Forward algorithm — alpha probabilities."""
        T = len(observations)
        alpha = [[0.0] * self.num_states for _ in range(T)]
        for s in range(self.num_states):
            alpha[0][s] = self.start_prob[s] * self.emission[s][observations[0]]
        for t in range(1, T):
            for s in range(self.num_states):
                alpha[t][s] = sum(
                    alpha[t - 1][j] * self.transition[j][s]
                    for j in range(self.num_states)
                ) * self.emission[s][observations[t]]
        return alpha

    def log_likelihood(self, observations: Sequence[int]) -> float:
        alpha = self.forward(observations)
        total = sum(alpha[-1])
        return math.log(total) if total > 0 else -float("inf")

    def viterbi(self, observations: Sequence[int]) -> List[int]:
        """Viterbi decoding — most likely hidden state sequence."""
        T = len(observations)
        if T == 0:
            return []
        v = [[0.0] * self.num_states for _ in range(T)]
        back = [[0] * self.num_states for _ in range(T)]
        for s in range(self.num_states):
            v[0][s] = math.log(self.start_prob[s] + 1e-12) + math.log(self.emission[s][observations[0]] + 1e-12)
        for t in range(1, T):
            for s in range(self.num_states):
                best = float("-inf")
                best_j = 0
                for j in range(self.num_states):
                    cand = v[t - 1][j] + math.log(self.transition[j][s] + 1e-12)
                    if cand > best:
                        best = cand
                        best_j = j
                v[t][s] = best + math.log(self.emission[s][observations[t]] + 1e-12)
                back[t][s] = best_j
        last = max(range(self.num_states), key=lambda s: v[T - 1][s])
        path = [last]
        for t in range(T - 1, 0, -1):
            path.insert(0, back[t][path[0]])
        return path

