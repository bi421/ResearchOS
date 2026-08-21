import yfinance as yf
from datetime import datetime, timedelta


class LiveCandleValidator:
    def __init__(self, symbol: str, yf_symbol: str):
        self.symbol = symbol
        self.yf_symbol = yf_symbol
        self.ticker = yf.Ticker(yf_symbol)

    def get_live_candle(self) -> dict:
        try:
            data = self.ticker.history(period="1d", interval="1m")
            if data.empty:
                return None
            last_candle = data.iloc[-1]
            return {
                "timestamp": last_candle.name,
                "open": last_candle["Open"],
                "high": last_candle["High"],
                "low": last_candle["Low"],
                "close": last_candle["Close"],
                "volume": last_candle["Volume"],
            }
        except Exception as e:
            print(f"⚠️ Live candle error: {e}")
            return None

    def get_historical_candle(self, date: datetime = None) -> dict:
        if date is None:
            date = datetime.now() - timedelta(days=1)
        try:
            data = self.ticker.history(
                start=date.strftime("%Y-%m-%d"),
                end=(date + timedelta(days=1)).strftime("%Y-%m-%d"),
                interval="1d",
            )
            if data.empty:
                return None
            candle = data.iloc[-1]
            return {
                "timestamp": candle.name,
                "open": candle["Open"],
                "high": candle["High"],
                "low": candle["Low"],
                "close": candle["Close"],
                "volume": candle["Volume"],
            }
        except Exception as e:
            print(f"⚠️ Historical candle error: {e}")
            return None

    def compare_candles(self, live: dict, historical: dict) -> dict:
        if live is None or historical is None:
            return {"status": "ERROR", "message": "Candle data missing"}
        diff_pct = (
            (live["close"] - historical["close"]) / historical["close"] * 100
            if historical["close"] != 0
            else 0
        )
        volume_ratio = live["volume"] / historical["volume"] if historical["volume"] != 0 else 0
        verification = {"status": "VERIFIED", "message": "Candles are consistent"}
        if abs(diff_pct) > 5:
            verification = {
                "status": "WARNING",
                "message": f"Close price differs by {diff_pct:.2f}%",
            }
        elif volume_ratio > 3:
            verification = {
                "status": "NOTICE",
                "message": f"Volume is {volume_ratio:.1f}x higher than historical",
            }
        return {
            "live": live,
            "historical": historical,
            "diff_pct": diff_pct,
            "volume_ratio": volume_ratio,
            "verification": verification,
        }

    def generate_report(self, comparison: dict) -> str:
        return f"""
# 🕯️ Live vs Historical Candle Validation Report
**Symbol:** {self.symbol} ({self.yf_symbol})
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📊 Live Candle
| Metric | Value |
|--------|-------|
| Timestamp | {comparison["live"]["timestamp"]} |
| Open | ${comparison["live"]["open"]:.2f} |
| High | ${comparison["live"]["high"]:.2f} |
| Low | ${comparison["live"]["low"]:.2f} |
| Close | ${comparison["live"]["close"]:.2f} |
| Volume | {comparison["live"]["volume"]:,.0f} |

## 📊 Historical Candle
| Metric | Value |
|--------|-------|
| Timestamp | {comparison["historical"]["timestamp"]} |
| Open | ${comparison["historical"]["open"]:.2f} |
| High | ${comparison["historical"]["high"]:.2f} |
| Low | ${comparison["historical"]["low"]:.2f} |
| Close | ${comparison["historical"]["close"]:.2f} |
| Volume | {comparison["historical"]["volume"]:,.0f} |

## 📈 Comparison
| Metric | Difference |
|--------|------------|
| Close Price | {comparison["diff_pct"]:+.2f}% |
| Volume Ratio | {comparison["volume_ratio"]:.2f}x |

## ✅ Verification Status
**Status:** {comparison["verification"]["status"]}
**Message:** {comparison["verification"]["message"]}
"""


if __name__ == "__main__":
    print("🕯️ Live Candle Validator")
    print("=" * 40)
    validator = LiveCandleValidator("XAUUSD", "GC=F")
    live = validator.get_live_candle()
    historical = validator.get_historical_candle()
    if live and historical:
        comparison = validator.compare_candles(live, historical)
        report = validator.generate_report(comparison)
        with open("candle_validation_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("\n✅ Validation report saved: candle_validation_report.md")
        print(f"📊 Status: {comparison['verification']['status']}")
        print(f"📝 Message: {comparison['verification']['message']}")
        print(
            f"💹 Live Close: ${live['close']:.2f} vs Historical Close: ${historical['close']:.2f}"
        )
    else:
        print("❌ Failed to get candle data")
