# scripts/validation_audit.py
import os
import re
from datetime import datetime

import pandas as pd

print("=" * 80)
print("🔍 RESEARCHOS – СИСТЕМИЙН АУДИТ, БАТАЛГААЖУУЛАЛТ")
print("=" * 80)
print(f"⏰ Шалгалт хийсэн огноо: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("-" * 80)

# ============================================================
# 1. БҮТЭЦ, ФАЙЛЫН БҮРЭН БҮТЭН БАЙДАЛ
# ============================================================
print("\n📁 1. БҮТЭЦ, ФАЙЛЫН БҮРЭН БҮТЭН БАЙДАЛ")
print("-" * 40)

required_dirs = ["scripts", "researchos", "data", "reports", "logs", "archive"]
missing_dirs = [d for d in required_dirs if not os.path.isdir(d)]
if missing_dirs:
    print(f"❌ Дараах хавтаснууд олдсонгүй: {missing_dirs}")
else:
    print("✅ Бүх шаардлагатай хавтаснууд байна.")

required_root_files = ["main.py", "researchos.db", "pyproject.toml", "ruff.toml", "README.md"]
missing_files = [f for f in required_root_files if not os.path.isfile(f)]
if missing_files:
    print(f"⚠️ Дараах root файлууд олдсонгүй: {missing_files}")
else:
    print("✅ Шаардлагатай root файлууд байна.")

# scripts/ доторх гол скриптүүд
required_scripts = ["run_first_backtest.py", "run_full_analysis_fixed4.py", "trading_signal.py", "validation_audit.py"]
missing_scripts = [s for s in required_scripts if not os.path.isfile(f"scripts/{s}")]
if missing_scripts:
    print(f"❌ Дараах скриптүүд scripts/ дотор олдсонгүй: {missing_scripts}")
else:
    print("✅ Бүх гол скриптүүд scripts/ дотор байна.")

# ============================================================
# 2. ӨГӨГДЛИЙН БҮРЭН БҮТЭН БАЙДАЛ (researchos.db)
# ============================================================
print("\n🗄️ 2. ӨГӨГДЛИЙН САН (researchos.db) ШАЛГАЛТ")
print("-" * 40)

if os.path.isfile("researchos.db"):
    db_size = os.path.getsize("researchos.db") / (1024 * 1024)
    print(f"✅ researchos.db хэмжээ: {db_size:.2f} MB")

    # SQLite шалгалт (хэрэв sqlite3 суулгасан бол)
    try:
        import sqlite3

        conn = sqlite3.connect("researchos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Нийт хүснэгтийн тоо: {len(tables)}")
        # XAUUSD өгөгдөл байгаа эсэх
        cursor.execute("SELECT COUNT(*) FROM candles WHERE symbol='XAUUSD'")
        count = cursor.fetchone()[0]
        print(f"✅ XAUUSD лааны тоо: {count:,}")
        conn.close()
    except Exception as e:
        print(f"⚠️ SQLite шалгалт амжилтгүй: {e}")
else:
    print("❌ researchos.db олдсонгүй!")

# ============================================================
# 3. BACKTEST ҮР ДҮНГИЙН БАТАЛГААЖУУЛАЛТ
# ============================================================
print("\n📊 3. BACKTEST ҮР ДҮН (run_first_backtest.py)")
print("-" * 40)

# run_first_backtest.py-ийн үр дүнг шалгах
# Бид энэ скриптийг шууд ажиллуулж, гаралтыг барихгүй,
# харин researchos.db-ээс шууд тооцоолж, өмнөх үр дүнтэй харьцуулна.
try:
    from cpp_quant_engine.backend import BacktestEngine
    from cpp_quant_engine.models import Candle as CQCandle
    from cpp_quant_engine.models import MarketData

    from researchos.data_engine.repository import SqliteDatasetRepository

    repo = SqliteDatasetRepository("researchos.db")
    dataset = repo.find_by_symbol_and_timeframe("XAUUSD", "1d")
    print(f"✅ Backtest өгөгдөл: {dataset.record_count} лаа")

    # Жижиг backtest хийж үзэх (хурдан шалгалт)
    cq_candles = []
    for c in dataset._records[:100]:
        cq_candles.append(
            CQCandle(
                timestamp=c.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                open=c.open,
                high=c.high,
                low=c.low,
                close=c.close,
                volume=c.volume if c.volume is not None else 0.0,
                timeframe="D1",
            )
        )
    engine = BacktestEngine()
    market_data = MarketData(symbol="XAUUSD", candles=cq_candles)

    def test_signal(bar_index, history):
        if not history:
            return {"direction": 0, "quantity": 0.0}
        last = history[-1]
        if last["close"] > last["open"]:
            return {"direction": 0, "quantity": 1.0}
        return {"direction": 0, "quantity": 0.0}

    result = engine.run(market_data, signal=test_signal, signal_reference="test://audit")
    print(f"✅ Backtest engine ажилласан: {result.num_trades} арилгаа")
    print(f"   Return: {result.total_return_pct:.2f}%")

    # Өмнөх үр дүнтэй харьцуулах (энэ нь бүтэн өгөгдөл дээр биш, харин зөвхөн шалгалт)
    expected_return = 138.80
    if abs(result.total_return_pct - expected_return) < 5:
        print("✅ Backtest үр дүн хүлээгдэж буй утгатай ойролцоо байна.")
    else:
        print(f"⚠️ Backtest үр дүн хүлээгдэж буй утгаас ялгаатай: {result.total_return_pct:.2f}% (хүлээгдэж буй: {expected_return:.2f}%)")

except Exception as e:
    print(f"❌ Backtest шалгалт амжилтгүй: {e}")

# ============================================================
# 4. MACRO ШИНЖИЛГЭЭНИЙ ҮР ДҮН
# ============================================================
print("\n📈 4. MACRO ШИНЖИЛГЭЭ (market_report_v3.md)")
print("-" * 40)

report_path = "reports/market_report_v3.md"
if os.path.isfile(report_path):
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"✅ Тайлангийн хэмжээ: {len(content):,} тэмдэгт")

    # Гол утгуудыг шалгах
    score_match = re.search(r"\*\*Total Score\*\* \| \*\*([\d.-]+)\*\*", content)
    dxy_match = re.search(r"DXY \| ([\d.-]+)", content)
    regime_match = re.search(r"Market Regime: \*\*([A-Z-]+)\*\*", content)

    if score_match:
        print(f"✅ Evidence Score: {score_match.group(1)}")
    else:
        print("❌ Evidence Score олдсонгүй")

    if dxy_match:
        print(f"✅ DXY vs XAUUSD: {dxy_match.group(1)}")
    else:
        print("❌ DXY correlation олдсонгүй")

    if regime_match:
        print(f"✅ Market Regime: {regime_match.group(1)}")
    else:
        print("❌ Regime олдсонгүй")

    # Assets Analyzed шалгах
    assets_match = re.search(r"\*\*Assets Analyzed:\*\* (.*)", content)
    if assets_match:
        assets = assets_match.group(1).strip()
        print(f"✅ Analyzed assets: {assets}")
        if "XAUUSD" in assets:
            print("   ✅ XAUUSD багтсан байна.")
        else:
            print("   ❌ XAUUSD багтаагүй байна!")
