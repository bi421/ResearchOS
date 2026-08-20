"""
Backtest engine for strategies.
"""
from typing import List, Any
from dataclasses import dataclass
import numpy as np

@dataclass
class BacktestResult:
    total_return: float          # Нийт өгөөж (жишээ нь 0.33 → 33%)
    sharpe_ratio: float          # Sharpe харьцаа
    max_drawdown: float          # Хамгийн их уналт (жишээ нь -0.25 → -25%)
    win_rate: float              # Ялалтын хувь (0-1)
    num_trades: int              # Нийт арилжааны тоо
    signals: List[Any]           # Дохионууд

class BacktestEngine:
    def __init__(self, initial_capital: float = 100000.0,
                 commission: float = 0.001,
                 slippage: float = 0.0005):
        """
        :param initial_capital: Эхний хөрөнгө
        :param commission: Нэг арилжааны шимтгэл (хувь, 0.001 = 0.1%)
        :param slippage: Нэг арилжааны гулсалт (хувь, 0.0005 = 0.05%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

    def run(self, prices: List[float], strategy) -> BacktestResult:
        """
        Бэктест ажиллуулах.
        :param prices: Үнийн жагсаалт (жишээ нь өдрийн хаалтын үнэ)
        :param strategy: Стратегийн обьект, `.generate_signals(prices)` методтой
        """
        signals = strategy.generate_signals(prices)
        if not signals:
            return BacktestResult(0.0, 0.0, 0.0, 0.0, 0, signals)

        capital = self.initial_capital
        position = 0.0
        trades = []          # (action, price, timestamp, size, net_value)
        equity_curve = [capital]   # Хөрөнгийн өөрчлөлтийн график

        for signal in signals:
            price = signal.price
            timestamp = getattr(signal, 'timestamp', None)

            if signal.action == "BUY" and position == 0:
                # Худалдан авах: шимтгэл + гулсалтыг харгалзан
                cost_per_unit = price * (1 + self.commission + self.slippage)
                size = capital / cost_per_unit
                if size > 0:
                    cost_total = size * cost_per_unit
                    capital -= cost_total
                    position = size
                    trades.append(("BUY", price, timestamp, size, cost_total))

            elif signal.action == "SELL" and position > 0:
                # Зарах: шимтгэл + гулсалтыг хасах
                revenue_per_unit = price * (1 - self.commission - self.slippage)
                revenue_total = position * revenue_per_unit
                capital += revenue_total
                trades.append(("SELL", price, timestamp, position, revenue_total))
                position = 0.0

            # Хөрөнгийн үнэлгээг (equity) хадгалах
            current_equity = capital + position * price
            equity_curve.append(current_equity)

        # Хэрэв позиц үлдсэн бол эцсийн үнээр хаах
        if position > 0 and prices:
            closing_price = prices[-1]
            revenue_per_unit = closing_price * (1 - self.commission - self.slippage)
            capital += position * revenue_per_unit
            trades.append(("CLOSE", closing_price, None, position, position * revenue_per_unit))
            position = 0.0

        final_value = capital
        total_return = (final_value - self.initial_capital) / self.initial_capital

        # 📊 Sharpe ratio (жилийнжүүлээгүй, өдрийн өгөөжөөр)
        equity = np.array(equity_curve)
        returns = np.diff(equity) / equity[:-1]
        if len(returns) > 1:
            sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)  # өдөр тутмын
        else:
            sharpe = 0.0

        # 📉 Max drawdown
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak
        max_drawdown = -np.max(drawdown) if len(drawdown) > 0 else 0.0

        # 📈 Win rate (зөвхөн BUY-SELL хосууд)
        buy_trades = [t for t in trades if t[0] == "BUY"]
        sell_trades = [t for t in trades if t[0] == "SELL"]
        # Хослох (BUY-ийн дараа SELL, эсвэл эсрэгээр)
        profit_trades = 0
        total_pairs = min(len(buy_trades), len(sell_trades))
        for i in range(total_pairs):
            buy_price = buy_trades[i][1]
            sell_price = sell_trades[i][1] if i < len(sell_trades) else prices[-1]
            if sell_price > buy_price:
                profit_trades += 1
        win_rate = profit_trades / total_pairs if total_pairs > 0 else 0.0

        return BacktestResult(
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            num_trades=total_pairs,
            signals=signals
        )
