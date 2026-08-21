"""
Macro economic factors provider (DXY, US10Y, VIX, XAUUSD).
"""

import pandas as pd

from researchos.data_engine.contracts import Timeframe
from researchos.data_engine.repository import DatasetRepository


class MacroFactorProvider:
    """Fetch macro economic indicators from DatasetRepository."""

    def __init__(self, repository: DatasetRepository):
        self.repo = repository

    def get_factors(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        timeframe: Timeframe | None = None,
    ) -> pd.DataFrame:
        """
        Fetch historical closing prices for given symbols.

        Args:
            symbols: List of tickers (e.g., ["DXY", "US10Y", "VIX", "XAUUSD"]).
            start_date: "YYYY-MM-DD".
            end_date: "YYYY-MM-DD".
            timeframe: Timeframe (default: first enum value).

        Returns:
            DataFrame with columns = symbols, index = dates.
        """
        if timeframe is None:
            try:
                timeframe = list(Timeframe)[0]
            except Exception:
                timeframe = list(Timeframe)[0]  # fallback

        data = {}
        for symbol in symbols:
            # find_by_symbol_and_timeframe ?? (symbol, timeframe.value) ???????
            dataset = self.repo.find_by_symbol_and_timeframe(symbol, timeframe.value)
            if dataset is None:
                continue  # ??????? ??????? ??? ???????
            # HistoricalDataset-??? DataFrame ??????
            try:
                df = dataset.to_dataframe(start=start_date, end=end_date)
                data[symbol] = df["close"]
            except AttributeError:
                # to_dataframe ??????? ??? _records-??? ???? DataFrame ????
                records = getattr(dataset, "_records", [])
                if records:
                    df = pd.DataFrame([{"timestamp": r.timestamp, "close": r.close} for r in records])
                    df = df.set_index("timestamp")
                    df = df.loc[start_date:end_date] if start_date in df.index else df
                    data[symbol] = df["close"]
                else:
                    continue
        return pd.DataFrame(data)
