import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

plt.style.use("dark_background")
fig = plt.figure(figsize=(9, 16), facecolor="#0a0a0a")
gs = gridspec.GridSpec(4, 2, height_ratios=[1.5, 3, 1.5, 1.5], hspace=0.3, wspace=0.2)

x = np.linspace(0, 100, 500)
base_profit = np.cumsum(np.random.normal(0.5, 2, 500)) + 100000
prices = 40000 + np.cumsum(np.random.normal(10, 50, 500))
volume = np.random.randint(100, 1000, 500)
rsi = 50 + np.cumsum(np.random.normal(0, 1, 500))
rsi = np.clip(rsi, 10, 90)

ax_header = fig.add_subplot(gs[0, :])
ax_header.axis("off")
ax_header.text(
    0.5,
    6,
    "+$220,084",
    fontsize=48,
    fontweight="bold",
    color="#00ff88",
    ha="left",
    va="center",
    fontfamily="monospace",
)
ax_header.text(
    0.5,
    2.5,
    "Total Backtest Profit | ResearchOS Engine",
    fontsize=14,
    color="#888888",
    ha="left",
    va="center",
)

ax_price = fig.add_subplot(gs[1, :])
ax_price.fill_between(x, prices, alpha=0.1, color="#00ff88")
ax_price.plot(x, prices, color="#00ff88", linewidth=1.5)
ax_price.set_title("BTC/USD Strategy Execution", color="white", fontsize=12, pad=10)
ax_price.tick_params(colors="#444444", labelsize=8)
for spine in ax_price.spines.values():
    spine.set_color("#222222")

ax_vol = fig.add_subplot(gs[2, 0])
ax_vol.bar(x, volume, color="#1e90ff", alpha=0.6, width=0.8)
ax_vol.set_title("Volume", color="#888888", fontsize=10)
ax_vol.tick_params(colors="#444444", labelsize=7)
for spine in ax_vol.spines.values():
    spine.set_color("#222222")

ax_rsi = fig.add_subplot(gs[2, 1])
ax_rsi.plot(x, rsi, color="#ff6347", linewidth=1.2)
ax_rsi.axhline(70, color="#ff4444", linestyle="--", linewidth=0.8, alpha=0.5)
ax_rsi.axhline(30, color="#00ff88", linestyle="--", linewidth=0.8, alpha=0.5)
ax_rsi.set_title("RSI (14)", color="#888888", fontsize=10)
ax_rsi.tick_params(colors="#444444", labelsize=7)
for spine in ax_rsi.spines.values():
    spine.set_color("#222222")

ax_profit = fig.add_subplot(gs[3, :])
ax_profit.fill_between(x, base_profit, alpha=0.15, color="#00ff88")
ax_profit.plot(x, base_profit, color="#00ff88", linewidth=1.2)
ax_profit.set_title("Equity Curve", color="#888888", fontsize=10)
ax_profit.tick_params(colors="#444444", labelsize=7)
for spine in ax_profit.spines.values():
    spine.set_color("#222222")

plt.tight_layout()
plt.savefig("quant_social_post.png", dpi=150, facecolor="#0a0a0a", edgecolor="none")
print("Амжилттай: quant_social_post.png")
