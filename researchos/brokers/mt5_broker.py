from __future__ import annotations

import pandas as pd

try:
    import MetaTrader5 as mt5

    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None


class MT5Broker:
    """
    Read-only MetaTrader 5 market-data adapter for ResearchOS.

    Constitutional invariant:
        ResearchOS MUST NOT execute broker trades.

    This adapter may:
        - connect to MT5
        - read account metadata
        - read open positions
        - read current prices
        - read historical OHLCV
        - shutdown the MT5 connection

    It MUST NOT:
        - create orders
        - modify orders
        - close positions
        - delete orders
        - perform broker execution
    """

    def __init__(
        self,
        symbol: str = "XAUUSD",
    ):
        self.symbol = symbol
        self.initialized = False
        self.symbol_info = None

        if not MT5_AVAILABLE:
            raise RuntimeError("MetaTrader5 module not available.")

        if not mt5.initialize():
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

        self.initialized = True

        terminal = mt5.terminal_info()

        if terminal is not None:
            print(f"MT5 connected. Terminal: {terminal.name}")

        self.symbol_info = mt5.symbol_info(symbol)

        if self.symbol_info is None:
            self.shutdown()
            raise RuntimeError(f"Symbol {symbol} not found. Add it to Market Watch.")

        print(f"Symbol {symbol} loaded. Digits: {self.symbol_info.digits}")

    def get_account_info(self) -> dict:
        """
        Read account information.

        This method does not perform any account mutation.
        """
        self._require_initialized()

        account = mt5.account_info()

        if account is None:
            return {}

        return {
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "free_margin": account.margin_free,
            "profit": account.profit,
            "currency": getattr(
                account,
                "currency",
                None,
            ),
            "leverage": getattr(
                account,
                "leverage",
                None,
            ),
        }

    def get_positions(self) -> pd.DataFrame:
        """
        Read currently open positions.

        No position mutation is performed.
        """
        self._require_initialized()

        positions = mt5.positions_get()

        if positions is None or len(positions) == 0:
            return pd.DataFrame()

        data = []

        for position in positions:
            if position.type == mt5.POSITION_TYPE_BUY:
                position_type = "BUY"
            elif position.type == mt5.POSITION_TYPE_SELL:
                position_type = "SELL"
            else:
                position_type = str(position.type)

            data.append(
                {
                    "ticket": position.ticket,
                    "symbol": position.symbol,
                    "type": position_type,
                    "volume": position.volume,
                    "price_open": position.price_open,
                    "price_current": position.price_current,
                    "profit": position.profit,
                    "sl": position.sl,
                    "tp": position.tp,
                    "comment": position.comment,
                    "time": getattr(
                        position,
                        "time",
                        None,
                    ),
                }
            )

        return pd.DataFrame(data)

    def get_current_price(self) -> tuple[float, float]:
        """
        Read current bid/ask price.
        """
        self._require_initialized()

        tick = mt5.symbol_info_tick(self.symbol)

        if tick is None:
            return 0.0, 0.0

        return (
            float(tick.bid),
            float(tick.ask),
        )

    def get_last_bars(
        self,
        timeframe: str = "4h",
        count: int = 300,
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data directly from MT5.

        No trading operation is performed.
        """
        self._require_initialized()

        if count <= 0:
            raise ValueError("count must be greater than zero")

        tf_map = {
            "1m": mt5.TIMEFRAME_M1,
            "5m": mt5.TIMEFRAME_M5,
            "15m": mt5.TIMEFRAME_M15,
            "30m": mt5.TIMEFRAME_M30,
            "1h": mt5.TIMEFRAME_H1,
            "4h": mt5.TIMEFRAME_H4,
            "1d": mt5.TIMEFRAME_D1,
        }

        tf = tf_map.get(timeframe)

        if tf is None:
            raise ValueError(f"Invalid timeframe: {timeframe}")

        rates = mt5.copy_rates_from_pos(
            self.symbol,
            tf,
            0,
            count,
        )

        if rates is None:
            return pd.DataFrame()

        if len(rates) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(rates)

        df["time"] = pd.to_datetime(
            df["time"],
            unit="s",
            utc=True,
        )

        df = df.rename(
            columns={
                "time": "datetime",
                "tick_volume": "volume",
            }
        )

        required_columns = [
            "datetime",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        missing = [column for column in required_columns if column not in df.columns]

        if missing:
            raise RuntimeError(f"MT5 data missing columns: {missing}")

        return df.set_index("datetime")[
            [
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        ]

    def shutdown(self) -> None:
        """
        Shutdown the read-only MT5 connection.
        """
        if MT5_AVAILABLE and self.initialized:
            mt5.shutdown()

        self.initialized = False

    def _require_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("MT5 is not initialized.")


if __name__ == "__main__":
    broker = MT5Broker(symbol="XAUUSD")

    try:
        print("Account:", broker.get_account_info())
        print("Price:", broker.get_current_price())
        print("Positions:")
        print(broker.get_positions())
        print("Bars:")
        print(broker.get_last_bars())
    finally:
        broker.shutdown()
