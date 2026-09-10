# Phase 5.2 feature-set isolation

The empirical comparison is defined over one identical common observation sample,
identical labels, chronological walk-forward folds, and identical cost settings.

Feature sets:

1. `PRICE_ONLY`
2. `PRICE + DXY`
3. `PRICE + US10Y`
4. `PRICE + VIX`
5. `PRICE + ALL`

`PRICE_ONLY` contains the frozen Phase 5.1 price feature vector. Each macro
variant adds exactly the three derived features for the named macro source.
`PRICE + ALL` adds all nine macro features.

Phase 5.1's frozen `EmpiricalProbabilityEstimator` is not changed. Phase 5.2
uses `MultivariateEmpiricalProbabilityEstimator`, a deterministic fixed-k
nearest-neighbour empirical conditional-frequency estimator, when an explicit
feature set is selected. Training-window min/max normalization is fitted only
on the training slice; ties are resolved by original training-row index and
class order `1 > 0 > -1`.

This comparison is predictive-value research only. It does not establish a
trading edge, profitability, or live-trading suitability.
