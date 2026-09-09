"""Deterministic XAUUSD M1 event extraction.

This module defines the first real-M1 event surface for the Market Memory
pipeline. Events are derived only from bars at or before the event timestamp;
forward outcomes are intentionally handled by ``outcome_engine``.
"""
from __future__ import annotations

import polars as pl

from researchos.market_memory.event_extractor import (
    _compute_atr,
    _compute_macd,
    _compute_rsi,
    _compute_sma,
    _compute_regime,
    _determine_session,
)
from researchos.market_memory.event_schema import (
    CrossoverDirection,
    EventContext,
    EventType,
    MarketEvent,
)


def extract_xauusd_m1_sma_crossover_events(
    df: pl.DataFrame,
    fast_period: int = 20,
    slow_period: int = 100,
    dataset_source: str = "xauusd_m1_mt5",
    seed: int = 42,
) -> list[MarketEvent]:
    """Extract leakage-safe SMA20/100 crossover events from XAUUSD M1 data.

    Required columns are ``timestamp, open, high, low, close, tick_volume``.
    No future rows are read while constructing an event.
    """
    required = {"timestamp", "open", "high", "low", "close", "tick_volume"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"df missing columns: {sorted(missing)}")
    if fast_period < 1 or slow_period <= fast_period:
        raise ValueError("periods must satisfy 1 <= fast_period < slow_period")
    if len(df) < slow_period + 1:
        raise ValueError(f"Insufficient data: need at least {slow_period + 1} bars, got {len(df)}")

    frame = df.sort("timestamp")
    closes = frame["close"].to_list()
    timestamps = frame["timestamp"].to_list()
    highs = frame["high"].to_list()
    lows = frame["low"].to_list()
    opens = frame["open"].to_list()
    volumes = frame["tick_volume"].to_list()

    sma_fast = _compute_sma(closes, fast_period)
    sma_slow = _compute_sma(closes, slow_period)
    atr = _compute_atr(highs, lows, closes)
    rsi = _compute_rsi(closes)
    macd_line, macd_signal, macd_histogram = _compute_macd(closes)

    events: list[MarketEvent] = []
    for i in range(slow_period, len(frame)):
        prev_fast, prev_slow = sma_fast[i - 1], sma_slow[i - 1]
        curr_fast, curr_slow = sma_fast[i], sma_slow[i]
        if None in (prev_fast, prev_slow, curr_fast, curr_slow):
            continue

        direction: str | None = None
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            direction = CrossoverDirection.BULLISH.value
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            direction = CrossoverDirection.BEARISH.value
        if direction is None:
            continue

        timestamp = timestamps[i]
        event_id = (
            f"XAUUSD_M1_SMA{fast_period}_{slow_period}_"
            f"{timestamp.strftime('%Y%m%dT%H%M%S')}_{direction}"
        )
        regime, vol_state = _compute_regime(curr_fast, curr_slow, atr[i], closes[i])
        context = EventContext(
            event_id=event_id,
            asset="XAUUSD",
            timeframe="M1",
            timestamp=timestamp,
            event_price=closes[i],
            open_price=opens[i],
            high_price=highs[i],
            low_price=lows[i],
            close_price=closes[i],
            tick_volume=int(volumes[i]),
            sma_fast=curr_fast,
            sma_slow=curr_slow,
            atr=atr[i],
            rsi=rsi[i] if rsi[i] is not None else 50.0,
            macd_line=macd_line[i],
            macd_signal=macd_signal[i],
            macd_histogram=macd_histogram[i],
            market_regime=regime,
            volatility_state=vol_state,
            day_of_week=timestamp.weekday(),
            session=_determine_session(timestamp),
            preceding_return_1d=(closes[i] - closes[i - 1]) / closes[i - 1],
            preceding_return_3d=(closes[i] - closes[i - 3]) / closes[i - 3] if i >= 3 else None,
            preceding_return_5d=(closes[i] - closes[i - 5]) / closes[i - 5] if i >= 5 else None,
        )
        events.append(
            MarketEvent(
                event_id=event_id,
                asset="XAUUSD",
                timeframe="M1",
                event_type=EventType.SMA_CROSSOVER.value,
                direction=direction,
                timestamp=timestamp,
                event_price=closes[i],
                context=context,
                dataset_source=dataset_source,
                computation_method=f"M1_SMA{fast_period}/{slow_period}_crossover",
                seed=seed,
            )
        )
    return events
