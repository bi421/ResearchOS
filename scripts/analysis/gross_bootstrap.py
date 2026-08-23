import numpy as np
import pandas as pd

p = "reports/xauusd_event_study/xauusd_sma20_100_events_2021_2025.csv"
df = pd.read_csv(p)

rng = np.random.default_rng(42)

print("=" * 70)
print("GROSS RETURN BOOTSTRAP — 95% CI")
print("=" * 70)

for col in [
    "return_15m",
    "return_30m",
    "return_60m",
    "return_240m",
]:
    x = df[col].dropna().to_numpy(dtype=float)
    n = len(x)

    boot = np.empty(5000)

    for i in range(5000):
        sample = rng.choice(x, size=n, replace=True)
        boot[i] = sample.mean()

    mean = x.mean()
    median = np.median(x)

    lo, hi = np.percentile(boot, [2.5, 97.5])

    print(f"{col:15} " f"N={n:,} " f"mean={mean:.8%} " f"median={median:.8%} " f"CI=[{lo:.8%}, {hi:.8%}] " f"{'POSITIVE' if lo > 0 else 'NEGATIVE' if hi < 0 else 'NO CLEAR EDGE'}")
