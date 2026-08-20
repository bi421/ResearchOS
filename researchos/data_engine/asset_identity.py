"""
Data Identity — canonical asset/symbol identity boundaries for ResearchOS.

REPAIR (forensic audit, data-identity boundary):
    The repository shipped several ad-hoc analytics scripts that mapped the
    XAUUSD (gold) asset to Yahoo Finance ticker ``GC=F`` -- the COMEX gold
    *futures* contract -- and treated that as canonical XAUUSD *spot* data.

    GC=F is NOT XAUUSD spot:

        * GC=F  -> COMEX Gold Futures (CME/COMEX, front-month, roll-adjusted).
                   The futures price embeds cost-of-carry, roll timing, and
                   futures-basis effects relative to spot.
        * XAUUSD -> the OTC gold *spot* rate (London / OTC fix vs USD).
                   It is a different instrument with different dynamics and a
                   different publication/availability schedule.

    Mapping XAUUSD -> GC=F corrupts the primary research asset: every
    measurement, return, correlation, and label downstream is computed on the
    wrong instrument.  This module enforces the boundary with a single,
    tested contract so the contamination cannot silently recur.

YFinance is NOT canonical real XAUUSD data:
    yfinance returns delayed/aggregated Yahoo data with no guaranteed
    availability time, publication time, or revision semantics, and is NOT a
    verified historical OHLCV source for scientific research.  Canonical real
    XAUUSD historical OHLCV MUST be loaded via
    ``researchos.data_engine.csv_loader.CsvLoader`` from curated historical CSVs
    (e.g. ``data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv``), which
    carry dataset identity, source provenance, and content hashing.

    Delayed/synthetic data (including yfinance) may be used for engineering,
    deterministic, integration, and benchmark tests ONLY.  It MUST NEVER be
    treated as evidence for real-market predictive value.

Public API:
    XAUUSD_SYMBOLS            - canonical XAUUSD symbol family.
    COMEX_GOLD_FUTURES        - gold futures tickers that are NOT XAUUSD spot.
    DataIdentityError         - raised when a futures contract is mislabeled.
    is_gold_futures_symbol    - predicate for COMEX gold futures tickers.
    resolve_xauusd_spot_proxy - canonical Yahoo spot proxy for XAUUSD.
    assert_xauusd_identity    - guard: rejects gold futures as XAUUSD spot.
    assert_not_gold_futures   - general guard: rejects gold futures as spot.
"""

from __future__ import annotations

from typing import FrozenSet

# ---------------------------------------------------------------------------
# Symbol families
# ---------------------------------------------------------------------------

#: Canonical symbol spellings for the XAUUSD (gold/USD) spot asset.
XAUUSD_SYMBOLS: FrozenSet[str] = frozenset({"XAUUSD", "XAU/USD", "GOLD"})

#: COMEX gold *futures* tickers.  These carry futures roll/carry dynamics and
#: are NEVER acceptable as a representation of XAUUSD spot.
COMEX_GOLD_FUTURES: FrozenSet[str] = frozenset(
    {
        "GC=F",  # COMEX Gold Futures (Yahoo front-month)
        "GC1!",  # front-month continuous
        "GC2!",
        "GC3!",
        "GC4!",
        "GC=",  # Bloomberg-style COMEX gold futures root
        "/GC",  # CME ticker root
        "HGC!",  # alternate gold front-month
    }
)

#: Canonical Yahoo Finance spot proxy for XAUUSD.  ``XAUUSD=X`` is Yahoo's
#: aggregated OTC XAU/USD spot index -- the only Yahoo ticker the analytics
#: surface may use for XAUUSD, and never as a substitute for real curated data.
XAUUSD_SPOT_YFINANCE: str = "XAUUSD=X"


class DataIdentityError(ValueError):
    """Raised when a futures contract or wrong instrument is mislabeled as XAUUSD spot."""


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------


def is_gold_futures_symbol(yf_symbol: str) -> bool:
    """Return True if *yf_symbol* is a COMEX gold futures contract (= NOT spot)."""
    if not isinstance(yf_symbol, str):
        return False
    candidate = yf_symbol.strip()
    if candidate in COMEX_GOLD_FUTURES:
        return True
    # Catch un-suffixed futures roots (e.g. "GC") while never flagging the
    # XAUUSD spot proxy.
    if candidate.upper() == "GC":
        return True
    return False


def resolve_xauusd_spot_proxy() -> str:
    """Return the canonical Yahoo spot proxy for XAUUSD.

    This is the ONLY Yahoo ticker the analytics surface may use for XAUUSD,
    and only as a delayed engineering reference -- never as canonical
    real-market evidence (use CsvLoader on curated CSVs for that).
    """
    return XAUUSD_SPOT_YFINANCE


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


def assert_not_gold_futures(symbol: str, yf_symbol: str) -> None:
    """Reject gold futures being represented as a spot gold instrument.

    Args:
        symbol: The logical asset symbol (e.g. "XAUUSD").
        yf_symbol: The Yahoo Finance ticker actually fetched.

    Raises:
        DataIdentityError: if *yf_symbol* is a COMEX gold futures contract.
    """
    if is_gold_futures_symbol(yf_symbol):
        raise DataIdentityError(
            f"Data-identity violation: '{yf_symbol}' is a COMEX gold FUTURES "
            f"contract and must NEVER be treated as {symbol} spot. XAUUSD spot "
            f"must use the curated historical dataset loaded via "
            f"researchos.data_engine.csv_loader.CsvLoader, or the spot proxy "
            f"'{XAUUSD_SPOT_YFINANCE}' for a delayed engineering reference only."
        )


def assert_xauusd_identity(symbol: str, yf_symbol: str) -> None:
    """Guard: XAUUSD must never resolve to a COMEX gold futures contract.

    For non-XAUUSD symbols this is a no-op (callers may legitimately fetch
    other futures for other assets).  For XAUUSD-family symbols it delegates
    to :func:`assert_not_gold_futures`.
    """
    if symbol.upper().replace("/", "") in {s.upper().replace("/", "") for s in XAUUSD_SYMBOLS}:
        assert_not_gold_futures(symbol, yf_symbol)
