# ResearchOS Decision/Risk Boundary v1

## Purpose

This boundary turns a validated research probability into a deterministic,
research-only risk calculation. It does **not** place orders, connect to a
broker, or decide that a trade must be opened.

## Pipeline

```text
ResearchOS
    |
    | validated probability + research provenance
    v
RiskInput (risk.v1)
    |
    | historical payoff statistics + account + explicit policy
    v
calculate_risk()
    |
    v
RiskCalculation (risk.v1)
```

## Contract

Required research input:

- `asset`
- `direction`
- `probability` — probability of the explicitly defined research event
- `account_equity`
- `trade_statistics.average_win`
- `trade_statistics.average_loss`

Optional:

- `risk_per_unit` — monetary loss for one position unit at the defined stop
- `research_id`
- probability method/calibration status

Policy inputs are explicit and versionable:

- `fractional_kelly` (default 0.25)
- `max_risk_fraction` (default 0.01)
- `max_position_fraction` (default 1.0)

## Mathematics

Let `p` be the supplied event probability and `b` be
`average_win / average_loss`.

```text
full_kelly = max(0, p - (1-p)/b)
fractional_kelly = full_kelly * fractional_kelly_policy
final_risk = min(fractional_kelly, max_risk_fraction)
risk_amount = account_equity * final_risk
```

If `risk_per_unit` is available:

```text
position_size = risk_amount / risk_per_unit
```

The result is capped by `max_position_fraction` of account equity.

## Scientific boundary

The risk layer does not reinterpret the research probability. The research
layer must define what the probability means, its horizon, evidence, and
validation/calibration state. A probability value alone is not evidence of
profitability.

The existing portfolio analytics already contains a pure `kelly_fraction`
primitive; this boundary provides the missing cross-block contract and policy
layer rather than creating a second mathematical definition of Kelly.

## Non-responsibilities

- No broker integration.
- No order creation.
- No autonomous trading.
- No modification of ResearchOS evidence or experiment semantics.
- No probability generation.
- No hidden risk limits.
