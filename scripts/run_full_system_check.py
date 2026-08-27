# scripts/run_full_system_check.py
import importlib
import os
import sys
from datetime import datetime

print("=" * 80)
print("🔍 RESEARCHOS – БҮРЭН СИСТЕМИЙН ШАЛГАЛТ")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
errors = []
warnings = []
success = []
print("\n📁 1. БҮТЭЦ, ФАЙЛЫН ШАЛГАЛТ")
print("-" * 40)
required_dirs = ["scripts", "researchos", "data", "reports", "logs", "archive", "cpp_quant_engine"]
for d in required_dirs:
    if os.path.isdir(d):
        print(f"   ✅ {d}/")
        success.append(f"Folder: {d}")
    else:
        print(f"   ❌ {d}/ олдсонгүй!")
        errors.append(f"Missing folder: {d}")
required_root_files = ["main.py", "researchos.db", "pyproject.toml", "README.md"]
for f in required_root_files:
    if os.path.isfile(f):
        print(f"   ✅ {f}")
        success.append(f"File: {f}")
    else:
        print(f"   ❌ {f} олдсонгүй!")
        errors.append(f"Missing file: {f}")
required_scripts = ["run_first_backtest.py", "run_full_analysis_fixed4.py", "trading_signal.py", "run_production_analysis.py", "run_massive_backtest_from_csv.py", "bot_server.py"]
for s in required_scripts:
    if os.path.isfile(f"scripts/{s}"):
        print(f"   ✅ scripts/{s}")
        success.append(f"Script: {s}")
    else:
        print(f"   ⚠️ scripts/{s} олдсонгүй (заавал биш)")
        warnings.append(f"Missing optional script: {s}")
print("\n🗄️ 2. ӨГӨГДЛИЙН САН (researchos.db)")
print("-" * 40)
if os.path.isfile("researchos.db"):
    size_mb = os.path.getsize("researchos.db") / (1024 * 1024)
    print(f"   ✅ Хэмжээ: {size_mb:.2f} MB")
    success.append(f"DB size: {size_mb:.2f} MB")
    try:
        import sqlite3

        conn = sqlite3.connect("researchos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   ✅ Хүснэгтийн тоо: {len(tables)}")
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t[0]}")
            count = cursor.fetchone()[0]
            print(f"      {t[0]}: {count:,} мөр")
        conn.close()
        success.append(f"Tables: {len(tables)}")
    except Exception as e:
        print(f"   ⚠️ SQLite алдаа: {e}")
        warnings.append(f"SQLite: {e}")
else:
    print("   ❌ researchos.db олдсонгүй!")
    errors.append("Missing researchos.db")
print("\n📦 3. PYTHON ИМПОРТУУД")
print("-" * 40)
modules = ["pandas", "numpy", "matplotlib", "seaborn", "yfinance", "xgboost", "sklearn", "telegram", "dotenv", "researchos.data_engine.repository", "researchos.decision_engine.contracts", "researchos.decision_engine.score", "researchos.quant_engine.backend", "cpp_quant_engine.backend", "cpp_quant_engine.models"]
for m in modules:
    try:
        importlib.import_module(m)
        print(f"   ✅ {m}")
        success.append(f"Import: {m}")
    except ImportError as e:
        print(f"   ❌ {m}: {e}")
        errors.append(f"Import failed: {m}")
print("\n📊 4. BACKTEST ШАЛГАЛТ (хурдан)")
print("-" * 40)
try:
    sys.path.insert(0, "cpp_quant_engine/python")
    from cpp_quant_engine.backend import BacktestEngine
    from cpp_quant_engine.models import Candle as CQCandle

    from researchos.data_engine.repository import SqliteDatasetRepository

    repo = SqliteDatasetRepository("researchos.db")
    dataset = repo.find_by_symbol_and_timeframe("XAUUSD", "1d")
    if dataset and dataset.record_count > 0:
        print(f"   ✅ XAUUSD өгөгдөл: {dataset.record_count} лаа")
        cq_candles = []
        for c in dataset._records[:20]:
            cq_candles.append(CQCandle(timestamp=c.timestamp.strftime("%Y-%m-%dT%H:%M:%S"), open=c.open, high=c.high, low=c.low, close=c.close, volume=c.volume if c.volume is not None else 0.0, timeframe="D1"))
        engine = BacktestEngine()

        def test_signal(bar_index, history):
            if not history:
                return {"direction": 0, "quantity": 0.0}
            last = history[-1]
            if last["close"] > last["open"]:
                return {"direction": 0, "quantity": 1.0}
            return {"direction": 0, "quantity": 0.0}

        from cpp_quant_engine.models import MarketData

        md = MarketData(symbol="XAUUSD", candles=cq_candles)
        res = engine.run(md, signal=test_signal)
        print(f"   ✅ C++ Engine ажилласан: {res.num_trades} арилгаа")
        success.append(f"Backtest: {res.num_trades} trades")
    else:
        print("   ❌ Өгөгдөл олдсонгүй")
        errors.append("No XAUUSD data in DB")
