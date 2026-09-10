"""Research-only latest-candle consistency diagnostic.

The previous implementation compared a 1-minute candle with a daily candle,
then called the result "VERIFIED".  That comparison was dimensionally invalid.
This version compares like-for-like completed daily candles and never claims
independent source verification.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import yfinance as yf

from researchos.data_engine.asset_identity import assert_xauusd_identity


class LiveCandleValidator:
    def __init__(self, symbol: str, yf_symbol: str):
        self.symbol = symbol
        self.yf_symbol = yf_symbol
        assert_xauusd_identity(symbol, yf_symbol)
        self.ticker = yf.Ticker(yf_symbol)

    @staticmethod
    def _candle(data) -> dict | None:
        if data.empty:
            return None
        row = data.iloc[-1]
        return {
            "timestamp": row.name,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": float(row["Volume"]) if "Volume" in data.columns else 0.0,
        }

    def get_live_candle(self) -> dict | None:
        """Return the latest completed daily candle from the engineering proxy."""
        try:
            data = self.ticker.history(period="10d", interval="1d", auto_adjust=False)
            return self._candle(data)
        except Exception as exc:
            print(f"Latest candle error: {exc}")
            return None

    def get_historical_candle(self, date: datetime | None = None) -> dict | None:
        """Return the requested completed daily candle from the same source."""
        if date is None:
            date = datetime.now(timezone.utc) - timedelta(days=1)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        start = date.astimezone(timezone.utc).date()
        end = start + timedelta(days=1)
        try:
            data = self.ticker.history(
                start=start.isoformat(),
                end=end.isoformat(),
                interval="1d",
                auto_adjust=False,
            )
            return self._candle(data)
        except Exception as exc:
            print(f"Historical candle error: {exc}")
            return None

    def compare_candles(self, live: dict | None, historical: dict | None) -> dict:
        """Compare same-timeframe candles; this is not independent verification."""
        if live is None or historical is None:
            return {"status": "ERROR", "message": "Candle data missing"}
        if historical["close"] <= 0 or live["close"] <= 0:
            return {"status": "ERROR", "message": "Invalid non-positive close"}

        diff_pct = (live["close"] - historical["close"]) / historical["close"] * 100
        volume_ratio = (
            live["volume"] / historical["volume"] if historical["volume"] > 0 else None
        )
        verification = {
            "status": "CONSISTENCY_CHECK",
            "message": "Same-source daily candles compared; no independent source verification claimed",
        }
        if abs(diff_pct) > 5:
            verification = {
                "status": "WARNING",
                "message": f"Daily close differs by {diff_pct:.2f}%",
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
# XAUUSD Daily Candle Consistency Report
**Symbol:** {self.symbol} ({self.yf_symbol})
**Generated:** {datetime.now(timezone.utc).isoformat()}

This report is a same-source consistency diagnostic. It is **not independent
source validation** and is not evidence for trading profitability.

## Comparison
| Metric | Value |
|--------|-------|
| Latest daily timestamp | {comparison["live"]["timestamp"]} |
| Historical daily timestamp | {comparison["historical"]["timestamp"]} |
| Latest close | ${comparison["live"]["close"]:.2f} |
| Historical close | ${comparison["historical"]["close"]:.2f} |
| Close difference | {comparison["diff_pct"]:+.2f}% |
| Volume ratio | {comparison["volume_ratio"] if comparison["volume_ratio"] is not None else "N/A"} |

## Status
**{comparison["verification"]["status"]}:** {comparison["verification"]["message"]}
"""


if __name__ == "__main__":
    validator = LiveCandleValidator("XAUUSD", "XAUUSD=X")
    live = validator.get_live_candle()
    historical = validator.get_historical_candle()
    if live and historical:
        comparison = validator.compare_candles(live, historical)
        with open("candle_validation_report.md", "w", encoding="utf-8") as handle:
            handle.write(validator.generate_report(comparison))
        print(f"Status: {comparison['verification']['status']}")
    else:
        raise SystemExit("Unable to obtain daily candle data")
