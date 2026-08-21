import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

warnings.filterwarnings("ignore")

print("=" * 60)
print("🚀 V4 H1 REAL DATA: 2026 оны бодит H1 өгөгдөл дээрх тест")
print("=" * 60)

data_dir = Path("data/curated/xauusd")
csv_files = list(data_dir.glob("*.csv"))

# H1 гэсэн үгтэй файлыг тэргүүнд хайх
h1_files = [f for f in csv_files if "h1" in f.name.lower()]
file_to_use = h1_files[0] if h1_files else csv_files[0]

print(f"📂 Ашиглаж буй өгөгдөл: {file_to_use.name}")
df = pd.read_csv(file_to_use)

cols_lower = {c.lower(): c for c in df.columns}
close_col = next((c for k, c in cols_lower.items() if "close" in k), None)
high_col = next((c for k, c in cols_lower.items() if "high" in k), close_col)
low_col = next((c for k, c in cols_lower.items() if "low" in k), close_col)
date_col = next((c for k, c in cols_lower.items() if "date" in k or "time" in k), df.columns[0])

df = df.sort_values(date_col).reset_index(drop=True)

# Индикаторууд үүсгэх
print("🔧 H1 индикаторуудыг тооцоолж байна...")
df["return_1"] = df[close_col].pct_change()
df["sma_20"] = df[close_col].rolling(20).mean()
df["price_to_sma_20"] = df[close_col] / df["sma_20"] - 1

delta = df[close_col].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df["rsi_14"] = 100 - (100 / (1 + rs))

high_low = df[high_col] - df[low_col]
high_close = np.abs(df[high_col] - df[close_col].shift(1))
low_close = np.abs(df[low_col] - df[close_col].shift(1))
true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
df["atr_14"] = true_range.rolling(window=14).mean()
df["atr_pct"] = df["atr_14"] / df[close_col]
df["vol_20"] = df["return_1"].rolling(20).std()

feature_cols = ["return_1", "price_to_sma_20", "rsi_14", "atr_pct", "vol_20"]
df = df.dropna(subset=feature_cols + [close_col]).reset_index(drop=True)

print(f"✅ Бэлэн: {len(df)} мөр (H1), {len(feature_cols)} индикатор")

# H1-д зориулсан бодит босго утгууд (0.0% - 0.5%)
horizons = [1, 3, 5, 10, 20]
thresholds = [0.0000, 0.0010, 0.0020, 0.0030]

results = []
print("\n🔄 Sweeping (Balanced RF on H1 Data)...")

for h in horizons:
    for t in thresholds:
        try:
            future_return = df[close_col].shift(-h) / df[close_col] - 1
            y = (future_return > t).astype(int)

            X = df[feature_cols].iloc[:-h]
            y_clean = y.iloc[:-h]

            if y_clean.sum() == 0 or y_clean.sum() == len(y_clean):
                continue

            baseline_acc = max(y_clean.mean(), 1 - y_clean.mean())

            split_idx = int(len(X) * 0.8)
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y_clean.iloc[:split_idx], y_clean.iloc[split_idx:]

            model = RandomForestClassifier(n_estimators=100, max_depth=6, class_weight="balanced", random_state=42)
            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            model_acc = accuracy_score(y_test, y_pred)

            n = len(y_test)
            k = int(model_acc * n)
            p_value = binomtest(k, n, p=baseline_acc, alternative="greater").pvalue

            # Зөвхөн 1%-иас дээш сайжруулалттайг бүртгэх
            if model_acc > baseline_acc + 0.01:
                results.append(
                    {
                        "horizon": int(h),
                        "threshold": float(t),
                        "model_acc": round(float(model_acc), 4),
                        "baseline_acc": round(float(baseline_acc), 4),
                        "improvement": round(float(model_acc - baseline_acc), 4),
                        "p_value": round(float(p_value), 5),
                    }
                )
        except Exception:
            pass

output_file = data_dir / "phase51_h1_2026_REAL_RESULTS.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\n✅ H1 Тест дууслаа. Файл: {output_file}")
print(f"🏆 Суурь шугамаас 1%-иар ИЛҮҮ гарсан бодит хослолууд: {len(results)}")

if results:
    results.sort(key=lambda x: x["improvement"], reverse=True)
    print("\n🥇 ШИЛДЭГ H1 ҮР ДҮНГҮҮД (2026 оны бодит өгөгдөл):")
    for r in results[:5]:
        print(f"  ✅ h={r['horizon']:2d}, t={r['threshold']:.4f} | Model: {r['model_acc']:.4f} vs Base: {r['baseline_acc']:.4f} (Improvement: +{r['improvement']:.4f}) | p={r['p_value']:.5f}")
else:
    print("\n⚠️ H1 өгөгдөл дээр ч гэсэн 1%-иас дээш давуу тал (edge) олдсонгүй.")
    print("   Дүгнэлт: Random Forest + стандарт индикаторууд XAUUSD H1 дээр чиглэл таамаглах хангалттай мэдээлэл агуулаагүй байна.")

print("=" * 60)
