"""Safety and logic tests for the legacy live-data diagnostic boundary."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.run_live_signal import LiveTradingSignal


def _ohlc(rows: int = 220) -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=rows, freq="min", tz="UTC")
    close = pd.Series(np.linspace(2000.0, 2100.0, rows), index=index)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 2.0,
            "Low": close - 2.0,
            "Close": close,
        },
        index=index,
    )


def test_xauusd_uses_spot_engineering_proxy():
    system = LiveTradingSignal("XAUUSD")
    assert system.yf_symbol == "XAUUSD=X"


def test_gc_f_is_not_accepted_as_xauusd(monkeypatch):
    system = LiveTradingSignal("XAUUSD")
    monkeypatch.setattr(system, "yf_symbol", "GC=F")
    with pytest.raises(ValueError):
        system.fetch_live_data()


def test_diagnostic_never_claims_trading_confidence():
    system = LiveTradingSignal("XAUUSD")
    system.data = _ohlc()
    system.calculate_indicators()
    result = system.generate_signal()
    assert result["research_status"] == "UNVALIDATED_DIAGNOSTIC"
    assert result["trading_action"] == "DISABLED"
    assert "confidence" not in result
    assert "position_size" not in result


def test_second_source_validation_is_not_falsely_true():
    system = LiveTradingSignal("XAUUSD")
    system.data = _ohlc()
    system.calculate_indicators()
    system.generate_signal()
    assert system.validate_with_second_source() is False


def test_incomplete_indicator_history_fails_closed():
    system = LiveTradingSignal("XAUUSD")
    system.data = _ohlc(50)
    system.calculate_indicators()
    with pytest.raises(ValueError, match="200 observations"):
        system.generate_signal()
