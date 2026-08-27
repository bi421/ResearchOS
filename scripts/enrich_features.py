from pathlib import Path

import numpy as np
import pandas as pd

print("=" * 60)
print("⚙️ FEATURE ENGINEER: Өгөгдлийг баяжуулах процесс эхэллээ...")
print("=" * 60)

# 1. Өгөгдлийн файлыг олох
data_dir = Path("data/curated/xauusd")
csv_files = list(data_dir.glob("*.csv"))

if not csv_files:
    print("❌ Алдаа: data/curated/xauusd/ хавтас дотроос .csv файл олдсонгүй.")
    print("   Өгөгдлийн файлынхаа нэрийг шалгана уу.")
    exit(1)

# Хамгийн сүүлийн үеийн эсвэл эхний CSV-г авах
input_file = csv_files[0]
print(f"📂 Оролт: {input_file.name}")

# 2. Өгөгдлийг унших
df = pd.read_csv(input_file)

# DateTime багана байгаа эсэхийг шалгах (ихэнхдээ 'datetime', 'date', 'time' гэх мэт)
date_cols = [col for col in df.columns if "date" in col.lower() or "time" in col.lower()]
if date_cols:
    df["datetime"] = pd.to_datetime(df[date_cols[0]])
else:
    df["datetime"] = pd.to_datetime(df.iloc[:, 0])  # Эхний баганыг datetime гэж үзэх

df = df.sort_values("datetime").reset_index(drop=True)

# 3. Шинж чанаруудыг тооцоолох (Feature Engineering)
print("🔧 Шинж чанаруудыг тооцоолж байна...")

# A. Өгөөж (Returns)
df["return_1"] = df["close"].pct_change()

# B. ATR (Average True Range 14)
high_low = df["high"] - df["low"]
high_close = np.abs(df["high"] - df["close"].shift(1))
low_close = np.abs(df["low"] - df["close"].shift(1))
true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
df["atr_14"] = true_range.rolling(window=14).mean()
df["atr_pct"] = df["atr_14"] / df["close"]  # Үнэтэй харьцуулсан хэлбэлзэл

# C. RSI (Relative Strength Index 14)
delta = df["close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df["rsi_14"] = 100 - (100 / (1 + rs))

# D. Rolling Volatility (20)
df["volatility_20"] = df["return_1"].rolling(window=20).std()

# E. Time Regime Features
df["hour"] = df["datetime"].dt.hour
df["day_of_week"] = df["datetime"].dt.dayofweek  # 0=Даваа, 4=Баасан
df["is_london_ny_overlap"] = ((df["hour"] >= 13) & (df["hour"] <= 17)).astype(int)  # UTC цагаар ойролцоогоор

# F. NaN утгуудыг цэвэрлэх (Эхний 20 мөр)
df = df.dropna().reset_index(drop=True)

# 4. Шинэ файлыг хадгалах
output_file = data_dir / "xauusd_h1_enriched.csv"
df.to_csv(output_file, index=False, encoding="utf-8")

print("✅ Амжилттай! Шинж чанар нэмэгдсэн өгөгдөл хадгалагдлаа:")
print(f"   📁 {output_file}")
print(f"   📊 Нийт мөр: {len(df)}")
print(f"   📈 Нэмэгдсэн баганууд: {[c for c in df.columns if c not in ['open', 'high', 'low', 'close', 'volume', 'datetime']]}")
print("=" * 60)
