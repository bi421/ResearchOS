"""
Technical Analysis Engine — input validation.

Validates bar series and indicator specifications before computation so
that the computation layer can assume well-formed inputs.
"""

from __future__ import annotations

from typing import Any, Dict

from researchos.quant_engine.technical.contracts import Bars


def validate_bars(bars: Bars) -> None:
    """Validate that the bar series is well-formed."""
    if bars.length == 0:
        raise ValueError("Cannot compute indicators on an empty bar series")

    bars.validate()

    for name, series in (
        ("open", bars.open),
        ("high", bars.high),
        ("low", bars.low),
        ("close", bars.close),
        ("volume", bars.volume),
    ):
        for i, value in enumerate(series):
            if value is None:
                raise ValueError(f"{name} series contains None at index {i}")
            if not isinstance(value, (int, float)):
                raise TypeError(f"{name} series must contain numeric values, got {type(value)}")
            if value != value:  # NaN check
                raise ValueError(f"{name} series contains NaN at index {i}")


def validate_period(period: Any, default: int = 14) -> int:
    """Validate/coerce a period parameter."""
    if period is None:
        return default
    if not isinstance(period, (int, float)):
        raise TypeError(f"period must be numeric, got {type(period)}")
    p = int(period)
    if p <= 0:
        raise ValueError(f"period must be positive, got {p}")
    return p


def validate_positive_float(name: str, value: Any, default: float) -> float:
    """Validate/coerce a positive float parameter."""
    if value is None:
        return default
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric, got {type(value)}")
    v = float(value)
    if v <= 0:
        raise ValueError(f"{name} must be positive, got {v}")
    return v


def validate_params(
    params: Dict[str, Any],
    allowed: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate indicator params against a schema of default values.

    Args:
        params: The user-supplied parameters.
        allowed: Mapping of param name → default value.

    Returns:
        A validated parameter dict with defaults filled in.
    """
    unknown = set(params.keys()) - set(allowed.keys())
    if unknown:
        raise ValueError(f"Unknown indicator parameters: {sorted(unknown)}")

    result: Dict[str, Any] = {}
    for key, default in allowed.items():
        result[key] = params.get(key, default)
    return result
