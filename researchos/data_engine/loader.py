"""
Unified Data Loader - Multi-Asset Entry Point for ResearchOS

This module provides a single, asset-agnostic interface to load market data.
It uses the existing CsvLoader under the hood but resolves file paths
based on the symbol and timeframe, making the rest of the system completely
independent of XAUUSD or any specific asset.

Usage:
    from researchos.data_engine.loader import DataLoader
    
    # Load XAUUSD (legacy)
    candles = DataLoader.load("xauusd", "h1")
    
    # Future: Load crypto
    # candles = DataLoader.load("btcusdt", "1h", source="binance")
"""

from pathlib import Path
from typing import List, Optional, Dict, Any

from researchos.data_engine.candle import Candle
from researchos.data_engine.csv_loader import CsvLoader, FORMAT_MT5, FORMAT_TRADINGVIEW


class DataLoader:
    """
    Unified data loader for any asset class.
    
    Resolves file paths from a configuration registry and delegates
    parsing to the existing CsvLoader.
    """
    
    # Registry: Maps symbol -> configuration for file resolution
    _CONFIG: Dict[str, Dict[str, Any]] = {
        "xauusd": {
            "base_path": "data/curated/xauusd",
            "format": FORMAT_MT5,
            "file_pattern": "{symbol}_{timeframe}_*.csv",  # e.g., xauusd_h1_2021_2025_mt5.csv
        },
        # 🔮 Ирээдүйд крипто нэмэхэд энд нэмэх:
        # "btcusdt": {
        #     "base_path": "data/curated/binance",
        #     "format": FORMAT_TRADINGVIEW,
        #     "file_pattern": "{symbol}_{timeframe}.csv",
        # },
        # "pepeusdt": {
        #     "base_path": "data/curated/binance",
        #     "format": FORMAT_TRADINGVIEW,
        #     "file_pattern": "{symbol}_{timeframe}.csv",
        # },
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._CONFIG
        self._csv_loader = CsvLoader()

    @classmethod
    def load(
        cls,
        symbol: str,
        timeframe: str,
        file_path: Optional[str] = None,
        force_format: Optional[str] = None,
        **kwargs
    ) -> List[Candle]:
        """
        Universal load function for all assets.

        Args:
            symbol: Asset symbol (e.g., 'xauusd', 'btcusdt').
            timeframe: Timeframe string (e.g., '1h', '1d', '1m').
            file_path: Optional explicit path (overrides auto-resolution).
            force_format: Force 'mt5' or 'tradingview'. Default is auto-detect.
            **kwargs: Additional arguments passed to CsvLoader methods.

        Returns:
            List of Candle objects.

        Raises:
            FileNotFoundError: If data file cannot be located.
            ValueError: If symbol is not registered.
        """
        symbol = symbol.lower()
        
        # 1. If path is provided explicitly, use it directly
        if file_path is not None:
            return cls._load_from_path(file_path, symbol, timeframe, force_format, **kwargs)
        
        # 2. Resolve path from configuration
        config = cls._CONFIG.get(symbol)
        if not config:
            raise ValueError(
                f"Symbol '{symbol}' is not registered. "
                f"Supported symbols: {list(cls._CONFIG.keys())}. "
                "Add it to DataLoader._CONFIG first."
            )
        
        base = Path(config["base_path"])
        if not base.exists():
            raise FileNotFoundError(f"Data directory not found: {base}")
        
        # Build pattern and search for files
        pattern = config["file_pattern"].format(symbol=symbol, timeframe=timeframe)
        matches = list(base.glob(pattern))
        
        if not matches:
            # Fallback: Try broader glob (just in case filename structure is slightly different)
            fallback_pattern = f"*{timeframe}*.csv"
            fallback_matches = list(base.glob(fallback_pattern))
            if fallback_matches:
                matches = fallback_matches
        
        if not matches:
            raise FileNotFoundError(
                f"No file found for {symbol} {timeframe} in {base}. "
                f"Searched pattern: {pattern}"
            )
        
        # Use the first match (or enhance later to pick the most recent)
        resolved_path = str(matches[0])
        print(f"[DataLoader] Resolved path: {resolved_path}")
        
        return cls._load_from_path(
            resolved_path, symbol, timeframe, 
            force_format or config.get("format"), 
            **kwargs
        )

    @classmethod
    def _load_from_path(
        cls,
        path: str,
        symbol: str,
        timeframe: str,
        format_type: Optional[str],
        **kwargs
    ) -> List[Candle]:
        """Delegate to CsvLoader with the given path."""
        loader = CsvLoader()
        
        # If format is forced, use specific loader
        if format_type == FORMAT_MT5:
            return loader.load_mt5_candles(path, symbol=symbol, timeframe=timeframe, **kwargs)
        elif format_type == FORMAT_TRADINGVIEW:
            return loader.load_tradingview_candles(path, symbol=symbol, timeframe=timeframe, **kwargs)
        else:
            # Auto-detect format and columns (handles generic, mt5, tradingview)
            return loader.load_candles_auto(path, symbol=symbol, timeframe=timeframe, **kwargs)

    @classmethod
    def register(cls, symbol: str, config: Dict[str, Any]) -> None:
        """Dynamically register a new asset (useful for future crypto)."""
        cls._CONFIG[symbol.lower()] = config

    @classmethod
    def list_supported(cls) -> List[str]:
        """List all registered symbols."""
        return list(cls._CONFIG.keys())
