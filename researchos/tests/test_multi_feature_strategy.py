import numpy as np
import pandas as pd
import pytest

from researchos.signals.multi_feature import generate_multi_feature_signals


def _bars(closes: list[float], ranges: float | list[float]) -> pd.DataFrame:
    close = pd.Series(closes, index=pd.date_range("2020-01-01", periods=len(closes)))
    range_values = pd.Series(ranges if isinstance(ranges, list) else [ranges] * len(close), index=close.index)
    return pd.DataFrame(
        {
            "high": close + range_values,
            "low": close - range_values,
            "close": close,
        }
    )


def test_preserves_index_dtype_and_warmup_is_flat() -> None:
    bars = _bars([100.0] * 49, 1.0)

    signals = generate_multi_feature_signals(bars)

    assert signals.index.equals(bars.index)
    assert signals.dtype == np.int8
    assert (signals == 0).all()


def test_combines_trend_momentum_and_volatility() -> None:
    rising = [100.0] * 50 + [101.0 + i for i in range(20)]
    falling = [100.0] * 50 + [99.0 - i for i in range(20)]

    ranges = [0.5] * 50 + [3.0] * 20
    long_signal = generate_multi_feature_signals(_bars(rising, ranges))
    short_signal = generate_multi_feature_signals(_bars(falling, ranges))

    assert long_signal.iloc[-1] == 1
    assert short_signal.iloc[-1] == -1


def test_rejects_missing_ohlc_columns() -> None:
    with pytest.raises(ValueError, match="Missing required columns: high, low"):
        generate_multi_feature_signals(pd.DataFrame({"close": [1.0]}))
