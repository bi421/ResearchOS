"""
Technical Analysis Engine — deterministic batch indicator computation.

The engine is a registry-based orchestrator:

    IndicatorSpec
        ↓
    TechnicalAnalysisEngine (registry dispatch)
        ↓
    IndicatorOutput
        ↓
    IndicatorBatch

Adding a new indicator requires only:
    1. Implement a pure function in ``indicators.py``
    2. Register it in the registry dict below

No changes to the engine core, contracts, or upper layers are required.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from researchos.quant_engine.technical.contracts import (
    Bars,
    IndicatorBatch,
    IndicatorCategory,
    IndicatorOutput,
    IndicatorSpec,
)
from researchos.quant_engine.technical.validation import (
    validate_bars,
    validate_params,
    validate_period,
    validate_positive_float,
)

# Registry: name → (compute callable, param schema, category)
INDICATOR_REGISTRY: Dict[str, Any] = {}


def register_indicator(
    name: str, category: IndicatorCategory, param_schema: Dict[str, Any]
) -> Callable:
    """
    Decorator to register an indicator computation function.

    The decorated function must accept ``bars`` (Bars) plus validated params
    and return either a ``List[Optional[float]]`` or a ``Dict[str, List[Optional[float]]]``.
    """

    def decorator(fn: Callable) -> Callable:
        INDICATOR_REGISTRY[name] = {
            "function": fn,
            "schema": param_schema,
            "category": category,
        }
        return fn

    return decorator


class TechnicalAnalysisEngine:
    """
    Vectorized, deterministic indicator computation engine.

    All computations are pure functions of the input bar series.
    The engine is stateless — no RNG, no hidden state, no wall-clock
    dependence. Identical inputs always produce identical outputs.
    """

    def __init__(self) -> None:
        self._registry = dict(INDICATOR_REGISTRY)

    @property
    def available_indicators(self) -> List[str]:
        """List of registered indicator names."""
        return sorted(self._registry.keys())

    def compute(
        self,
        bars: Bars,
        spec: IndicatorSpec,
    ) -> IndicatorOutput:
        """
        Compute a single indicator.

        Args:
            bars: Immutable OHLCV bar series.
            spec: The indicator specification.

        Returns:
            IndicatorOutput with values aligned to the input bar count.
        """
        validate_bars(bars)
        if spec.name not in self._registry:
            raise KeyError(
                f"Unknown indicator '{spec.name}'. Available: {self.available_indicators}"
            )

        entry = self._registry[spec.name]
        schema = entry["schema"]
        params = validate_params(spec.params, schema)

        # Validate numeric params against the schema.
        for key, default in schema.items():
            if key == "period":
                params[key] = validate_period(params[key], int(default))
            elif key in ("std_dev", "multiplier"):
                params[key] = validate_positive_float(key, params[key], float(default))
            elif isinstance(default, int):
                params[key] = int(params[key])
            elif isinstance(default, float):
                params[key] = float(params[key])

        result = entry["function"](bars, **params)

        if isinstance(result, dict):
            values: List[Optional[float]] = result.get(
                self._primary_key_for(spec.name), [None] * bars.length
            )
            aux: Dict[str, List[Optional[float]]] = {
                k: v for k, v in result.items() if k != self._primary_key_for(spec.name)
            }
        else:
            values = result
            aux = {}

        return IndicatorOutput(
            name=spec.name,
            values=values,
            aux=aux,
            category=spec.category or entry["category"],
            params=params,
        )

    def compute_batch(
        self,
        bars: Bars,
        specs: List[IndicatorSpec],
    ) -> IndicatorBatch:
        """
        Compute a batch of indicators deterministically.

        Args:
            bars: Immutable OHLCV bar series.
            specs: List of indicator specifications.

        Returns:
            IndicatorBatch with one IndicatorOutput per spec.
        """
        validate_bars(bars)
        outputs: Dict[str, IndicatorOutput] = {}
        for spec in specs:
            out = self.compute(bars, spec)
            outputs[spec.name] = out
        return IndicatorBatch(
            outputs=outputs,
            bar_count=bars.length,
            computation_version="TECHNICAL_V1",
        )

    @staticmethod
    def _primary_key_for(name: str) -> str:
        """The main series key for an indicator's dict output."""
        if name == "MACD":
            return "macd"
        if name == "Stochastic":
            return "k"
        if name == "Bollinger":
            return "middle"
        if name == "Keltner":
            return "middle"
        if name == "Donchian":
            return "middle"
        if name == "DMI":
            return "adx"
        if name == "SuperTrend":
            return "supertrend"
        if name == "Ichimoku":
            return "tenkan_sen"
        if name == "PSAR":
            return "psar"
        return "value"


# Register all built-in indicators.
# (Registration uses functions imported lazily to keep the registry clean.)


