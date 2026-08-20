import sys
import warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, 'cpp_quant')

import pandas as pd
import numpy as np
import yfinance as yf
import glob
import time
from joblib import Parallel, delayed
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from cpp_quant import run_ml_backtest_cpp

print("="*60)
print("🚀 SEQUENTIAL TESTING: ALL ASSETS & TIMEFRAMES (FINAL)")
print("="*60)

# =============================================
# 1. ӨГӨГДӨЛ АЧААЛАХ ФУНКЦУУД
# =============================================
def get_macro(start='2021-01-01', end='2026-08-20'):
    print("📊 Fetching macro data (DXY, VIX)...")
    macro = yf.download(['DX-Y.NYB', '^VIX'], start=start, end=end, progress=False)['Close']
    macro.columns = ['dxy', 'vix']
    return macro

def load_xauusd(timeframe='4h'):
    files = glob.glob('data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv')
    df = pd.concat([pd.read_csv(f, sep=';', header=None,
                                names=['datetime','open','high','low','close','volume'])
                    for f in files], ignore_index=True)
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S')
    df = df.set_index('datetime')
    if timeframe == '4h':
        return df.resample('4h').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
    else:
        return df.resample('D').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()

def load_btc(timeframe='4h'):
    print(f"📊 Fetching BTC-USD {timeframe}...")
    ticker = yf.Ticker("BTC-USD")
    df = ticker.history(start='2021-01-01', end='2026-08-20')
    # df columns: Open, High, Low, Close, Volume (capitalized)
    if timeframe == '4h':
        df_h = df.resample('4h').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
    else:
        df_h = df.resample('D').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
    df_h.columns = ['open','high','low','close','volume']  # rename to lowercase
    return df_h

# =============================================
# 2. FEATURE GENERATION
# =============================================
def make_features(df):
    df = df.copy()
    close = df['close']
    df['ret1'] = close.pct_change()
    for lag in [1,2,3,5,10,20]:
        df[f'ret_lag_{lag}'] = df['ret1'].shift(lag)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    exp1, exp2 = close.ewm(span=12).mean(), close.ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_diff'] = df['macd'] - df['macd_signal']
    mean, std = close.rolling(20).mean(), close.rolling(20).std()
    df['bb_pos'] = (close - mean + 2*std) / (4*std)
    df['volatility'] = df['ret1'].rolling(20).std()
    if 'dxy' in df.columns:
        df['dxy_return'] = df['dxy'].pct_change()
        df['vix_return'] = df['vix'].pct_change()
    df['target'] = (close.shift(-1) > close).astype(int)
    df = df.replace([np.inf, -np.inf], np.nan).ffill().fillna(0)
    return df

