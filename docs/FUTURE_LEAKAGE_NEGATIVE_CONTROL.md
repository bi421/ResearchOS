# XAUUSD M1 Future-Leakage Negative Control

This control deliberately injects the first validation event ID into the first
fold's training-event membership. The resulting artifact is intentionally
invalid and must be rejected by the independent source-to-result auditor.

## Scientific boundary

This is a structural negative control. A successful rejection demonstrates
that the audit path detects this specific future-data membership violation. It
does not establish predictive edge, profitability, calibration, or trading
validity.

## Reproduction

```text
python scripts/run_xauusd_m1_future_leakage_negative_control.py <result.json> --output artifacts/xauusd_m1_future_leakage_negative_control.json
python scripts/audit_xauusd_m1_source_to_result.py <source.json> artifacts/xauusd_m1_future_leakage_negative_control.json
```

The second command is expected to exit non-zero with a training-membership
failure.
