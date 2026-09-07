# P0 remediation status

The audit branch enforces the following quantitative correctness boundaries:

- Phase 5.1 rejects invalid temporal configuration before dataset construction.
- Phase 5.1 uses purge-aware walk-forward validation and non-overlapping significance observations.
- C++ strategy sizing ignores caller-supplied quantity for risk-based sizing.
- C++ risk-based sizing rejects trades without a positive stop distance.
- C++ replay fills signals at the next bar open.

CI remains the authoritative verification gate; this document does not certify a green build by itself.
