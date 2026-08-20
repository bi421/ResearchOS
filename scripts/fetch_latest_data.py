import yfinance as yf
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("📡 ШИНЭ ӨГӨГДӨЛ: GC=F (Gold Futures) бодит өгөгдлийг татаж байна...")
print("=" * 60)

data_dir = Path("data/curated/xauusd")
data_dir.mkdir(parents=True, exist_ok=True)

# GC=F нь Yahoo Finance дээрх хамгийн найдвартай алтны үнийн тикер (XAUUSD-тай ижил хөдөлдөг)
ticker = yf.Ticker("GC=F")

print("⏳ Өдрийн (D1) өгөгдлийг 2021 оноос хойш татаж байна...")
df_d1 = ticker.history(period="5y", interval="1d")

print("⏳ Цагийн (H1) өгөгдлийг сүүлийн 60 хоногоос хойш татаж байна...")
df_h1 = ticker.history(period="60d", interval="1h")

# Баганын нэрийг жижиг үсэгтэй, MT5 форматтай ижил болгох
def format_columns(df):
    df.index.name = 'Date'
    df = df.reset_index()
    df.columns = [c.lower() for c in df.columns]
    if 'datetime' not in df.columns and 'date' in df.columns:
        df = df.rename(columns={'date': 'datetime'})
    return df

df_d1 = format_columns(df_d1)
df_h1 = format_columns(df_h1)

# Өгөгдөл хоосон эсэхийг шалгах
if len(df_d1) == 0 or len(df_h1) == 0:
    print("\n❌ АЛДАА: Yahoo Finance-аас өгөгдөл татаж чадсангүй. Интернет холболтоо шалгана уу.")
else:
    file_d1 = data_dir / "xauusd_d1_2021_2026_real.csv"
    file_h1 = data_dir / "xauusd_h1_2026_recent_real.csv"

    df_d1.to_csv(file_d1, index=False, encoding='utf-8')
    df_h1.to_csv(file_h1, index=False, encoding='utf-8')

    print("\n✅ АМЖИЛТТАЙ! Бодит өгөгдлүүд хадгалагдлаа:")
    print(f"   📁 Өдрийн (D1): {file_d1.name}")
    print(f"      → Нийт мөр: {len(df_d1)} | Сүүлийн огноо: {df_d1['datetime'].max().date()}")
    print(f"   📁 Цагийн (H1): {file_h1.name}")
    print(f"      → Нийт мөр: {len(df_h1)} | Сүүлийн огноо: {df_h1['datetime'].max()}")
    
    print(f"\n🔍 Сүүлийн бичлэг (H1): {df_h1.iloc[-1]['datetime']} | Close: {df_h1.iloc[-1]['close']:.2f}")

print("=" * 60)
