"""Regression tests for research-integrity boundaries identified by the code audit."""

import pytest

from researchos.data_engine.asset_identity import (
    DataIdentityError,
    assert_xauusd_identity,
    is_gold_futures_symbol,
    resolve_xauusd_spot_proxy,
)


def test_xauusd_identity_rejects_any_non_spot_yahoo_symbol():
    with pytest.raises(DataIdentityError):
        assert_xauusd_identity("XAUUSD", "BTC-USD")


def test_xauusd_identity_accepts_only_declared_spot_proxy():
    assert_xauusd_identity("XAUUSD", resolve_xauusd_spot_proxy())


def test_gold_futures_detection_is_case_insensitive_for_known_tickers():
    assert is_gold_futures_symbol("GC=F")
    assert is_gold_futures_symbol("gc=f")
    assert is_gold_futures_symbol("GC")
    assert not is_gold_futures_symbol("XAUUSD=X")


def test_xauusd_family_aliases_are_guarded():
    for symbol in ("XAUUSD", "XAU/USD", "GOLD"):
        with pytest.raises(DataIdentityError):
            assert_xauusd_identity(symbol, "GC=F")
