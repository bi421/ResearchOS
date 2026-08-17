"""XAUUSD macro interpretation engine (Phase 0 constitutional layer).

This package is the asset-specific interpretation layer for XAUUSD macro
analysis.  Generic macro intelligence (regimes, econometrics, events,
relationships) is owned by the standalone ``macro_intelligence`` library —
do not add generic macro logic here (see docs/architecture/OWNERSHIP.md).

The module previously worked only through implicit namespace-package
behavior; this ``__init__`` makes the package explicit and re-exports the
public engine surface.
"""

from researchos.macro.engine import (
    ALL_DRIVERS,
    DRIVER_WEIGHTS,
    MacroAnalysisEngine,
)

__all__ = [
    "ALL_DRIVERS",
    "DRIVER_WEIGHTS",
    "MacroAnalysisEngine",
]
