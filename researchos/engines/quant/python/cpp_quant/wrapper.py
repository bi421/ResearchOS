import pandas as pd
import numpy as np
import glob

try:
    # E????? ????? ?????????? ????, ????? ?? build ??????????
    try:
        import cpp_quant_core as _core
    except ImportError:
        import sys

        sys.path.insert(0, "cpp_quant/build/Release")
        import cpp_quant_core as _core
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False
    print("?? C++ quant engine not available. Falling back to Python backend.")

__version__ = "1.0.0"


class CppQuant:
    def __init__(self):
        if not _AVAILABLE:
            raise RuntimeError("C++ engine not available. Compile it first.")
        self.engine = _core.QuantEngine()
        self._loaded = False
        self._data_info = ""

    def load_csv_files(self, path_pattern: str):
        """Load multiple CSV files using glob pattern.
        Example: 'data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv'
        """
        files = glob.glob(path_pattern)
        if not files:
            raise FileNotFoundError(f"No files found for pattern: {path_pattern}")
        success = self.engine.load_data(files)
        if success:
            self._loaded = True
            self._data_info = self.engine.get_data_info()
        return success

    def load_from_dataframe(self, df: pd.DataFrame):
        """Load data from pandas DataFrame with columns: open, high, low, close, volume.
        Index must be datetime.
        """
        if df.empty:
            raise ValueError("DataFrame is empty")
        timestamps = df.index.astype(np.int64) // 10**9  # convert to seconds
        success = self.engine.load_data_from_vectors(
            timestamps.tolist(),
            df["open"].tolist(),
            df["high"].tolist(),
            df["low"].tolist(),
            df["close"].tolist(),
            df["volume"].tolist() if "volume" in df.columns else [0] * len(df),
        )
        if success:
            self._loaded = True
            self._data_info = self.engine.get_data_info()
        return success

    def set_timeframe(self, minutes: int):
        if self._loaded:
            self.engine.set_timeframe(minutes)

    def run_sma(self, short=10, long=30) -> dict:
        if not self._loaded:
            raise RuntimeError("Load data first")
        res = self.engine.run_sma(short, long)
        return self._to_dict(res)

    def run_rsi(self, period=14, oversold=30, overbought=70) -> dict:
        if not self._loaded:
            raise RuntimeError("Load data first")
        res = self.engine.run_rsi(period, oversold, overbought)
        return self._to_dict(res)

    def run_macd(self, fast=12, slow=26, signal=9, sma_filter=200) -> dict:
        if not self._loaded:
            raise RuntimeError("Load data first")
        res = self.engine.run_macd(fast, slow, signal, sma_filter)
        return self._to_dict(res)

    def run_all(self) -> dict:
        if not self._loaded:
            raise RuntimeError("Load data first")
        results = self.engine.run_all_strategies()
        return {k: self._to_dict(v) for k, v in results.items()}

    def monte_carlo_pvalue(self, result: dict, num_simulations=10000) -> float:
        # Need to reconstruct BacktestResult object
        # This is simplified; better to pass the raw result object
        raise NotImplementedError("Use engine directly for Monte Carlo")

    def optimize_sma(self, short_min=5, short_max=30, long_min=20, long_max=100) -> dict:
        if not self._loaded:
            raise RuntimeError("Load data first")
        res = self.engine.optimize_sma(short_min, short_max, long_min, long_max)
        return {k: v for k, v in res.items()}

    def get_mean(self, data):
        """Calculate mean using C++."""
        if not data:
            return 0.0
        return _core.mean(data)

    def get_stddev(self, data):
        """Calculate standard deviation using C++."""
        if not data:
            return 0.0
        return _core.stddev(data)

    def get_correlation(self, x, y):
        """Calculate correlation using C++."""
        if len(x) != len(y) or not x:
            return 0.0
        return _core.correlation(x, y)

    def get_bootstrap_ci(self, data, iterations=1000, ci=0.95):
        """Bootstrap CI for mean using C++ (fast!)."""
        if not data:
            return (0.0, 0.0)
        return _core.bootstrap_ci(data, iterations, ci)

    def get_bootstrap_winrate_ci(self, pnls, iterations=1000, ci=0.95):
        """Bootstrap CI for winrate using C++ (fast!)."""
        if not pnls:
            return (0.0, 0.0)
        return _core.bootstrap_winrate_ci(pnls, iterations, ci)

    def get_info(self) -> str:
        return self._data_info

    @staticmethod
    def _to_dict(res):
        return {
            "num_trades": res.num_trades,
            "winrate": res.winrate,
            "total_return": res.total_return,
            "sharpe_ratio": res.sharpe_ratio,
            "max_drawdown": res.max_drawdown,
            "avg_win": res.avg_win,
            "avg_loss": res.avg_loss,
            "profit_factor": res.profit_factor,
            "trades": [
                (t.entry_time, t.exit_time, t.entry_price, t.exit_price, t.pnl, t.is_win)
                for t in res.trades
            ],
        }
