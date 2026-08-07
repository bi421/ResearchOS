"""
Unit tests for Technical Analysis Engine missing indicators:
- SuperTrend
- Ichimoku Cloud
- Parabolic SAR
- Determinism and contract validation
"""

from researchos.quant_engine.technical.contracts import (
    Bars,
    IndicatorSpec,
)
from researchos.quant_engine.technical.engine import get_technical_engine
from researchos.quant_engine.technical.indicators import (
    ichimoku_cloud,
    parabolic_sar,
    supertrend,
)


def _sample_bars(length: int = 50) -> Bars:
    open_prices = [100.0 + (i * 0.5) for i in range(length)]
    high_prices = [o + 1.5 for o in open_prices]
    low_prices = [o - 1.0 for o in open_prices]
    close_prices = [o + 0.5 for o in open_prices]
    volumes = [1000.0 + i * 10.0 for i in range(length)]
    return Bars(
        open=open_prices,
        high=high_prices,
        low=low_prices,
        close=close_prices,
        volume=volumes,
    )


class TestSuperTrend:
    def test_supertrend_structure(self):
        bars = _sample_bars(40)
        res = supertrend(bars, period=10, multiplier=3.0)
        assert "supertrend" in res
        assert "upper_band" in res
        assert "lower_band" in res
        assert "trend" in res

        assert len(res["supertrend"]) == 40
        assert len(res["trend"]) == 40

    def test_supertrend_determinism(self):
        bars = _sample_bars(40)
        res1 = supertrend(bars, period=10, multiplier=3.0)
        res2 = supertrend(bars, period=10, multiplier=3.0)
        assert res1 == res2

    def test_supertrend_engine_integration(self):
        engine = get_technical_engine()
        bars = _sample_bars(30)
        spec = IndicatorSpec(name="SuperTrend", params={"period": 10, "multiplier": 3.0})
        out = engine.compute(bars, spec)
        assert out.name == "SuperTrend"
        assert len(out.values) == 30
        assert "upper_band" in out.aux
        assert "lower_band" in out.aux
        assert "trend" in out.aux


class TestIchimokuCloud:
    def test_ichimoku_structure(self):
        bars = _sample_bars(60)
        res = ichimoku_cloud(bars, tenkan_period=9, kijun_period=26, senkou_b_period=52, displacement=26)
        assert "tenkan_sen" in res
        assert "kijun_sen" in res
        assert "senkou_span_a" in res
        assert "senkou_span_b" in res
        assert "chikou_span" in res

        assert len(res["tenkan_sen"]) == 60

    def test_ichimoku_determinism(self):
        bars = _sample_bars(60)
        res1 = ichimoku_cloud(bars)
        res2 = ichimoku_cloud(bars)
        assert res1 == res2

    def test_ichimoku_engine_integration(self):
        engine = get_technical_engine()
        bars = _sample_bars(60)
        spec = IndicatorSpec(name="Ichimoku")
        out = engine.compute(bars, spec)
        assert out.name == "Ichimoku"
        assert len(out.values) == 60
        assert "kijun_sen" in out.aux
        assert "senkou_span_a" in out.aux
        assert "senkou_span_b" in out.aux
        assert "chikou_span" in out.aux


class TestParabolicSAR:
    def test_psar_structure(self):
        bars = _sample_bars(30)
        res = parabolic_sar(bars, af_step=0.02, af_max=0.2)
        assert "psar" in res
        assert "trend" in res
        assert len(res["psar"]) == 30

    def test_psar_determinism(self):
        bars = _sample_bars(30)
        res1 = parabolic_sar(bars, af_step=0.02, af_max=0.2)
        res2 = parabolic_sar(bars, af_step=0.02, af_max=0.2)
        assert res1 == res2

    def test_psar_engine_integration(self):
        engine = get_technical_engine()
        bars = _sample_bars(30)
        spec = IndicatorSpec(name="PSAR")
        out = engine.compute(bars, spec)
        assert out.name == "PSAR"
        assert len(out.values) == 30
        assert "trend" in out.aux