def _register_builtins() -> None:
    from researchos.quant_engine.technical import indicators as ind

    # Trend
    register_indicator("SMA", IndicatorCategory.TREND, {"period": 20})(
        lambda bars, period: ind.sma(bars, period)
    )
    register_indicator("EMA", IndicatorCategory.TREND, {"period": 20})(
        lambda bars, period: ind.ema(bars, period)
    )
    register_indicator("WMA", IndicatorCategory.TREND, {"period": 20})(
        lambda bars, period: ind.wma(bars, period)
    )
    register_indicator("HMA", IndicatorCategory.TREND, {"period": 20})(
        lambda bars, period: ind.hma(bars, period)
    )
    register_indicator("VWMA", IndicatorCategory.TREND, {"period": 20})(
        lambda bars, period: ind.vwma(bars, period)
    )
    register_indicator("SuperTrend", IndicatorCategory.TREND, {"period": 10, "multiplier": 3.0})(
        lambda bars, period, multiplier: ind.supertrend(bars, period, multiplier)
    )
    register_indicator(
        "Ichimoku",
        IndicatorCategory.TREND,
        {"tenkan_period": 9, "kijun_period": 26, "senkou_b_period": 52, "displacement": 26},
    )(
        lambda bars, tenkan_period, kijun_period, senkou_b_period, displacement: ind.ichimoku_cloud(
            bars, tenkan_period, kijun_period, senkou_b_period, displacement
        )
    )
    register_indicator("PSAR", IndicatorCategory.TREND, {"af_step": 0.02, "af_max": 0.2})(
        lambda bars, af_step, af_max: ind.parabolic_sar(bars, af_step, af_max)
    )

    # Momentum
    register_indicator("RSI", IndicatorCategory.MOMENTUM, {"period": 14})(
        lambda bars, period: ind.rsi(bars, period)
    )
    register_indicator(
        "Stochastic", IndicatorCategory.MOMENTUM, {"period": 14, "smooth_k": 3, "smooth_d": 3}
    )(lambda bars, period, smooth_k, smooth_d: ind.stochastic(bars, period, smooth_k, smooth_d))
    register_indicator("CCI", IndicatorCategory.MOMENTUM, {"period": 20})(
        lambda bars, period: ind.cci(bars, period)
    )
    register_indicator("ROC", IndicatorCategory.MOMENTUM, {"period": 12})(
        lambda bars, period: ind.roc(bars, period)
    )
    register_indicator("Momentum", IndicatorCategory.MOMENTUM, {"period": 12})(
        lambda bars, period: ind.momentum(bars, period)
    )

    # Volatility
    register_indicator("ATR", IndicatorCategory.VOLATILITY, {"period": 14})(
        lambda bars, period: ind.atr(bars, period)
    )
    register_indicator("Bollinger", IndicatorCategory.VOLATILITY, {"period": 20, "std_dev": 2.0})(
        lambda bars, period, std_dev: ind.bollinger_bands(bars, period, std_dev)
    )
    register_indicator(
        "Keltner", IndicatorCategory.VOLATILITY, {"period": 20, "atr_period": 10, "multiplier": 2.0}
    )(
        lambda bars, period, atr_period, multiplier: ind.keltner_channel(
            bars, period, atr_period, multiplier
        )
    )
    register_indicator("Donchian", IndicatorCategory.VOLATILITY, {"period": 20})(
        lambda bars, period: ind.donchian_channel(bars, period)
    )

    # Volume
    register_indicator("OBV", IndicatorCategory.VOLUME, {})(lambda bars: ind.obv(bars))
    register_indicator("VWAP", IndicatorCategory.VOLUME, {})(lambda bars: ind.vwap(bars))
    register_indicator("MFI", IndicatorCategory.VOLUME, {"period": 14})(
        lambda bars, period: ind.mfi(bars, period)
    )
    register_indicator("CMF", IndicatorCategory.VOLUME, {"period": 20})(
        lambda bars, period: ind.cmf(bars, period)
    )
    register_indicator("Accumulation/Distribution", IndicatorCategory.VOLUME, {})(
        lambda bars: ind.accumulation_distribution(bars)
    )

    # Trend strength
    register_indicator("ADX", IndicatorCategory.TREND_STRENGTH, {"period": 14})(
        lambda bars, period: ind.adx(bars, period)
    )
    register_indicator("DMI", IndicatorCategory.TREND_STRENGTH, {"period": 14})(
        lambda bars, period: ind.dmi(bars, period)
    )

    # MACD family
    register_indicator("MACD", IndicatorCategory.MACD, {"fast": 12, "slow": 26, "signal": 9})(
        lambda bars, fast, slow, signal: ind.macd(bars, fast, slow, signal)
    )


_register_builtins()


# Convenience factory
def get_technical_engine() -> TechnicalAnalysisEngine:
    """Get a fresh TechnicalAnalysisEngine instance."""
    return TechnicalAnalysisEngine()
