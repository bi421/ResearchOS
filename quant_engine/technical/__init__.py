"""
Technical Analysis Engine — deterministic vectorized indicator framework.

Research-only computation. No trading logic, no signals, no execution.
"""

from researchos.quant_engine.technical.contracts import (
    Bars,
    IndicatorBatch,
    IndicatorCategory,
    IndicatorFamily,
    IndicatorOutput,
    IndicatorSpec,
)
from researchos.quant_engine.technical.engine import (
    INDICATOR_REGISTRY,
    TechnicalAnalysisEngine,
    get_technical_engine,
    register_indicator,
)
from researchos.quant_engine.technical.validation import (
    validate_bars,
    validate_params,
    validate_period,
)

__all__ = [
    "Bars",
    "IndicatorBatch",
    "IndicatorCategory",
    "IndicatorFamily",
    "IndicatorOutput",
    "IndicatorSpec",
    "INDICATOR_REGISTRY",
    "TechnicalAnalysisEngine",
    "get_technical_engine",
    "register_indicator",
    "validate_bars",
    "validate_params",
    "validate_period",
]
