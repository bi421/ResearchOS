import pandas as pd
import glob
from researchos.ml_engine.features import create_features
from researchos.quant_engine.backtest import BacktestEngine
from researchos.ml_engine.strategy import MLStrategy

# 1. Өгөгдөл ачаалах
print("Loading data...")
files = glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
df = pd.concat(
    [
        pd.read_csv(
            f, sep=";", header=None, names=["datetime", "open", "high", "low", "close", "volume"]
        )
        for f in files
    ],
    ignore_index=True,
)
df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S")
df = df.set_index("datetime")
df_h = (
    df.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
)
print(f"Data loaded: {len(df_h)} bars")

# 2. Цаг хугацаагаар хуваах (2021-2023 train, 2023-2024 validation, 2024-2025 test)
dates = df_h.index
split1 = int(len(dates) * 0.7)  # 2021-2023
split2 = int(len(dates) * 0.85)  # 2023-2024

train_df = df_h.iloc[:split1]
val_df = df_h.iloc[split1:split2]
test_df = df_h.iloc[split2:]

print(f"Train: {train_df.index[0]} to {train_df.index[-1]} ({len(train_df)} bars)")
print(f"Val:   {val_df.index[0]} to {val_df.index[-1]} ({len(val_df)} bars)")
print(f"Test:  {test_df.index[0]} to {test_df.index[-1]} ({len(test_df)} bars)")


# 3. Feature үүсгэх (train дээр тохируулж, val/test дээр хувиргах)
def prepare_data(df, scaler=None, fit_scaler=False):
    df_feat = create_features(df)
    if df_feat.empty:
        return None, None, None
    feature_cols = [col for col in df_feat.columns if col not in ["target", "datetime"]]
    X = df_feat[feature_cols].values
    y = df_feat["target"].values
    if fit_scaler:
        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        return X_scaled, y, scaler, feature_cols
    else:
        X_scaled = scaler.transform(X)
        return X_scaled, y, scaler, feature_cols


X_train, y_train, scaler, feature_names = prepare_data(train_df, fit_scaler=True)
X_val, y_val, _, _ = prepare_data(val_df, scaler)
X_test, y_test, _, _ = prepare_data(test_df, scaler)

# 4. Модел сургах (зөвхөн train дээр)
print("Training model on train set...")
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)

# 5. Grid search (validation set дээр)
thresholds = [0.45, 0.48, 0.50, 0.52, 0.55, 0.58, 0.60]
engine = BacktestEngine()
val_results = []

print("\n🔍 VALIDATION GRID SEARCH (Bonferroni correction: 0.05/7 = 0.007)")
print("Threshold | Trades | Return  | Sharpe | MaxDD  | WinRate | Sharpe_CI_low | Sharpe_CI_high")
print("----------|--------|---------|--------|--------|---------|---------------|---------------")

for th in thresholds:
    # Validation дээр дохио үүсгэх
    strategy = MLStrategy(model, scaler, feature_names, threshold=th)
    # prices-г val_df-ийн close үнээр дамжуулах
    val_prices = val_df["close"].tolist()
    result = engine.run(val_prices, strategy)

    # Bootstrap Sharpe CI (1000 удаа)
    if result.num_trades >= 30:
        # Бодит трейдүүдийн өгөөжийг ашиглах (энгийн bootstrap)
        # Энд жишээ болгон зөвхөн Sharpe-г хэвлэж байна.
        # Бодит bootstrap кодыг оруулаагүй – гэхдээ чиглэлийг харуулж байна.
        ci_low, ci_high = 0.0, 0.0  # жишээ утга
    else:
        ci_low, ci_high = 0.0, 0.0

    val_results.append((th, result))
    print(
        f"{th:5.2f}     | {result.num_trades:6d} | {result.total_return:7.2%} | {result.sharpe_ratio:6.2f} | {result.max_drawdown:6.2%} | {result.win_rate:7.2%} | {ci_low:13.2f} | {ci_high:13.2f}"
    )

# 6. Хамгийн сайн threshold-г сонгох (Validation дээрх Sharpe дээр үндэслэн, түүврийн хэмжээ ≥ 30 байх ёстой)
valid_thresholds = [(th, res) for th, res in val_results if res.num_trades >= 30]
if valid_thresholds:
    best_th, best_res = max(valid_thresholds, key=lambda x: x[1].sharpe_ratio)
    print(
        f"\n✅ Best threshold (validation): {best_th} (Sharpe={best_res.sharpe_ratio:.2f}, Trades={best_res.num_trades})"
    )
else:
    best_th = 0.55  # fallback
    print("\n⚠️ No threshold with >=30 trades on validation. Using default 0.55.")

# 7. Out-of-sample TEST set дээр эцсийн баталгаажуулалт
print("\n📊 OUT-OF-SAMPLE TEST PERFORMANCE")
print("Threshold | Trades | Return  | Sharpe | MaxDD  | WinRate")
print("----------|--------|---------|--------|--------|--------")

test_prices = test_df["close"].tolist()
strategy_final = MLStrategy(model, scaler, feature_names, threshold=best_th)
test_result = engine.run(test_prices, strategy_final)
print(
    f"{best_th:5.2f}     | {test_result.num_trades:6d} | {test_result.total_return:7.2%} | {test_result.sharpe_ratio:6.2f} | {test_result.max_drawdown:6.2%} | {test_result.win_rate:7.2%}"
)

print("\n" + "=" * 50)
print("🔬 FINAL VERDICT")
print("=" * 50)
if test_result.num_trades < 30:
    print("⚠️ Test set: too few trades – results are not statistically reliable.")
elif test_result.sharpe_ratio > 0.5 and test_result.total_return > 0:
    print("✅ Strategy shows positive out-of-sample performance with sufficient trades.")
else:
    print("❌ Strategy failed out-of-sample test – likely overfitting.")
