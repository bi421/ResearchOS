"""
Phase 5.1 — spread/slippage/commission cost adjustment.

Measures how much realistic execution costs erode the model's directional
accuracy.  Reuses the deterministic cost semantics from
``researchos.quant_engine.execution.ExecutionSimulationLayer`` and
``parse_cost_spec`` (verified existing infrastructure).

Rather than simulating a full equity curve (which requires portfolio
accounting that is out of the forward-prediction scope), this module applies
the same per-fill cost model to each directional prediction: a BUY or SELL
signal incurs a round-trip cost equal to (spread + slippage + 2*commission)
per unit.  If the cost exceeds the bar-to-bar price move captured by the
label's threshold, the "profit" (directional correctness in pips) may become
negative, reducing net directional accuracy.

Guarantees:
    * Deterministic.
    * Composes existing ``parse_cost_spec`` / ``ExecutionSimulationLayer`` cost
      semantics rather than duplicating them.
    * Never makes a live-trading claim; it is a research cost model only.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from researchos.quant_engine.execution import parse_cost_spec

from .contracts import CostResult


def spread_points_per_bar(
    close: Sequence[float],
    spread_cost_spec: str,
    slippage_cost_spec: str,
    commission_cost_spec: str,
) -> Tuple[float, float, float]:
    """Return (spread$, slippage$, commission$) applied to a single bar.

    Costs are expressed in price units (dollars per unit).  ``pct`` specs are
    converted to price units using the last close as reference.
    """
    if not close:
        return 0.0, 0.0, 0.0
    ref = close[-1]
    sk, sv = parse_cost_spec(spread_cost_spec)
    hk, hv = parse_cost_spec(slippage_cost_spec)
    ck, cv = parse_cost_spec(commission_cost_spec)
    spread = sk == "pct" and (ref * sv) or sv
    slip = hk == "pct" and (ref * hv) or hv
    comm = ck == "pct" and (ref * cv) or cv
    return spread, slip, comm


def _cost_overwhelms(
    predicted: int,
    actual: int,
    threshold_pip: float,
    round_trip_cost: float,
) -> Tuple[bool, float]:
    """Return (cost_killed_prediction, net_gain_in_pips).

    For a ternary prediction, the "profit" in price units for a correct
    directional call is approximately the threshold (the minimal move required
    to be up/down).  Net gain = gross_pip - round_trip_cost.
    """
    if int(predicted) != int(actual):
        return False, 0.0  # already wrong; cost does not change correctness
    gross = threshold_pip
    return (gross - round_trip_cost) < 0.0, gross - round_trip_cost


def apply_costs(
    predictions: Sequence[int],
    actuals: Sequence[float],
    close: Sequence[float],
    threshold: float,
    spread_spec: str = "fixed:0.0",
    slippage_spec: str = "fixed:0.0",
    commission_spec: str = "fixed:0.0",
    cost_applied: bool = True,
) -> CostResult:
    """Compute gross and net directional accuracy after costs.

    Args:
        predictions: Model ternary predictions aligned with ``actuals``.
        actuals: True ternary labels.
        close: Close prices (for pct-spec reference).
        threshold: The label threshold (price move defining up/down).
        spread_spec / slippage_spec / commission_spec: cost specs.
        cost_applied: Whether to apply the cost model (validation flag).
    """
    spread, slip, comm = spread_points_per_bar(close, spread_spec, slippage_spec, commission_spec)
    round_trip = spread + slip + 2.0 * comm

    gross_correct = sum(1 for p, a in zip(predictions, actuals) if int(p) == int(a))
    gross_acc = gross_correct / len(actuals) if actuals else 0.0

    up = [(p, a) for p, a in zip(predictions, actuals) if int(a) == 1]
    down = [(p, a) for p, a in zip(predictions, actuals) if int(a) == -1]

    def _acc(pairs: List[Tuple[int, float]]) -> float:
        if not pairs:
            return 0.0
        correct = 0
        for p, a in pairs:
            if cost_applied and round_trip > 0:
                killed, _ = _cost_overwhelms(int(p), int(a), threshold, round_trip)
                if killed:
                    continue
            if int(p) == int(a):
                correct += 1
        # A cost-killed correct prediction is subtracted only if it was
        # otherwise correct; so net-correct = gross-correct - killed.
        return correct / len(pairs)

    net_up = _acc(up)
    net_down = _acc(down)

    # Overall net accuracy: correct minus cost-killed ones.
    killed = 0
    if cost_applied and round_trip > 0:
        for p, a in zip(predictions, actuals):
            if int(p) == int(a):
                is_killed, _ = _cost_overwhelms(int(p), int(a), threshold, round_trip)
                if is_killed:
                    killed += 1
    net_all = (gross_correct - killed) / len(actuals) if actuals else 0.0

    return CostResult(
        cost_model=f"{spread_spec};{slippage_spec};{commission_spec}",
        spread_cost_per_bar=spread,
        slippage_cost_per_bar=slip,
        commission_cost_per_bar=comm,
        gross_accuracy=gross_acc,
        net_accuracy_up=net_up,
        net_accuracy_down=net_down,
        net_accuracy_all=net_all,
        cost_applied=cost_applied,
    )


__all__ = [
    "apply_costs",
    "spread_points_per_bar",
    "_cost_overwhelms",
]
