"""
Data Identity - canonical asset/symbol identity boundaries for ResearchOS.

This module prevents instrument substitution at data-ingestion boundaries.
XAUUSD spot and COMEX gold futures are distinct instruments. Yahoo Finance
tickers may be used only as explicitly named engineering references, never as
canonical historical evidence.
"""

from __future__ import annotations

import re

XAUUSD_SYMBOLS: frozenset[str] = frozenset({"XAUUSD", "XAU/USD", "GOLD"})
COMEX_GOLD_FUTURES: frozenset[str] = frozenset(
    {"GC=F", "GC1!", "GC2!", "GC3!", "GC4!", "GC=", "/GC", "HGC!"}
)
XAUUSD_SPOT_YFINANCE = "XAUUSD=X"


class DataIdentityError(ValueError):
    """Raised when an instrument is used under an incompatible identity.

    ``str(error)`` is human-readable prose and is not a stable API contract.
    Callers/tests should use the structured attributes instead.
    """

    def __init__(
        self,
        message: str,
        *,
        offending_ticker: str,
        declared_symbol: str,
    ) -> None:
        super().__init__(message)
        self.offending_ticker = offending_ticker
        self.declared_symbol = declared_symbol


def _normalise(value: str) -> str:
    return value.strip().upper()


def is_gold_futures_symbol(yf_symbol: str) -> bool:
    """Return True when a ticker identifies a COMEX gold futures contract."""
    if not isinstance(yf_symbol, str):
        return False
    candidate = _normalise(yf_symbol)
    if candidate in COMEX_GOLD_FUTURES or candidate == "GC":
        return True
    if re.fullmatch(r"GC[A-Z]\d{2,4}", candidate):
        return True
    if re.fullmatch(r"GC\d+!", candidate):
        return True
    return False


def resolve_xauusd_spot_proxy() -> str:
    """Return the explicitly declared Yahoo XAU/USD spot engineering proxy."""
    return XAUUSD_SPOT_YFINANCE


def assert_not_gold_futures(symbol: str, yf_symbol: str) -> None:
    """Reject a gold futures ticker when the logical instrument is spot."""
    if is_gold_futures_symbol(yf_symbol):
        raise DataIdentityError(
            f"Data-identity violation: '{yf_symbol}' is a gold futures contract "
            f"and must never be treated as {symbol} spot.",
            offending_ticker=yf_symbol,
            declared_symbol=symbol,
        )


def assert_xauusd_identity(symbol: str, yf_symbol: str) -> None:
    """Require XAUUSD Yahoo lookups to use the declared spot proxy exactly."""
    logical = _normalise(symbol).replace("/", "")
    xauusd_family = {_normalise(s).replace("/", "") for s in XAUUSD_SYMBOLS}
    if logical not in xauusd_family:
        return

    assert_not_gold_futures(symbol, yf_symbol)
    if _normalise(yf_symbol) != XAUUSD_SPOT_YFINANCE:
        raise DataIdentityError(
            f"Data-identity violation: '{yf_symbol}' is not the declared XAUUSD "
            f"spot engineering proxy '{XAUUSD_SPOT_YFINANCE}'.",
            offending_ticker=yf_symbol,
            declared_symbol=symbol,
        )
