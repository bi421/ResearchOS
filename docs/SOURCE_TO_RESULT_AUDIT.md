# XAUUSD M1 Source-to-Result Audit

## Purpose

The walk-forward producer is not trusted as its own verifier. The audit stage accepts the original event/outcome artifact and the derived walk-forward result as separate inputs.

## Required proof chain

1. Recompute the source artifact SHA-256 from bytes.
2. Reconstruct complete XAUUSD M1 events from `events_data`.
3. Recompute chronological training and validation membership from the declared split.
4. Recompute the realized-end embargo (`realized_end < validation_start`).
5. Verify every emitted prediction maps to exactly one source validation event.
6. Verify source timestamp, direction, and boolean-derived label are unchanged.
7. Verify training IDs, counts, fold boundaries, and embargo counts.
8. Recompute aggregate scores from source-linked labels and emitted probabilities.
9. Return `PASS` only when every invariant holds; otherwise return `FAIL`.

The auditor deliberately does not import the walk-forward producer. A passing result therefore means the derived artifact is internally consistent with the supplied source artifact and declared research contract; it does not by itself establish predictive edge, profitability, calibrated live probabilities, or trading validity.

## CLI

```text
python scripts/audit_xauusd_m1_source_to_result.py SOURCE_EVENTS.json WALKFORWARD_RESULT.json
```

Exit code `0` means PASS. Exit code `1` means FAIL.