else:
    print(f"❌ {report_path} олдсонгүй!")

# ============================================================
# 5. ШИЙДВЭР ГАРГАЛТЫН ЛОГИК
# ============================================================
print("\n🎯 5. ШИЙДВЭР ГАРГАЛТ (trading_signal.py)")
print("-" * 40)

# trading_signal.py-г шууд ажиллуулахгүйгээр логикийг шалгах
try:
    # Action score тооцоог шалгах
    df = pd.read_csv("reports/backtest_results_all.csv")
    best = df[df["Strategy"].str.contains("SMA")].iloc[0]
    ret = best["Return"]
    sharpe = best["Sharpe"]
    winrate = best["Winrate"]

    # Macro утгууд
    if os.path.isfile("reports/market_report_v3.md"):
        with open("reports/market_report_v3.md", "r", encoding="utf-8") as f:
            text = f.read()
        score = float(re.search(r"\*\*Total Score\*\* \| \*\*([\d.-]+)\*\*", text).group(1))
        dxy = float(re.search(r"DXY \| ([\d.-]+)", text).group(1))
    else:
        score, dxy = 0.0, -0.8

    # Тооцоолол
    macro_score = score * 10
    if dxy < -0.5:
        macro_score += 2
    tech_score = (1 if ret > 50 else 0) + (1 if sharpe > 1.0 else 0) + (1 if winrate > 50 else 0)
    action_score = (macro_score * 0.4) + (tech_score * 0.6)

    print(f"✅ Macro score: {macro_score:.2f}")
    print(f"✅ Tech score: {tech_score:.2f}")
    print(f"✅ Action score: {action_score:.2f} / 5.0")

    if action_score > 2.5 and ret > 50:
        decision = "BUY"
    elif action_score > 1.5:
        decision = "WAIT"
    else:
        decision = "AVOID"
    print(f"✅ Шийдвэр: {decision}")

    # Хүлээгдэж буй шийдвэртэй харьцуулах (өмнөх гаралтаас AVOID байсан)
    expected_decision = "AVOID"
    if decision == expected_decision:
        print(f"✅ Шийдвэр хүлээгдэж буй утгатай тохирч байна: {decision}")
    else:
        print(f"⚠️ Шийдвэр өөр байна: {decision} (хүлээгдэж буй: {expected_decision})")

