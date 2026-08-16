"""
Phase 5.1 — self-validation.

Aggregates the experiment's internal validity flags into a single outcome:

    * ``PASS``      — all flags satisfied AND the model beats the baseline
                      out-of-sample after costs with the configured criteria.
    * ``FAIL``      — all flags satisfied but the model does NOT beat the
                      baseline (or loses after costs / is not significant).
    * ``UNCERTAIN`` — data/evaluation insufficient to conclude either way
                      (e.g. insufficient validation samples).
    * ``BLOCKED``   — real XAUUSD data is required but not supplied.  This is
                      NEVER an interpretation of model success or failure.

Guarantees:
    * Deterministic: same inputs -> same outcome.
    * BLOCKED is a data-availability state, not a model verdict.
"""

from __future__ import annotations


from .contracts import (
    Outcome,
    ValidationFlags,
)


def aggregate_outcome(
    *,
    data_valid: bool,
    leakage_check: bool,
    out_of_sample: bool,
    cost_adjusted: bool,
    reproducible: bool,
    model_accuracy: float,
    baseline_accuracy: float,
    net_accuracy_all: float,
    significant: bool,
    min_sample_count: int,
    validation_sample_count: int,
    brier_model: float = 0.0,
    brier_baseline: float = 0.0,
) -> ValidationFlags:
    """Aggregate flags + performance into a single outcome.

    Decision rule (smallest scientifically-defensible):
        * If NOT data_valid or NOT reproducible                    -> BLOCKED.
        * If NOT leakage_check or NOT out_of_sample or
          NOT cost_adjusted                                        -> FAIL (invalid eval).
        * If validation_sample_count < min_sample_count            -> UNCERTAIN.
        * Model beats baseline out-of-sample AND net-of-cost
          accuracy remains >= baseline accuracy AND significant    -> PASS.
        * Otherwise                                                -> FAIL.
    """
    reasons: list[str] = []

    if not data_valid or not reproducible:
        out = Outcome.BLOCKED
        reasons.append("Real dataset/data unavailable or not reproducible")
    elif not (leakage_check and out_of_sample and cost_adjusted):
        out = Outcome.FAIL
        reasons.append("Evaluation did not meet leakage/out-of-sample/cost conditions")
    elif validation_sample_count < min_sample_count:
        out = Outcome.UNCERTAIN
        reasons.append(f"Too few validation samples ({validation_sample_count})")
    else:
        # Determine predictive value.
        model_wins_gross = model_accuracy > baseline_accuracy
        model_wins_net = net_accuracy_all >= baseline_accuracy
        if model_wins_gross and model_wins_net and significant:
            out = Outcome.PASS
            reasons.append("Model beats baseline out-of-sample, net-of-cost, significant")
        else:
            out = Outcome.FAIL
            reasons.append("Model does not demonstrate out-of-sample predictive value")

    return ValidationFlags(
        data_valid=data_valid,
        leakage_check=leakage_check,
        out_of_sample=out_of_sample,
        cost_adjusted=cost_adjusted,
        reproducible=reproducible,
        outcome=out,
        reasons=tuple(reasons),
    )


__all__ = ["aggregate_outcome"]
