from pathlib import Path

import numpy as np
import pandas as pd

INPUT = Path("data/curated/xauusd/xauusd_m1_2021_2025_mt5.csv")
OUTPUT_DIR = Path("reports/xauusd_event_study")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("XAUUSD 2021-2025 EVENT DATASET BUILDER")
print("=" * 70)

df = pd.read_csv(INPUT)

required = {"Date", "Time", "Open", "High", "Low", "Close"}
missing = required - set(df.columns)

if missing:
    raise RuntimeError(f"Missing columns: {sorted(missing)}")

df["timestamp"] = pd.to_datetime(
    df["Date"] + " " + df["Time"],
    format="%Y.%m.%d %H:%M:%S",
    errors="raise",
)

df = df.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)

close = df["Close"].astype(float)
high = df["High"].astype(float)
low = df["Low"].astype(float)

# ------------------------------------------------------------
# Indicators
# ------------------------------------------------------------

sma20 = close.rolling(20).mean()
sma100 = close.rolling(100).mean()

prev_sma20 = sma20.shift(1)
prev_sma100 = sma100.shift(1)

cross_up = (sma20 > sma100) & (prev_sma20 <= prev_sma100)

cross_down = (sma20 < sma100) & (prev_sma20 >= prev_sma100)

# ATR-like M1 range measure
tr1 = high - low
tr2 = (high - close.shift(1)).abs()
tr3 = (low - close.shift(1)).abs()

true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

atr14 = true_range.rolling(14).mean()

# ------------------------------------------------------------
# Event extraction
# ------------------------------------------------------------

event_mask = cross_up | cross_down

events = pd.DataFrame(
    {
        "timestamp": df.loc[event_mask, "timestamp"].values,
        "direction": np.where(
            cross_up.loc[event_mask],
            "LONG",
            "SHORT",
        ),
        "entry": close.loc[event_mask].values,
        "sma20": sma20.loc[event_mask].values,
        "sma100": sma100.loc[event_mask].values,
        "atr14": atr14.loc[event_mask].values,
    }
)

events = events.dropna().reset_index(drop=True)

# ------------------------------------------------------------
# Forward horizons
# ------------------------------------------------------------

HORIZONS = {
    "15m": 15,
    "30m": 30,
    "60m": 60,
    "240m": 240,
}

# Map event timestamp -> dataframe row
timestamp_to_index = pd.Series(
    np.arange(len(df)),
    index=df["timestamp"],
)

events["bar_index"] = events["timestamp"].map(timestamp_to_index)

# ------------------------------------------------------------
# Event outcomes
# ------------------------------------------------------------

for name, horizon in HORIZONS.items():
    future_close = close.shift(-horizon)

    future_high = high.shift(-1).rolling(horizon).max().shift(-(horizon - 1))

    future_low = low.shift(-1).rolling(horizon).min().shift(-(horizon - 1))

    idx = events["bar_index"].astype("Int64")

    entry = events["entry"]

    fc = future_close.reindex(idx.to_numpy()).to_numpy()

    fh = future_high.reindex(idx.to_numpy()).to_numpy()

    fl = future_low.reindex(idx.to_numpy()).to_numpy()

    direction_sign = np.where(
        events["direction"].eq("LONG"),
        1.0,
        -1.0,
    )

    forward_return = (fc / entry - 1.0) * direction_sign

    mfe = np.where(
        events["direction"].eq("LONG"),
        fh / entry - 1.0,
        entry / fl - 1.0,
    )

    mae = np.where(
        events["direction"].eq("LONG"),
        fl / entry - 1.0,
        entry / fh - 1.0,
    )

    events[f"return_{name}"] = forward_return
    events[f"mfe_{name}"] = mfe
    events[f"mae_{name}"] = mae

    # Directional binary outcome
    events[f"win_{name}"] = (forward_return > 0).astype("Int64")

# ------------------------------------------------------------
# Cost-adjusted outcomes
# ------------------------------------------------------------

# Preserve the current project assumptions:
# commission = 0.10%
# slippage  = 0.05%
#
# Round-trip impact is represented conservatively as 0.30%.
# This is a research label, NOT a claim about broker execution.

COMMISSION = 0.0010
SLIPPAGE = 0.0005

ENTRY_COST = COMMISSION + SLIPPAGE
EXIT_COST = COMMISSION + SLIPPAGE

ROUND_TRIP_COST = ENTRY_COST + EXIT_COST

for name in HORIZONS:
    gross = events[f"return_{name}"]

    net = gross - ROUND_TRIP_COST

    events[f"net_return_{name}"] = net

    events[f"net_win_{name}"] = (net > 0).astype("Int64")

# ------------------------------------------------------------
# Quality flags
# ------------------------------------------------------------

events["valid_atr"] = events["atr14"] > 0

events["event_year"] = events["timestamp"].dt.year

events["event_month"] = events["timestamp"].dt.to_period("M").astype(str)

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_csv = OUTPUT_DIR / "xauusd_sma20_100_events_2021_2025.csv"

events.to_csv(
    output_csv,
    index=False,
)

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

summary = {
    "candles": len(df),
    "events": len(events),
    "long_events": int((events["direction"] == "LONG").sum()),
    "short_events": int((events["direction"] == "SHORT").sum()),
    "commission": COMMISSION,
    "slippage": SLIPPAGE,
    "round_trip_cost": ROUND_TRIP_COST,
}

for name in HORIZONS:
    valid = events[f"net_return_{name}"].dropna()

    summary[f"{name}_observations"] = len(valid)

    if len(valid):
        summary[f"{name}_gross_mean"] = float(events[f"return_{name}"].mean())

        summary[f"{name}_net_mean"] = float(valid.mean())

        summary[f"{name}_gross_win_rate"] = float(events[f"win_{name}"].mean())

        summary[f"{name}_net_win_rate"] = float(events[f"net_win_{name}"].mean())

        summary[f"{name}_median_net"] = float(valid.median())

summary_df = pd.DataFrame([summary])

summary_csv = OUTPUT_DIR / "event_study_summary.csv"

summary_df.to_csv(
    summary_csv,
    index=False,
)

print()
print("DATASET COMPLETE")
print("-" * 70)
print(f"Candles           : {len(df):,}")
print(f"Events            : {len(events):,}")
print(f"LONG events       : {(events.direction == 'LONG').sum():,}")
print(f"SHORT events      : {(events.direction == 'SHORT').sum():,}")
print()

for name in HORIZONS:
    print(f"{name:>5} | observations={len(events[f'return_{name}'].dropna()):,} | gross win={events[f'win_{name}'].mean():.2%} | net win={events[f'net_win_{name}'].mean():.2%} | net mean={events[f'net_return_{name}'].mean():.6%}")

print()
print("OUTPUT:")
print(output_csv)
print(summary_csv)
print("=" * 70)
