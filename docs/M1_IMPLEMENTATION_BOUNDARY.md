# M1 implementation boundary

This change adds only the deterministic M1 event and outcome contract surfaces.

It does not:

- claim a trading edge;
- fit calibration on future observations;
- bypass leakage checks;
- replace the audited MT5 dataset;
- introduce synthetic or mock fallback data.

The next gate is an actual integration run against the local audited MT5 XAUUSD M1 dataset.
