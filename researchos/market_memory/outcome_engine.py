"""
Outcome Engine — deterministic forward outcome calculation for market events.

For each event, computes:
  - Forward absolute and percentage returns at available horizons
  - Direction of movement
  - Maximum favorable excursion (MFE)
  - Maximum adverse excursion (MAE)
  - Hit/miss for predefined thresholds

All calculations are timestamp-aware and prevent future information leakage.
"""

from __future__ import annotations

import polars as pl

from researchos.market_memory.event_schema import (
    EventOutcome,
    MarketEvent,
)

# =============================================================================
# Outcome Calculation
# =============================================================================


def compute_forward_outcomes(
    events: list[MarketEvent],
    price_df: pl.DataFrame,
    horizons: list[int] | None = None,
    threshold: float = 0.0,
) -> list[MarketEvent]:
    """
    Compute forward outcomes for a list of market events.

    Args:
        events: List of MarketEvent objects
        price_df: DataFrame with columns [timestamp, open, high, low, close]
                  Must be sorted by timestamp
        horizons: List of forward horizons in days (default: [1, 2, 3, 5, 10, 20])
        threshold: Threshold for hit/miss classification (default: 0.0)

    Returns:
        Updated list of MarketEvent objects with outcome field populated
    """
    if horizons is None:
        horizons = [1, 2, 3, 5, 10, 20]

    if len(price_df) == 0:
        return events

    timestamps = price_df["timestamp"].to_list()
    closes = price_df["close"].to_list()
    highs = price_df["high"].to_list()
    lows = price_df["low"].to_list()

    # Build lookup: timestamp -> index
    ts_to_idx = {ts: i for i, ts in enumerate(timestamps)}

    updated_events = []
    for event in events:
        event_ts = event.timestamp
        event_close = event.event_price

        # Find the index of the event timestamp
        if event_ts not in ts_to_idx:
            # Event timestamp not found in price data; skip outcome computation
            updated_events.append(event)
            continue

        idx = ts_to_idx[event_ts]

        # Compute outcomes for each horizon
        returns = {}
        directions = {}
        mfe = {}
        mae = {}
        hits = {}

        for h in horizons:
            future_idx = idx + h
            if future_idx >= len(price_df):
                returns[f"return_{h}d"] = None
                directions[f"direction_{h}d"] = None
                mfe[f"mfe_{h}d"] = None
                mae[f"mae_{h}d"] = None
                hits[f"hit_{h}d"] = None
                continue

            future_close = closes[future_idx]
            future_high = highs[future_idx]
            future_low = lows[future_idx]

            # Forward return (from event close to future close)
            ret = (future_close - event_close) / event_close if event_close != 0 else 0.0
            returns[f"return_{h}d"] = ret

            # Direction
            if ret > 0:
                directions[f"direction_{h}d"] = "up"
            elif ret < 0:
                directions[f"direction_{h}d"] = "down"
            else:
                directions[f"direction_{h}d"] = "flat"

            # MFE/MAE (from event close to future high/low)
            mfe_val = (future_high - event_close) / event_close if event_close != 0 else 0.0
            mae_val = (future_low - event_close) / event_close if event_close != 0 else 0.0
            mfe[f"mfe_{h}d"] = mfe_val
            mae[f"mae_{h}d"] = mae_val

            # Hit/miss
            hits[f"hit_{h}d"] = ret > threshold

        # Create outcome
        outcome = EventOutcome(
            event_id=event.event_id,
            asset=event.asset,
            timeframe=event.timeframe,
            event_timestamp=event.timestamp,
            return_1d=returns.get("return_1d"),
            return_2d=returns.get("return_2d"),
            return_3d=returns.get("return_3d"),
            return_5d=returns.get("return_5d"),
            return_10d=returns.get("return_10d"),
            return_20d=returns.get("return_20d"),
            direction_1d=directions.get("direction_1d"),
            direction_2d=directions.get("direction_2d"),
            direction_3d=directions.get("direction_3d"),
            direction_5d=directions.get("direction_5d"),
            direction_10d=directions.get("direction_10d"),
            direction_20d=directions.get("direction_20d"),
            mfe_1d=mfe.get("mfe_1d"),
            mae_1d=mae.get("mae_1d"),
            mfe_5d=mfe.get("mfe_5d"),
            mae_5d=mae.get("mae_5d"),
            mfe_20d=mfe.get("mfe_20d"),
            mae_20d=mae.get("mae_20d"),
            hit_threshold_1d=hits.get("hit_1d"),
            hit_threshold_5d=hits.get("hit_5d"),
            hit_threshold_20d=hits.get("hit_20d"),
            data_availability={
                "return_1d": "available" if returns.get("return_1d") is not None else "unavailable",
                "return_5m": "FIELD_UNAVAILABLE",
                "return_15m": "FIELD_UNAVAILABLE",
                "return_30m": "FIELD_UNAVAILABLE",
                "return_1h": "FIELD_UNAVAILABLE",
                "return_4h": "FIELD_UNAVAILABLE",
            },
        )

        updated_event = MarketEvent(
            event_id=event.event_id,
            asset=event.asset,
            timeframe=event.timeframe,
            event_type=event.event_type,
            direction=event.direction,
            timestamp=event.timestamp,
            event_price=event.event_price,
            context=event.context,
            outcome=outcome,
            dataset_source=event.dataset_source,
            computation_method=event.computation_method,
            seed=event.seed,
        )
        updated_events.append(updated_event)

    return updated_events