except Exception as e:
    print(f"   ❌ Backtest алдаа: {e}")
    errors.append(f"Backtest error: {e}")
print("\n🧠 5. ML ШАЛГАЛТ (хурдан)")
print("-" * 40)
try:
    import pandas as pd
    import xgboost as xgb

    repo = SqliteDatasetRepository("researchos.db")
    dataset = repo.find_by_symbol_and_timeframe("XAUUSD", "1d")
    if dataset and dataset.record_count > 50:
        df = pd.DataFrame([{"close": c.close, "open": c.open, "high": c.high, "low": c.low} for c in dataset._records])
        df["ret"] = df["close"].pct_change()
        df["target"] = (df["close"].shift(-1) > df["open"].shift(-1)).astype(int)
        df = df.dropna()
        if len(df) > 20:
            X = df[["ret"]]
            y = df["target"]
            model = xgb.XGBClassifier(n_estimators=10, max_depth=2)
            model.fit(X.iloc[:-10], y.iloc[:-10])
            acc = model.score(X.iloc[-10:], y.iloc[-10:])
            print(f"   ✅ XGBoost ажилласан: {acc:.2%} (10 test sample)")
            success.append(f"ML: {acc:.2%}")
        else:
            print("   ⚠️ ML-д хангалттай өгөгдөл байхгүй")
            warnings.append("Insufficient data for ML")
    else:
        print("   ❌ ML-д өгөгдөл олдсонгүй")
        errors.append("No data for ML")
except ImportError:
    print("   ⚠️ XGBoost суугаагүй (pip install xgboost)")
    warnings.append("XGBoost not installed")
except Exception as e:
    print(f"   ❌ ML алдаа: {e}")
    errors.append(f"ML error: {e}")
print("\n📄 6. ТАЙЛАН ГАРГАЛТ")
print("-" * 40)
report_files = ["reports/market_report_v3.md", "reports/backtest_results_all.csv"]
for rf in report_files:
    if os.path.isfile(rf):
        size = os.path.getsize(rf)
        print(f"   ✅ {rf} ({size:,} bytes)")
        success.append(f"Report: {os.path.basename(rf)}")
    else:
        print(f"   ⚠️ {rf} олдсонгүй")
        warnings.append(f"Missing report: {rf}")
print("\n🤖 7. TELEGRAM БОТ")
print("-" * 40)
env_files = [".env", "scripts/.env"]
token_found = False
for ef in env_files:
    if os.path.isfile(ef):
        with open(ef, "r") as f:
            content = f.read()
        if "TELEGRAM_BOT_TOKEN" in content:
            token_found = True
            print(f"   ✅ Token олдсон: {ef}")
            success.append(f"Telegram token: {ef}")
            break
if not token_found:
    print("   ⚠️ Telegram токен олдсонгүй (заавал биш)")
    warnings.append("No Telegram token found")
print("\n" + "=" * 80)
print("📋 ДҮГНЭЛТ")
print("=" * 80)
print(f"\n✅ Амжилттай: {len(success)}")
for s in success[:10]:
    print(f"   - {s}")
if len(success) > 10:
    print(f"   ... болон {len(success) - 10} бусад")
print(f"\n⚠️ Анхааруулга: {len(warnings)}")
for w in warnings:
    print(f"   - {w}")
print(f"\n❌ Алдаа: {len(errors)}")
for e in errors:
    print(f"   - {e}")
print("\n" + "=" * 80)
if errors:
    print("🔴 СИСТЕМ ЗАРИМ АЛДААТАЙ – ДЭЭРХ АЛДААНУУДЫГ ЗАСНА УУ.")
elif warnings:
    print("🟡 СИСТЕМ АЖИЛЛАЖ БАЙНА, ГЭХДЭЭ ЗАРИМ АНХААРУУЛГА БАЙНА.")
else:
    print("🟢 СИСТЕМ БҮРЭН АЖИЛЛАГААТАЙ, АЛДАА, АНХААРУУЛГА БАЙХГҮЙ.")
print("=" * 80)
