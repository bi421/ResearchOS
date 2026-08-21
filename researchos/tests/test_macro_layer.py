"""
Test Market Intelligence Layer.
"""

import pytest

pytest.skip("Requires live market data provider — not a unit test", allow_module_level=True)

from researchos.engines.data.contracts import Timeframe
from researchos.engines.data.macro_analyzer import MacroAnalyzer
from researchos.engines.data.macro_provider import MacroFactorProvider
from researchos.engines.data.repository import SqliteDatasetRepository

# 1. Init
repo = SqliteDatasetRepository("researchos.db")
provider = MacroFactorProvider(repo)
analyzer = MacroAnalyzer()

# 2. Get data
df = provider.get_factors(
    symbols=["XAUUSD"],
    start_date="2025-01-01",
    end_date="2025-12-31",
    timeframe=Timeframe.D1,
)
print("DataFrame shape:", df.shape)
print(df.head())

# 3. Analyze
corr = analyzer.compute_correlation(df, "XAUUSD")
print("Correlations with XAUUSD:", corr if corr else "(no other factors yet)")
