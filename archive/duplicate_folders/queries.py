"""
Queries — data querying interface for the Data Engine.

Re-exports RangeQuery and MultiSymbolQuery from the canonical `query` module.

This module exists to provide the public `queries` namespace for consumers
while keeping the implementations in `researchos.data_engine.query`.
"""

from __future__ import annotations

from researchos.data_engine.query import MultiSymbolQuery, RangeQuery

__all__ = ["RangeQuery", "MultiSymbolQuery"]