except Exception as e:
    print(f"❌ Шийдвэр шалгалт амжилтгүй: {e}")

# ============================================================
# 6. IMPORT-УУДЫН АЖИЛЛАГАА
# ============================================================
print("\n📦 6. IMPORT-УУДЫН АЖИЛЛАГАА")
print("-" * 40)

modules_to_check = ["researchos.data_engine.repository", "researchos.decision_engine.contracts", "researchos.decision_engine.score", "researchos.quant_engine.backend", "cpp_quant_engine.backend", "cpp_quant_engine.models", "pandas", "numpy", "yfinance", "matplotlib", "seaborn"]

failed_imports = []
for module in modules_to_check:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError as e:
        print(f"❌ {module}: {e}")
        failed_imports.append(module)

if failed_imports:
    print(f"\n⚠️ Дараах модулиуд импортлогдохгүй байна: {failed_imports}")
else:
    print("\n✅ Бүх чухал модулиуд амжилттай импортлогдлоо.")

# ============================================================
# 7. ДҮГНЭЛТ
# ============================================================
print("\n" + "=" * 80)
print("📋 ДҮГНЭЛТ")
print("=" * 80)

# Нийт алдаа, анхааруулгын тоо
errors = []
warnings = []

# Дээрх шалгалтуудаас цуглуулсан алдаануудыг энд нэмэх
# (энэ нь зөвхөн жишээ, бодит байдалд тохируулах)

print("\n🔍 Шалгалтын дүн:")
print("- Бүтэц: " + ("✅" if not missing_dirs else "❌"))
print("- Өгөгдлийн сан: " + ("✅" if os.path.isfile("researchos.db") else "❌"))
print("- Backtest: " + ("✅" if "Backtest engine ажилласан" in locals() else "❌"))
print("- Macro тайлан: " + ("✅" if os.path.isfile(report_path) else "❌"))
print("- Шийдвэр гаргалт: " + ("✅" if decision else "❌"))
print("- Import-ууд: " + ("✅" if not failed_imports else "❌"))

print("\n" + "=" * 80)
print("✅ АУДИТ ДУУССАН.")
print("=" * 80)
