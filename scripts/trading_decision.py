# trading_decision.py
import re

import pandas as pd

print("=" * 60)
print("ðŸš€ Ð¥Ð£Ð”ÐÐ›Ð”ÐÐÐÐ« Ð¨Ð˜Ð™Ð”Ð’Ð­Ð  Ð“ÐÐ Ð“ÐÐ¥ Ð¡Ð˜Ð¡Ð¢Ð•Ðœ")
print("=" * 60)

# 1. Market Intelligence Ñ‚Ð°Ð¹Ð»Ð°Ð½Ð³Ð°Ð°Ñ Ó©Ð³Ó©Ð³Ð´Ó©Ð» Ð°Ð²Ð°Ñ…
try:
    with open("market_report_v3.md", "r", encoding="utf-8") as f:
        text = f.read()

    # Evidence Score ÑƒÑ‚Ð³Ð° Ð°Ð²Ð°Ñ…
    score_match = re.search(r"\*\*Total Score\*\* \| \*\*([\d.-]+)\*\*", text)
    total_score = float(score_match.group(1)) if score_match else 0.0

    # Correlation ÑƒÑ‚Ð³Ð° Ð°Ð²Ð°Ñ…
    dxy_match = re.search(r"DXY \| ([\d.-]+)", text)
    dxy_corr = float(dxy_match.group(1)) if dxy_match else 0.0

    # Regime Ð°Ð²Ð°Ñ…
    regime_match = re.search(r"Market Regime: \*\*([A-Z-]+)\*\*", text)
    regime = regime_match.group(1) if regime_match else "NEUTRAL"

    print("\nðŸ“Š 1. MACRO Ð¨Ð˜ÐÐ–Ð˜Ð›Ð“Ð­Ð­")
    print(f"   Evidence Score: {total_score:.3f} (Bullish > 0.2, Bearish < -0.2)")
    print(f"   Ð”Ð¾Ð»Ð»Ð°Ñ€ (DXY) Ð±Ð° ÐÐ»Ñ‚Ð½Ñ‹ Ñ…Ð°Ð¼Ð°Ð°Ñ€Ð°Ð»: {dxy_corr:.3f} (Ð¡Ó©Ñ€Ó©Ð³ = ÐÐ»Ñ‚ Ó©ÑÓ©Ñ…)")
    print(f"   Ð—Ð°Ñ… Ð·ÑÑÐ»Ð¸Ð¹Ð½ Ñ‚Ó©Ð»Ó©Ð²: {regime}")

except FileNotFoundError:
    print("âš ï¸ market_report_v3.md Ð¾Ð»Ð´ÑÐ¾Ð½Ð³Ò¯Ð¹! Ð­Ñ…Ð»ÑÑÐ´ run_full_analysis_fixed4.py-Ð³ Ð°Ð¶Ð¸Ð»Ð»ÑƒÑƒÐ»Ð½Ð° ÑƒÑƒ.")
    total_score, dxy_corr, regime = 0.0, -0.8, "RISK-ON"