# =============================================
# 3. PIPELINE
# =============================================
def run_pipeline(df_h, macro_df, name):
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {name}")
    print(f"{'='*60}")
    print(f"Data: {len(df_h)} bars")
    
    df_h = df_h.join(macro_df, how='inner')
    print(f"After macro merge: {len(df_h)} bars")
    
    train_mask = df_h.index.year <= 2023
    val_mask = df_h.index.year == 2024
    test_mask = df_h.index.year >= 2025
    train_df, val_df, test_df = df_h[train_mask], df_h[val_mask], df_h[test_mask]
    print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    
    if len(train_df) < 100 or len(val_df) < 50:
        print("❌ Хэт цөөн өгөгдөл, алгасаж байна.")
        return None
    
    train_feat = make_features(train_df)
    val_feat = make_features(val_df)
    test_feat = make_features(test_df)
    feature_cols = [c for c in train_feat.columns if c != 'target']
    X_train, y_train = train_feat[feature_cols].values, train_feat['target'].values
    X_val, y_val = val_feat[feature_cols].values, val_feat['target'].values
    X_test, y_test = test_feat[feature_cols].values, test_feat['target'].values
    
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)
    
    model = XGBClassifier(n_estimators=80, max_depth=5, learning_rate=0.05,
                          subsample=0.8, colsample_bytree=0.8,
                          random_state=42, use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train_s, y_train, eval_set=[(X_val_s, y_val)], verbose=False)
    print(f"Train acc: {model.score(X_train_s, y_train):.2%}, Val acc: {model.score(X_val_s, y_val):.2%}")
    
    thresholds = [0.50, 0.55, 0.58, 0.60, 0.62]
    def eval_th(th):
        val_probs = model.predict_proba(X_val_s)[:, 1]
        val_prices = val_df['close'].values.tolist()
        res = run_ml_backtest_cpp(val_prices, val_probs.tolist(), th)
        return th, {'trades': res[4], 'sharpe': res[1], 'return': res[0], 'dd': res[2], 'wr': res[3]}
    
    print("🔍 Grid search (C++ turbo)...")
    start = time.time()
    results = Parallel(n_jobs=-1, prefer='threads')(delayed(eval_th)(th) for th in thresholds)
    best_sharpe, best_th = -999, 0.55
    for th, res in results:
        if res['trades'] >= 15 and res['sharpe'] > best_sharpe:
            best_sharpe, best_th = res['sharpe'], th
    print(f"⏱️ Grid time: {time.time()-start:.3f}s, Best: {best_th} (Sharpe={best_sharpe:.2f})")
    
    test_probs = model.predict_proba(X_test_s)[:, 1]
    test_prices = test_df['close'].values.tolist()
    res_test = run_ml_backtest_cpp(test_prices, test_probs.tolist(), best_th)
    
    print("\n📊 OUT-OF-SAMPLE TEST (2025-2026)")
    print(f"Trades: {res_test[4]}")
    print(f"Return: {res_test[0]:.2%}")
    print(f"Sharpe: {res_test[1]:.2f}")
    print(f"Max DD: {res_test[2]:.2%}")
    print(f"Win Rate: {res_test[3]:.2%}")
    
    status = "✅ SUCCESS" if res_test[4] >= 30 and res_test[1] > 0.5 else "❌ FAILED"
    print(status)
    
    return {
        'name': name,
        'trades': res_test[4],
        'return': res_test[0],
        'sharpe': res_test[1],
        'max_dd': res_test[2],
        'win_rate': res_test[3],
        'status': status
    }

# =============================================
# 4. MAIN – ДЭС ДАРААЛАЛ
# =============================================
macro_df = get_macro()
results = []

print("\n" + "="*60)
print("📌 [1/3] XAUUSD DAILY")
df_xau_daily = load_xauusd('daily')
res = run_pipeline(df_xau_daily, macro_df, "XAUUSD Daily")
if res: results.append(res)

print("\n" + "="*60)
print("📌 [2/3] BTC-USD 4H")
df_btc_4h = load_btc('4h')
res = run_pipeline(df_btc_4h, macro_df, "BTC-USD 4h")
if res: results.append(res)

print("\n" + "="*60)
print("📌 [3/3] BTC-USD DAILY")
df_btc_daily = load_btc('daily')
res = run_pipeline(df_btc_daily, macro_df, "BTC-USD Daily")
if res: results.append(res)

# =============================================
# 5. ЭЦСИЙН ТАЙЛАН
# =============================================
print("\n" + "="*60)
print("🏆 ЭЦСИЙН ХАРЬЦУУЛАЛТ")
print("="*60)
print(f"{'Asset/Time':15} | {'Trades':6} | {'Return':8} | {'Sharpe':7} | {'MaxDD':8} | {'Status'}")
print("-"*60)
for r in results:
    print(f"{r['name']:15} | {r['trades']:6d} | {r['return']:8.2%} | {r['sharpe']:7.2f} | {r['max_dd']:8.2%} | {r['status']}")

best = max(results, key=lambda x: x['sharpe']) if results else None
if best:
    print("\n" + "="*60)
    print(f"✅ ХАМГИЙН САЙН: {best['name']} (Sharpe={best['sharpe']:.2f})")
    print("="*60)
    
    if best['sharpe'] > 0.5 and best['trades'] >= 30:
        print("🎉 Энэ стратегийг бодит арилжаанд ашиглах боломжтой!")
    elif best['sharpe'] > 0:
        print("⚠️ Sharpe эерэг ч, хангалттай өндөр биш байна. LSTM руу шилжих шаардлагатай.")
    else:
        print("❌ Бүх тест бүтэлгүйтсэн. LSTM руу шилжих цаг боллоо.")
