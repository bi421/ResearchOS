"""Dependence-aware inference primitives for market-event outcomes."""

from __future__ import annotations

import math


_PARK_MILLER_MODULUS = 2_147_483_647
_PARK_MILLER_MULTIPLIER = 48_271


def block_bootstrap_mean_ci(
    values: list[float],
    *,
    block_size: int,
    num_resamples: int = 1000,
    seed: int = 42,
    confidence_level: float = 0.95,
) -> tuple[float, float] | None:
    """Return a deterministic moving-block-bootstrap CI for the mean.

    Contiguous blocks preserve short-range serial dependence. The block-size
    assumption is deliberately explicit so it can be recorded in evidence
    provenance. This method does not claim independence and is not a substitute
    for validating the dependence structure itself.
    """
    if len(values) < 2:
        return None
    if not 1 <= block_size <= len(values):
        raise ValueError("block_size must be between 1 and len(values)")
    if num_resamples < 1:
        raise ValueError("num_resamples must be >= 1")
    if not isinstance(seed, int):
        raise TypeError("seed must be an int")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be strictly between 0 and 1")
    if any(not math.isfinite(float(value)) for value in values):
        raise ValueError("values must be finite")

    n = len(values)
    starts = n - block_size + 1
    state = seed % _PARK_MILLER_MODULUS or 1

    def next_start() -> int:
        nonlocal state
        state = (_PARK_MILLER_MULTIPLIER * state) % _PARK_MILLER_MODULUS
        return state % starts

    means: list[float] = []
    for _ in range(num_resamples):
        sample: list[float] = []
        while len(sample) < n:
            start = next_start()
            sample.extend(values[start : start + block_size])
        sample = sample[:n]
        means.append(sum(sample) / n)

    means.sort()
    alpha = 1.0 - confidence_level
    return (_percentile(means, alpha / 2.0), _percentile(means, 1.0 - alpha / 2.0))


def _percentile(sorted_values: list[float], probability: float) -> float:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] + weight * (sorted_values[upper] - sorted_values[lower])


__all__ = ["block_bootstrap_mean_ci"]
