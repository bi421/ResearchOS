# scripts/trading_signal.py
import os
import re

import pandas as pd

print("=" * 70)
print("📊 ХУДАЛДААНЫ ШИЙДВЭР ГАРГАХ СИСТЕМ")
print("=" * 70)

report_dir = "reports"
if not os.path.exists(report_dir):
    report_dir = "."

try:
    with open(os.path.join(report_dir, "market_report_v3.md"), "r", encoding="utf-8") as f:
        text = f.read()
    score = float(re.search(r"\*\*Total Score\*\* \| \*\*([\d.-]+)\*\*", text).group(1))
    dxy = float(re.search(r"DXY \| ([\d.-]+)", text).group(1))
    regime = re.search(r"Market Regime: \*\*([A-Z-]+)\*\*", text).group(1)
    print(f"   Evidence Score: {score:.3f}")
    print(f"   DXY vs XAUUSD: {dxy:.3f}")
    print(f"   Regime: {regime}")
except Exception as e:
    print(f"⚠️ Market Intelligence тайлан олдсонгүй: {e}")
    score, dxy, regime = 0.0, -0.8, "RISK-ON"

try:
    df = pd.read_csv(os.path.join(report_dir, "backtest_results_all.csv"))
    best = df[df["Strategy"].str.contains("SMA")].iloc[0]
    trades = best["Trades"]
    winrate = best["Winrate"]
    ret = best["Return"]
    sharpe = best["Sharpe"]
    print(f"   Шилдэг стратеги: {best['Strategy']} @ {best['Timeframe']}")
    print(f"   Арилгаа: {trades}, Winrate: {winrate:.1f}%, Return: {ret:.2f}%")
except Exception as e:
    print(f"⚠️ Backtest үр дүн олдсонгүй: {e}")
    trades, winrate, ret, sharpe = 650, 41.5, 124.9, 0.23

print("\n" + "=" * 70)
print("🎯 ШИЙДВЭР")
print("=" * 70)

macro_score = score * 10
if dxy < -0.5:
    macro_score += 2
tech_score = (1 if ret > 50 else 0) + (1 if sharpe > 1.0 else 0) + (1 if winrate > 50 else 0)
action_score = (macro_score * 0.4) + (tech_score * 0.6)

if action_score > 2.5 and ret > 50:
    print("✅ ХУДАЛДАХ (BUY)")
    print("   Макро болон техник үзүүлэлтүүд эерэг.")
elif action_score > 1.5:
    print("⏳ ХҮЛЭХ (WAIT)")
    print("   Үзүүлэлтүүд төвийг сахисан.")
else:
    print("❌ ХУДАЛДАХГҮЙ БАЙХ (AVOID)")

print(f"   Нийт үнэлгээний оноо: {action_score:.2f} / 5.0")
print("\n" + "=" * 70)
