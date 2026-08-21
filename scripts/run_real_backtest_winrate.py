import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")


class RealBacktestWinrate:
    def __init__(self, symbol="GC=F", start_date="2020-01-01", end_date=None):
        self.symbol = symbol
        self.start = start_date
        self.end = end_date or datetime.now().strftime("%Y-%m-%d")
        self.data = None
        self.results = {}

    def fetch_data(self):
        """Бодит өгөгдөл татах"""
        print(f"📡 {self.symbol} өгөгдөл татаж байна ({self.start} → {self.end})")
        ticker = yf.Ticker(self.symbol)
        self.data = ticker.history(start=self.start, end=self.end)
        if self.data.empty:
            print("❌ Өгөгдөл олдсонгүй")
            return False
        print(f"✅ {len(self.data)} ширхэг candle татагдлаа")
        return True

    def run_backtest(self, strategy_name, entry_condition, exit_condition):
        """Бэктест хийх үндсэн функц"""
        df = self.data.copy()
        df["signal"] = 0
        df["position"] = 0
        trades = []

        in_position = False
        entry_price = 0
        entry_time = None

        for i in range(1, len(df)):
            current_time = df.index[i]
            current_price = df["Close"].iloc[i]

            # Entry
            if not in_position and entry_condition(df, i):
                in_position = True
                entry_price = current_price
                entry_time = current_time

            # Exit
            elif in_position and exit_condition(df, i):
                in_position = False
                exit_price = current_price
                pnl = (exit_price - entry_price) / entry_price
                trades.append(
                    {
                        "entry_time": entry_time,
                        "exit_time": current_time,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl": pnl,
                        "direction": "LONG",  # BUY only for simplicity
                    }
                )

        # Хэрэв сүүлчийн позиц хаагдаагүй бол хаах
        if in_position:
            exit_price = df["Close"].iloc[-1]
            pnl = (exit_price - entry_price) / entry_price
            trades.append(
                {
                    "entry_time": entry_time,
                    "exit_time": df.index[-1],
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "direction": "LONG",
                }
            )

        # Статистик тооцоолох
        if trades:
            df_trades = pd.DataFrame(trades)
            winrate = (df_trades["pnl"] > 0).sum() / len(df_trades) * 100
            avg_win = (
                df_trades[df_trades["pnl"] > 0]["pnl"].mean()
                if (df_trades["pnl"] > 0).sum() > 0
                else 0
            )
            avg_loss = (
                df_trades[df_trades["pnl"] < 0]["pnl"].mean()
                if (df_trades["pnl"] < 0).sum() > 0
                else 0
            )
            profit_factor = (
                abs(
                    (df_trades[df_trades["pnl"] > 0]["pnl"].sum())
                    / (df_trades[df_trades["pnl"] < 0]["pnl"].sum())
                )
                if (df_trades["pnl"] < 0).sum() > 0
                else np.inf
            )
            total_return = (1 + df_trades["pnl"]).prod() - 1
            sharpe = (
                df_trades["pnl"].mean() / df_trades["pnl"].std() * np.sqrt(252)
                if df_trades["pnl"].std() != 0
                else 0
            )

            self.results[strategy_name] = {
                "trades": len(trades),
                "winrate": winrate,
                "avg_win": avg_win * 100,
                "avg_loss": avg_loss * 100,
                "profit_factor": profit_factor,
                "total_return": total_return * 100,
                "sharpe": sharpe,
            }
        else:
            self.results[strategy_name] = {
                "trades": 0,
                "winrate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "profit_factor": 0,
                "total_return": 0,
                "sharpe": 0,
            }

        return trades

    def strategy_sma_crossover(self):
        """SMA 10/30 Crossover"""
        print("📊 [1/3] SMA Crossover стратегийн бэктест хийж байна...")
        df = self.data.copy()
        df["SMA_10"] = df["Close"].rolling(10).mean()
        df["SMA_30"] = df["Close"].rolling(30).mean()

        def entry_condition(data, i):
            if i < 30:
                return False
            return (data["SMA_10"].iloc[i] > data["SMA_30"].iloc[i]) and (
                data["SMA_10"].iloc[i - 1] <= data["SMA_30"].iloc[i - 1]
            )

        def exit_condition(data, i):
            if i < 30:
                return False
            return (data["SMA_10"].iloc[i] < data["SMA_30"].iloc[i]) and (
                data["SMA_10"].iloc[i - 1] >= data["SMA_30"].iloc[i - 1]
            )

        return self.run_backtest("SMA Crossover", entry_condition, exit_condition)

    def strategy_rsi_mean_reversion(self):
        """RSI Mean Reversion (14 period)"""
        print("📊 [2/3] RSI Mean Reversion стратегийн бэктест хийж байна...")
        df = self.data.copy()
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        def entry_condition(data, i):
            if i < 14:
                return False
            return data["RSI"].iloc[i] < 30  # Oversold

        def exit_condition(data, i):
            if i < 14:
                return False
            return data["RSI"].iloc[i] > 70  # Overbought

        return self.run_backtest("RSI Mean Reversion", entry_condition, exit_condition)

    def strategy_macd_sma_filter(self):
        """MACD + SMA 200 фильтр"""
        print("📊 [3/3] MACD + SMA Filter стратегийн бэктест хийж байна...")
        df = self.data.copy()
        exp1 = df["Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
        df["SMA_200"] = df["Close"].rolling(200).mean()

        def entry_condition(data, i):
            if i < 200:
                return False
            # MACD bullish crossover + price above SMA 200
            return (
                (data["MACD_Hist"].iloc[i] > 0)
                and (data["MACD_Hist"].iloc[i - 1] <= 0)
                and (data["Close"].iloc[i] > data["SMA_200"].iloc[i])
            )

        def exit_condition(data, i):
            if i < 200:
                return False
            # MACD bearish crossover OR price below SMA 200
            return (data["MACD_Hist"].iloc[i] < 0) or (
                data["Close"].iloc[i] < data["SMA_200"].iloc[i]
            )

        return self.run_backtest("MACD + SMA Filter", entry_condition, exit_condition)

    def print_summary(self):
        """Үр дүнг хүснэгт хэлбэрээр харуулах"""
        print("\n" + "=" * 70)
        print("🏆 БЭКТЕСТИЙН ҮР ДҮН (БОДИТ ВИНРЭЙТ)")
        print("=" * 70)
        print(f"📅 Хугацаа: {self.start} → {self.end}")
        print(f"📊 Хөрөнгө: {self.symbol}")
        print("=" * 70)

        df_summary = pd.DataFrame(self.results).T
        print(df_summary.round(2).to_string())

        # Хамгийн сайн стратегийг тодорхойлох
        if not self.results.empty:
            best = max(self.results.items(), key=lambda x: x[1]["sharpe"])
            print("\n" + "=" * 70)
            print(f"🔥 ХАМГИЙН САЙН СТРАТЕГИ: {best[0]}")
            print(f"   • Winrate: {best[1]['winrate']:.1f}%")
            print(f"   • Sharpe Ratio: {best[1]['sharpe']:.2f}")
            print(f"   • Нийт өгөөж: {best[1]['total_return']:.1f}%")
            print("=" * 70)

    def save_report(self):
        """Тайланг файлд хадгалах"""
        report = f"""
# 📊 БОДИТ ВИНРЭЙТ БЭКТЕСТИЙН ТАЙЛАН
**Хөрөнгө:** {self.symbol}
**Хугацаа:** {self.start} → {self.end}
**Үүсгэсэн:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 📈 БЭКТЕСТИЙН ҮР ДҮН

| Стратеги | Арилжаа | Winrate | Дунд ашиг | Дунд алдагдал | Profit Factor | Нийт өгөөж | Sharpe |
|----------|---------|---------|-----------|---------------|---------------|------------|--------|
"""
        for name, res in self.results.items():
            report += f"| {name} | {res['trades']} | {res['winrate']:.1f}% | {res['avg_win']:.2f}% | {res['avg_loss']:.2f}% | {res['profit_factor']:.2f} | {res['total_return']:.1f}% | {res['sharpe']:.2f} |\n"

        # Хамгийн сайн стратеги
        if self.results:
            best = max(self.results.items(), key=lambda x: x[1]["sharpe"])
            report += f"""
## 🔥 ХАМГИЙН САЙН СТРАТЕГИ
**{best[0]}**
- Winrate: {best[1]["winrate"]:.1f}%
- Sharpe Ratio: {best[1]["sharpe"]:.2f}
- Нийт өгөөж: {best[1]["total_return"]:.1f}%

## 💡 ЗӨВЛӨМЖ
- Хэрэв Winrate < 50% бол стратегийг сайжруулах хэрэгтэй
- Profit Factor > 1.5 бол ашигтай стратеги
- Sharpe > 1 бол эрсдэлд тохируулсан ашиг сайтай
"""

        with open("backtest_winrate_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("\n✅ Тайлан хадгалагдлаа: backtest_winrate_report.md")


# === MAIN ===
if __name__ == "__main__":
    print("🚀 БОДИТ ВИНРЭЙТ БЭКТЕСТ")
    print("=" * 40)

    system = RealBacktestWinrate(symbol="GC=F", start_date="2020-01-01")

    if system.fetch_data():
        system.strategy_sma_crossover()
        system.strategy_rsi_mean_reversion()
        system.strategy_macd_sma_filter()
        system.print_summary()
        system.save_report()
    else:
        print("❌ Өгөгдөл татахад алдаа гарлаа")
