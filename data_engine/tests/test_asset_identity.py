"""
Tests for researchos.data_engine.asset_identity.

These tests enforce the canonical data-identity boundary that the forensic
audit identified as missing: COMEX gold futures (GC=F) must NEVER be accepted
as XAUUSD spot, and the spot proxy must be the canonical Yahoo XAUUSD symbol.
"""

from __future__ import annotations

import pytest

from researchos.data_engine.asset_identity import (
    COMEX_GOLD_FUTURES,
    DataIdentityError,
    XAUUSD_SPOT_YFINANCE,
    XAUUSD_SYMBOLS,
    assert_not_gold_futures,
    assert_xauusd_identity,
    is_gold_futures_symbol,
    resolve_xauusd_spot_proxy,
)


# ---------------------------------------------------------------------------
# Symbol families
# ---------------------------------------------------------------------------


def test_comex_gold_futures_set_contains_known_contamination():
    assert "GC=F" in COMEX_GOLD_FUTURES
    assert "GC1!" in COMEX_GOLD_FUTURES
    assert "GC=" in COMEX_GOLD_FUTURES


def test_xauusd_spot_proxy_is_canonical_spot():
    # The canonical spot proxy must NEVER be a futures contract.
    assert XAUUSD_SPOT_YFINANCE == "XAUUSD=X"
    assert not is_gold_futures_symbol(XAUUSD_SPOT_YFINANCE)
    assert resolve_xauusd_spot_proxy() == XAUUSD_SPOT_YFINANCE


def test_xauusd_symbol_family_recognised():
    for sym in ("XAUUSD", "XAU/USD", "GOLD"):
        assert sym in XAUUSD_SYMBOLS


# ---------------------------------------------------------------------------
# Predicate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fut", ["GC=F", "GC1!", "GC2!", "GC=", "/GC", "GC"])
def test_gold_futures_detected(fut):
    assert is_gold_futures_symbol(fut) is True


@pytest.mark.parametrize("ok", ["XAUUSD=X", "XAUUSD", "BTC-USD", "AAPL", "CL=F", ""])
def test_non_futures_not_flagged(ok):
    assert is_gold_futures_symbol(ok) is False


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


def test_gc_f_rejected_as_xauusd():
    with pytest.raises(DataIdentityError, match="COMEX gold FUTURES"):
        assert_xauusd_identity("XAUUSD", "GC=F")


def test_gc1_rejected_as_xauusd():
    with pytest.raises(DataIdentityError):
        assert_not_gold_futures("XAUUSD", "GC1!")


def test_spot_proxy_accepted_for_xauusd():
    # Must not raise: XAUUSD=X is the engineering spot proxy (delayed ref only).
    assert_xauusd_identity("XAUUSD", XAUUSD_SPOT_YFINANCE)


def test_non_xauusd_symbols_not_gated_by_xauusd_guard():
    # Other assets may legitimately use their own (futures or spot) tickers.
    assert_xauusd_identity("BTCUSD", "BTC-USD")
    assert_xauusd_identity("USOIL", "CL=F")


def test_gc_f_rejected_regardless_of_logical_symbol():
    # Gold futures are never an acceptable spot representation for any symbol
    # when routed through the general futures-as-spot guard.
    with pytest.raises(DataIdentityError):
        assert_not_gold_futures("XAUUSD", "GC=F")