# 2. Ð¢ÐµÑ…Ð½Ð¸Ðº ÑˆÐ¸Ð½Ð¶Ð¸Ð»Ð³ÑÑÐ½Ð¸Ð¹ Ò¯Ñ€ Ð´Ò¯Ð½ (Backtest)
try:
    df = pd.read_csv("backtest_results_all.csv")
    # Ð¥Ð°Ð¼Ð³Ð¸Ð¹Ð½ ÑÐ°Ð¹Ð½ Ð°Ñ€Ð¸Ð»Ð¶Ð°Ð°Ð½Ñ‹ Ñ‚Ð¾Ð¾ Ð±Ò¯Ñ…Ð¸Ð¹ ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ð¹Ð³ Ð¾Ð»Ð¾Ñ… (30min SMA)
    best_strategy = df[(df["Strategy"].str.contains("SMA")) & (df["Timeframe"] == "30min")]
    if not best_strategy.empty:
        row = best_strategy.iloc[0]
        tech_return = row["Return"]
        tech_sharpe = row["Sharpe"]
        tech_trades = row["Trades"]
        tech_winrate = row["Winrate"]
    else:
        tech_return, tech_sharpe, tech_trades, tech_winrate = 0, 0, 0, 0

    print("\nðŸ“ˆ 2. Ð¢Ð•Ð¥ÐÐ˜Ðš Ð¨Ð˜ÐÐ–Ð˜Ð›Ð“Ð­Ð­ (SMA 20/50 - 30Ð¼Ð¸Ð½)")
    print(f"   ÐÑ€Ð¸Ð»Ð³Ð°Ð°Ð½Ñ‹ Ñ‚Ð¾Ð¾: {tech_trades}")
    print(f"   Ð¯Ð»Ð°Ð»Ñ‚Ñ‹Ð½ Ñ…ÑƒÐ²ÑŒ: {tech_winrate:.1f}%")
    print(f"   ÐÐ¸Ð¹Ñ‚ Ó©Ð³Ó©Ó©Ð¶: {tech_return:.2f}%")
    print(f"   Sharpe: {tech_sharpe:.2f}")

except FileNotFoundError:
    print("âš ï¸ backtest_results_all.csv Ð¾Ð»Ð´ÑÐ¾Ð½Ð³Ò¯Ð¹! Ð­Ñ…Ð»ÑÑÐ´ run_all_in_one.py-Ð³ Ð°Ð¶Ð¸Ð»Ð»ÑƒÑƒÐ»Ð½Ð° ÑƒÑƒ.")
    tech_return, tech_sharpe, tech_trades, tech_winrate = 124.92, 0.23, 650, 41.54

# 3. ÐÐ­Ð“Ð”Ð¡Ð­Ð Ð¨Ð˜Ð™Ð”Ð’Ð­Ð  (Decision Logic)
print("\n" + "=" * 60)
print("ðŸ§  3. ÐÐ­Ð“Ð”Ð¡Ð­Ð Ð¨Ð˜Ð™Ð”Ð’Ð­Ð  (Action Plan)")
print("=" * 60)

# Ò®Ð·Ò¯Ò¯Ð»ÑÐ»Ñ‚Ò¯Ò¯Ð´Ð¸Ð¹Ð³ Ð½Ð¾Ñ€Ð¼Ñ‡Ð¸Ð»Ð¾Ð» (0-100 Ñ…Ð¾Ð¾Ñ€Ð¾Ð½Ð´)
macro_score = total_score * 10  # 0.064 -> 0.64
if dxy_corr < -0.5:  # Ð”Ð¾Ð»Ð»Ð°Ñ€ Ð¼Ð°Ñˆ ÑÑƒÐ»
    macro_score += 2.0
elif dxy_corr < -0.3:
    macro_score += 1.0

# Ð¢ÐµÑ…Ð½Ð¸Ðº Ò¯Ð·Ò¯Ò¯Ð»ÑÐ»Ñ‚Ð¸Ð¹Ð³ Ð¾Ð½Ð¾Ð¾ Ð±Ð¾Ð»Ð³Ð¾Ñ…
tech_score = 0
if tech_return > 100:
    tech_score = 3.0
elif tech_return > 50:
    tech_score = 2.0
elif tech_return > 0:
    tech_score = 1.0

if tech_sharpe > 1.0:
    tech_score += 1.0
if tech_winrate > 50:
    tech_score += 1.0

# ÐÐ¸Ð¹Ñ‚ Ð¸Ñ‚Ð³ÑÐ»Ñ†Ð»Ð¸Ð¹Ð½ Ð¸Ð½Ð´ÐµÐºÑ (Action Index)
action_score = (macro_score * 0.4) + (tech_score * 0.6)

print("\nðŸ’¡ Ð¨Ð˜Ð™Ð”Ð’Ð­Ð :")
print("-" * 40)

