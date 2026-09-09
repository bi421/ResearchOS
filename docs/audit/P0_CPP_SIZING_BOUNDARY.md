# P0 — C++ strategy sizing authority boundary

## Finding

`StrategySignal::quantity` can currently override `TradeConfig::sizing` inside `cpp_quant_engine/src/strategy/strategy_kernel.cpp`.

The signal contract says `quantity == 0.0` means position sizing comes from `TradeConfig`, and `SignalAction::Open` is documented as sizing from `TradeConfig`.

Current execution logic effectively does:

```cpp
const double qty = sig.quantity > 0.0 ? sig.quantity : size_quantity(ctx, sig, plan);
```

This means a signal can bypass a configured `FixedLot` or risk-based sizing policy.

## Required invariant

`TradeConfig` is authoritative for entry sizing:

- `FixedLot`: quantity MUST equal `TradeConfig.fixed_lot`.
- `RiskPercent`: quantity MUST be derived from configured/explicit risk amount and a positive stop distance.
- `StrategySignal.risk_amount` may override the risk amount, but MUST NOT directly set quantity.
- Risk-based sizing without a valid stop distance MUST reject the entry rather than silently falling back to `default_quantity`.
- Signal execution timing MUST remain `bar i -> bar i+1 open`.

## Regression cases required

1. Signal quantity cannot override FixedLot.
2. Signal quantity cannot override RiskPercent sizing.
3. Signal risk amount override still works.
4. RiskPercent without stop rejects the entry.
5. Existing next-bar-open execution behavior remains unchanged.

## Important

Do not use a workflow that edits test expectations automatically. The kernel implementation must enforce the boundary.

PR #6 contained a self-modifying remediation workflow; it is intentionally excluded from this audit remediation.
