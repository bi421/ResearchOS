"""Stable entrypoint for the real XAUUSD M1 research contract."""

from researchos.market_memory.m1_event_engine import extract_xauusd_m1_sma_crossover_events
from researchos.market_memory.m1_outcome_contract import M1OutcomeContract

__all__ = ["M1OutcomeContract", "extract_xauusd_m1_sma_crossover_events"]