if action_score > 2.5 and total_score > 0.1:
    print("âœ… **Ð¥Ð£Ð”ÐÐ›Ð”ÐÐ¥ (BUY)**")
    print("   Ð¨Ð°Ð»Ñ‚Ð³Ð°Ð°Ð½: ÐœÐ°ÐºÑ€Ð¾ Ð±Ð¾Ð»Ð¾Ð½ Ñ‚ÐµÑ…Ð½Ð¸Ðº Ò¯Ð·Ò¯Ò¯Ð»ÑÐ»Ñ‚Ò¯Ò¯Ð´ ÑÐµÑ€ÑÐ³. ÐÐ»Ñ‚Ð½Ñ‹ Ó©ÑÓ©Ð»Ñ‚Ð¸Ð¹Ð½ Ð¼Ð°Ð³Ð°Ð´Ð»Ð°Ð» Ó©Ð½Ð´Ó©Ñ€.")
    print("   Ð¡Ð°Ð½Ð°Ð» Ð±Ð¾Ð»Ð³Ð¾Ñ… ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸: 30Ð¼Ð¸Ð½-Ð¸Ð¹Ð½ SMA(20,50) ÐºÑ€Ð¾ÑÑÐ¾Ð²ÐµÑ€.")
    print("   ðŸ“Œ Ð—Ð¾Ð³ÑÐ¾Ð»Ñ‚Ñ‹Ð½ Ð°Ð»Ð´Ð°Ð³Ð´Ð°Ð» (Stop Loss): -5%")
    print("   ðŸ“Œ ÐÑˆÐ¸Ð³ Ð°Ð²Ð°Ñ… Ñ‚Ò¯Ð²ÑˆÐ¸Ð½ (Take Profit): +10%")
elif action_score > 1.5:
    print("â³ **Ð¥Ò®Ð›Ð­Ð¥ (WAIT / CAUTIOUS)**")
    print("   Ð¨Ð°Ð»Ñ‚Ð³Ð°Ð°Ð½: Ò®Ð·Ò¯Ò¯Ð»ÑÐ»Ñ‚Ò¯Ò¯Ð´ Ñ‚Ó©Ð²Ð¸Ð¹Ð³ ÑÐ°Ñ…Ð¸ÑÐ°Ð½. Ð­Ñ€ÑÐ´ÑÐ» Ð±Ð°Ð³Ð°Ñ‚Ð°Ð¹ Ð±Ð°Ð¹Ñ…Ñ‹Ð³ Ð·Ó©Ð²Ð»Ó©Ð¶ Ð±Ð°Ð¹Ð½Ð°.")
    print("   Ð¡Ð°Ð½Ð°Ð»: Evidence Score 0.2-Ð¾Ð¾Ñ Ð´ÑÑÑˆ Ð³Ð°Ñ€Ð°Ñ… ÑÑÐ²ÑÐ» 30Ð¼Ð¸Ð½ Ð³Ñ€Ð°Ñ„Ð¸Ðº Ð´ÑÑÑ€ SMA Ð·Ð°Ð³Ð°Ð»Ð¼Ð°Ð¹ Ñ‚Ð¾Ð´Ð¾Ñ€Ñ…Ð¾Ð¹ Ð±Ð¾Ð»Ñ‚Ð¾Ð» Ñ…Ò¯Ð»ÑÑÐ½Ñ Ò¯Ò¯.")
else:
    print("âŒ **Ð—ÐÐ ÐÐ¥ / Ð¥Ð£Ð”ÐÐ›Ð”ÐÐ¥Ð“Ò®Ð™ Ð‘ÐÐ™Ð¥ (SELL / AVOID)**")
    print("   Ð¨Ð°Ð»Ñ‚Ð³Ð°Ð°Ð½: Ð¢ÐµÑ…Ð½Ð¸Ðº ÑÑÐ²ÑÐ» Ð¼Ð°ÐºÑ€Ð¾ Ò¯Ð·Ò¯Ò¯Ð»ÑÐ»Ñ‚Ò¯Ò¯Ð´ ÑÑƒÐ» Ð±Ð°Ð¹Ð½Ð°.")
    print("   Ð¡Ð°Ð½Ð°Ð»: Ð‘Ð¾Ð³Ð¸Ð½Ð¾ Ñ…ÑƒÐ³Ð°Ñ†Ð°Ð°Ð½Ð´ Ð°Ð»Ñ‚Ð½Ñ‹ Ò¯Ð½Ñ ÑƒÐ½Ð°Ñ… Ð¼Ð°Ð³Ð°Ð´Ð»Ð°Ð»Ñ‚Ð°Ð¹. Ð¥ÑƒÐ´Ð°Ð»Ð´Ð°Ñ… ÑÑÐ²ÑÐ» Ð·Ð°Ñ… Ð·ÑÑÐ»ÑÑÑ Ð³Ð°Ñ€Ð°Ñ….")

