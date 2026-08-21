import sys

sys.path.append("cpp_quant/python")
import json

import pandas as pd

from cpp_quant import CppQuant

df = pd.read_parquet("data/raw/histdata/xauusd/xauusd_m1_cached.parquet")

timeframes = [
    ("1min", "1min"),
    ("5min", "5min"),
    ("15min", "15min"),
    ("30min", "30min"),
    ("1h", "1h"),
    ("4h", "4h"),
    ("1D", "1D"),
    ("1W", "W"),
    ("1M", "ME"),
]

summary = []
detail_timeframe = "1D"
detail_trades = []
detail_equity = []

for label, rule in timeframes:
    df_r = (
        df.resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    )

    engine = CppQuant()
    engine.load_from_dataframe(df_r)
    result = engine.run_sma(20, 50)

    summary.append(
        {
            "timeframe": label,
            "candles": len(df_r),
            "trades": result["num_trades"],
            "winrate": round(result["winrate"], 2),
            "total_return": round(result["total_return"], 2),
            "sharpe": round(result["sharpe_ratio"], 2),
            "profit_factor": round(result["profit_factor"], 2),
            "avg_win": round(result["avg_win"], 2),
            "avg_loss": round(result["avg_loss"], 2),
            "max_drawdown": round(result.get("max_drawdown", 0), 2),
        }
    )

    if label == detail_timeframe:
        capital = 10000.0
        for t in result["trades"]:
            entry_time, exit_time, entry_price, exit_price, pnl, is_win = t
            capital *= 1 + pnl
            detail_trades.append(
                {
                    "exit_time": int(exit_time),
                    "pnl_pct": round(pnl * 100, 3),
                    "is_win": bool(is_win),
                }
            )
            detail_equity.append({"exit_time": int(exit_time), "equity": round(capital, 2)})

output = {
    "summary": summary,
    "detail_timeframe": detail_timeframe,
    "detail_trades": detail_trades,
    "detail_equity": detail_equity,
}

with open("dashboard_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Saved dashboard_data.json — {len(summary)} timeframes, {len(detail_trades)} trades for {detail_timeframe}")
