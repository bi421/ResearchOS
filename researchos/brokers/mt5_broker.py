import pandas as pd
import numpy as np

try:
    import MetaTrader5 as mt5

    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("❌ MetaTrader5 module not installed. Run: pip install MetaTrader5")


class MT5Broker:
    """
    MetaTrader 5 trading wrapper for ResearchOS.
    Requires MT5 terminal to be running and logged in.
    """

    def __init__(self, symbol: str = "XAUUSD", magic: int = 123456):
        self.symbol = symbol
        self.magic = magic
        self.initialized = False
        self.symbol_info = None

        if not MT5_AVAILABLE:
            raise RuntimeError("MetaTrader5 module not available.")

        # Initialize MT5 connection
        if not mt5.initialize():
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

        self.initialized = True
        print(f"✅ MT5 connected. Terminal: {mt5.terminal_info().name}")

        # Get symbol info
        self.symbol_info = mt5.symbol_info(symbol)
        if self.symbol_info is None:
            raise RuntimeError(f"Symbol {symbol} not found. Add it to Market Watch.")

        print(f"✅ Symbol {symbol} loaded. Digits: {self.symbol_info.digits}")

    def get_account_info(self) -> dict:
        """Get account balance, equity, margin."""
        acc = mt5.account_info()
        if acc is None:
            return {}
        return {
            "balance": acc.balance,
            "equity": acc.equity,
            "margin": acc.margin,
            "free_margin": acc.margin_free,
            "profit": acc.profit,
        }

    def get_positions(self) -> pd.DataFrame:
        """Get all open positions for the magic number."""
        positions = mt5.positions_get(magic=self.magic)
        if positions is None or len(positions) == 0:
            return pd.DataFrame()
        data = []
        for pos in positions:
            data.append(
                {
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL",
                    "volume": pos.volume,
                    "price_open": pos.price_open,
                    "price_current": pos.price_current,
                    "profit": pos.profit,
                    "sl": pos.sl,
                    "tp": pos.tp,
                    "comment": pos.comment,
                }
            )
        return pd.DataFrame(data)

    def get_current_price(self) -> tuple:
        """Get current bid and ask prices."""
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            return 0.0, 0.0
        return tick.bid, tick.ask

    def calculate_lot_size(
        self, risk_percent: float = 0.02, stop_loss_points: int = 200, account_balance: float = None
    ) -> float:
        """
        Calculate lot size based on risk % and stop loss points.
        For XAUUSD: 1 lot = 100 units, 0.01 lot = 1 unit.
        stop_loss_points: e.g., 200 points =  per 0.01 lot.
        """
        if account_balance is None:
            acc = mt5.account_info()
            if acc is None:
                return 0.01
            account_balance = acc.balance

        # Risk amount in dollars
        risk_amount = account_balance * risk_percent

        # Value per point for 0.01 lot is  for XAUUSD
        # For other symbols, we should calculate, but for simplicity:
        pip_value = 1.0  # 0.01 lot XAUUSD =  per point

        lot_size = risk_amount / (stop_loss_points * pip_value)

        # Round down to nearest 0.01
        lot_size = np.floor(lot_size * 100) / 100

        # Minimum lot size
        min_lot = 0.01
        if self.symbol_info:
            min_lot = max(min_lot, self.symbol_info.volume_min)

        return max(min_lot, lot_size)

    def place_market_order(
        self,
        action: str,  # "BUY" or "SELL"
        volume: float,
        sl_price: float = None,
        tp_price: float = None,
        deviation: int = 20,
        comment: str = "ResearchOS",
    ) -> dict:
        """
        Place a market order (BUY or SELL).
        Returns order result dictionary.
        """
        if not self.initialized:
            raise RuntimeError("MT5 not initialized.")

        bid, ask = self.get_current_price()

        if action == "BUY":
            price = ask
            order_type = mt5.ORDER_TYPE_BUY
        elif action == "SELL":
            price = bid
            order_type = mt5.ORDER_TYPE_SELL
        else:
            raise ValueError("action must be 'BUY' or 'SELL'")

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": deviation,
            "magic": self.magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        if sl_price is not None:
            request["sl"] = sl_price
        if tp_price is not None:
            request["tp"] = tp_price

        result = mt5.order_send(request)
        if result is None:
            return {"error": f"Order failed: {mt5.last_error()}"}

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {
                "error": f"Order failed: {result.retcode} - {result.comment}",
                "retcode": result.retcode,
                "comment": result.comment,
            }

        return {
            "ticket": result.order,
            "volume": result.volume,
            "price": result.price,
            "sl": result.sl,
            "tp": result.tp,
            "comment": result.comment,
            "retcode": result.retcode,
        }

    def close_position(self, ticket: int) -> dict:
        """Close a position by ticket number."""
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            return {"error": "Position not found"}
        pos = position[0]

        if pos.type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(pos.symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(pos.symbol).ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": self.magic,
            "comment": "Close by ResearchOS",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result is None:
            return {"error": f"Close failed: {mt5.last_error()}"}

        return {"retcode": result.retcode, "comment": result.comment, "ticket": result.order}

    def close_all_positions(self):
        """Close all positions with this magic number."""
        positions = mt5.positions_get(magic=self.magic)
        if positions is None:
            return
        for pos in positions:
            self.close_position(pos.ticket)

    def get_last_bars(self, timeframe: str = "4h", count: int = 300) -> pd.DataFrame:
        """
        Fetch OHLCV data directly from MT5.
        """
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

        rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, count)
        if rates is None:
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df = df.rename(
            columns={
                "time": "datetime",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "tick_volume": "volume",
            }
        )
        df = df.set_index("datetime")[["open", "high", "low", "close", "volume"]]
        return df

    def shutdown(self):
        """Shutdown MT5 connection."""
        mt5.shutdown()
        print("🔌 MT5 disconnected.")


if __name__ == "__main__":
    # Test connection
    broker = MT5Broker(symbol="XAUUSD")
    print("Account:", broker.get_account_info())
    print("Price:", broker.get_current_price())
    print("Positions:", broker.get_positions())
    broker.shutdown()
