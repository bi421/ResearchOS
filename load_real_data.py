import pathlib

import numpy as np
import pandas as pd


def load_and_merge_real_data():
    print("🔄 Бодит өгөгдөл ачаалж байна...")

    # 1. XAUUSD өгөгдөл (Танд байгаа замыг тохируулна уу)
    # Жишээ: 'data/curated/xauusd/xauusd_daily.csv'
    xauusd_path = pathlib.Path("data/curated/xauusd/xauusd_daily.csv")

    if not xauusd_path.exists():
        print("⚠️  XAUUSD CSV файл олдсонгүй. Зохиомол өгөгдөл үүсгэж байна ( жишээ болгож)...")
        # fallback to synthetic if real data is missing
        dates = pd.date_range("2021-01-01", periods=1000, freq="D")
        df = pd.DataFrame({"close": 1800 + np.cumsum(np.random.normal(0, 5, 1000)), "open": 1800 + np.cumsum(np.random.normal(0, 5, 1000)), "high": 1800 + np.cumsum(np.random.normal(0, 5, 1000)) + 10, "low": 1800 + np.cumsum(np.random.normal(0, 5, 1000)) - 10, "volume": np.random.uniform(50000, 200000, 1000)}, index=dates)
        df.index.name = "date"
    else:
        df = pd.read_csv(xauusd_path, parse_dates=["date"], index_col="date")
        print(f"✅ XAUUSD ачаалагдлаа: {len(df)} мөр")

    # 2. Macro Factor-уудыг нэмэх (Жишээ баганууд)
    # Бодит төсөлд та эдгээрийг тусдаа CSV-ээс эсвэл yfinance-аас татаж merge хийнэ.
    np.random.seed(42)
    df["real_yield_10y"] = np.random.normal(0.5, 0.5, len(df))
    df["dxy"] = np.random.normal(95, 5, len(df))
    df["vix"] = np.random.normal(18, 5, len(df))
    df["breakeven_inflation_10y"] = np.random.normal(2.0, 0.3, len(df))
    df["fed_balance_sheet_change"] = np.random.normal(0, 2, len(df))
    df["geopolitical_risk_index"] = np.random.normal(50, 20, len(df))
    df["gold_silver_ratio"] = np.random.normal(75, 5, len(df))
    df["gold_oil_ratio"] = np.random.normal(25, 3, len(df))
    df["gold_btc_correlation"] = np.random.normal(0.2, 0.3, len(df))

    # 3. Цэвэрлэгээ: NaN утгуудыг forward-fill хийх
    df = df.ffill().dropna()

    print(f"✅ Нэгтгэсэн өгөгдөл бэлэн: {len(df)} мөр, {len(df.columns)} багана")
    return df


if __name__ == "__main__":
    real_df = load_and_merge_real_data()
    print("\n📊 Эхний 5 мөр:")
    print(real_df.head())
    real_df.to_csv("data/curated/xauusd/real_merged_data.csv", index=True)
    print("\n💾 'data/curated/xauusd/real_merged_data.csv' болж хадгалагдлаа.")
