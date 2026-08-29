import pathlib
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Төслийн root замыг нэмэх
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from researchos.engines.quant.machine_learning.purged_validation import purged_k_fold


def run_ml_macro_strategy():
    print("=" * 60)
    print("MACRO FACTOR ML PREDICTOR (Purged Walk-Forward)")
    print("=" * 60)

    # 1. Өгөгдөл ачаалах
    data_path = pathlib.Path("data/curated/xauusd/real_merged_data.csv")
    if not data_path.exists():
        print("❌ Өгөгдөл олдсонгүй. Эхлээд load_real_data.py-г ажиллуулна уу.")
        return

    df = pd.read_csv(data_path, parse_dates=["date"], index_col="date")
    print(f"✅ Өгөгдөл ачаалагдлаа: {len(df)} мөр")

    # 2. Шинж чанар (Features) ба Зорилт (Target) тодорхойлох
    feature_cols = ["real_yield_10y", "dxy", "vix", "breakeven_inflation_10y", "fed_balance_sheet_change", "geopolitical_risk_index", "gold_silver_ratio", "gold_oil_ratio", "gold_btc_correlation"]

    # Зорилт: Дараагийн өдрийн үнэ өсөх үү? (1 = Өснө, 0 = Буурна)
    df["target"] = (df["close"].pct_change().shift(-1) > 0).astype(int)

    # NaN утгуудыг цэвэрлэх
    df_clean = df.dropna(subset=feature_cols + ["target"]).copy()
    print(f"✅ Цэвэрлэсэн өгөгдөл: {len(df_clean)} мөр")

    X = df_clean[feature_cols].values
    y = df_clean["target"].values

    # 3. Purged K-Fold Cross-Validation (Өгөгдлийн алдагдлаас сэргийлэх)
    n_splits = 5
    purge_gap = 5  # 5 өдрийн цэвэрлэгээ (overlap-аас сэргийлэх)
    embargo_gap = 2  # 2 өдрийн embargo (target leakage-аас сэргийлэх)

    print(f"\n🔄 Purged K-Fold эхэлж байна (splits={n_splits}, purge={purge_gap}, embargo={embargo_gap})...")

    folds = purged_k_fold(len(X), n_splits=n_splits, purge_gap=purge_gap, embargo_gap=embargo_gap)

    fold_accuracies = []
    fold_sharpe = []

    for fold in folds:
        train_idx = fold.train_indices
        test_idx = fold.test_indices
        fold_id = fold.fold_id
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # ML загвар сургах (Random Forest)
        model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)

        # Таамаглал
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        fold_accuracies.append(acc)

        # Энгийн стратеги: Таамаглал = 1 бол Long, 0 бол Short
        # Test period-ын бодит өгөгдлийг авах
        test_returns = df_clean["close"].pct_change().iloc[test_idx].values
        # Таамагласан чиглэлээр position авах (1 -> 1, 0 -> -1)
        positions = np.where(y_pred == 1, 1, -1)
        strategy_returns = positions * test_returns

        # Sharpe Ratio тооцоолох (жилийн 252 өдөр гэж үзвэл)
        if np.std(strategy_returns) > 0:
            sharpe = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
        else:
            sharpe = 0.0
        fold_sharpe.append(sharpe)

        print(f"  Fold {fold_id+1}: Accuracy = {acc:.4f}, Sharpe = {sharpe:.4f}")

    # 4. Үр дүнгийн нэгтгэл
    print("\n" + "=" * 60)
    print("📊 ML STRATEGY RESULTS")
    print("=" * 60)
    print(f"Average Purged Accuracy : {np.mean(fold_accuracies):.4f} (+/- {np.std(fold_accuracies):.4f})")
    print(f"Average Out-of-Sample Sharpe : {np.mean(fold_sharpe):.4f}")

    # Feature Importance (Хамгийн чухал макро хүчин зүйлс)
    final_model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    final_model.fit(X, y)
    importances = pd.Series(final_model.feature_importances_, index=feature_cols).sort_values(ascending=False)

    print("\n🏆 Top 3 Macro Features by Importance:")
    for feat, imp in importances.head(3).items():
        print(f"  - {feat}: {imp:.4f}")

    print("\n✅ ML Macro Predictor амжилттай дууслаа!")


if __name__ == "__main__":
    run_ml_macro_strategy()
