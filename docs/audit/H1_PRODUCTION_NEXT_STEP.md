# H1 Production Evidence Boundary

The real MT5 XAUUSD M1 dataset is validated, but the current D1 production evidence gate produces only 10 SMA20/100 crossover events and therefore remains correctly rejected by the minimum-event gate.

The next production research boundary is deterministic M1 → UTC H1 aggregation. H1 is the event-research timeframe; D1 remains the macro/regime timeframe.

Required sequence:

1. Validate and canonicalize M1.
2. Aggregate to UTC H1 without lookahead.
3. Preserve source/provenance identity.
4. Run Market Memory on H1.
5. Require at least 100 validated events before publication.
6. Apply purged chronological OOS validation.
7. Evaluate probability calibration.
8. Feed calibrated probability into the decision pipeline.

The 100-event gate must not be weakened to manufacture an accepted result.