# 4. Ð­Ñ€ÑÐ´ÑÐ»Ð¸Ð¹Ð½ ÑÐ°Ð½ÑƒÑƒÐ»Ð³Ð°
print("\nâš ï¸ Ð­Ð Ð¡Ð”Ð­Ð›Ð˜Ð™Ð Ð¡ÐÐÐ£Ð£Ð›Ð“Ð:")
print("-" * 40)
if regime == "RISK-ON":
    print("   ðŸ”¥ Ð—Ð°Ñ… Ð·ÑÑÐ» 'RISK-ON' Ñ‚Ó©Ð»Ó©Ð²Ñ‚ Ð±Ð°Ð¹Ð½Ð°. Ó¨Ð½Ð´Ó©Ñ€ Ó©Ð³Ó©Ó©Ð¶, Ó©Ð½Ð´Ó©Ñ€ ÑÑ€ÑÐ´ÑÐ»Ñ‚ÑÐ¹ Ò¯Ðµ.")
else:
    print("   ðŸ›¡ï¸ Ð—Ð°Ñ… Ð·ÑÑÐ» 'RISK-OFF' Ñ‚Ó©Ð»Ó©Ð²Ñ‚ Ð¾Ð¹Ñ€Ñ…Ð¾Ð½. Ð‘Ð¾Ð»Ð³Ð¾Ð¾Ð¼Ð¶Ñ‚Ð¾Ð¹ Ð°Ñ€Ð¸Ð»Ð¶Ð°Ð° Ñ…Ð¸Ð¹Ñ… Ñ…ÑÑ€ÑÐ³Ñ‚ÑÐ¹.")

# Ð”Ò¯Ð³Ð½ÑÐ»Ñ‚
print("\n" + "=" * 60)
print("ðŸ“Œ Ð”Ò®Ð“ÐÐ­Ð›Ð¢")
print("=" * 60)
print(f"ðŸ“Š ÐÐ¸Ð¹Ñ‚ Ò¯Ð½ÑÐ»Ð³ÑÑÐ½Ð¸Ð¹ Ð¾Ð½Ð¾Ð¾ (Action Score): {action_score:.2f} / 5.0")
print(f"ðŸ“ˆ Ð¥Ð°Ð¼Ð³Ð¸Ð¹Ð½ ÑÐ°Ð¹Ð½ ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸: SMA(20,50) - {tech_trades} Ð°Ñ€Ð¸Ð»Ð³Ð°Ð°, {tech_return:.2f}% Ó©Ð³Ó©Ó©Ð¶")
print("âœ… Ð­Ð½ÑÑ…Ò¯Ò¯ ÑˆÐ¸Ð¹Ð´Ð²ÑÑ€ Ð½ÑŒ Ð·Ó©Ð²Ñ…Ó©Ð½ Ñ‚Ð°Ð½Ñ‹ Ð¾Ð´Ð¾Ð¾Ð³Ð¸Ð¹Ð½ Ó©Ð³Ó©Ð³Ð´Ó©Ð» Ð´ÑÑÑ€ ÑÑƒÑƒÑ€Ð¸Ð»ÑÐ°Ð½ Ð·Ó©Ð²Ð»Ó©Ð¼Ð¶ ÑŽÐ¼.\n")
