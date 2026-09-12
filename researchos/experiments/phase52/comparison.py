"""Public optimized comparison entry point for Phase 5.2."""
from __future__ import annotations

from .execution import run_prepared_phase52_comparison
from .experiment import Phase52Config
from .prepared import Phase52PreparedData


def run_phase52_comparison_optimized(
    close,
    high,
    low,
    volume,
    macro_factor_series,
    *,
    config: Phase52Config | None = None,
    timestamps=None,
    macro_timestamps=None,
):
    """Prepare once, then execute every feature set against the same dataset."""
    cfg = config or Phase52Config()
    if timestamps is None or macro_timestamps is None:
        raise ValueError("Explicit UTC timestamps are required for optimized Phase 5.2 comparison")
    prepared = Phase52PreparedData.build(
        close,
        high,
        low,
        volume,
        timestamps,
        macro_timestamps,
        macro_factor_series,
        horizon=cfg.horizon,
        threshold=cfg.threshold,
        required_macro_symbols=cfg.required_macro_symbols,
    )
    return run_prepared_phase52_comparison(prepared, cfg)


__all__ = ["run_phase52_comparison_optimized"]
