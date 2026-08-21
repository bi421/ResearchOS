import numpy as np
import pandas as pd

from researchos.data_engine.repository import SqliteDatasetRepository


# === 1. ӨГӨГДЛИЙН БҮРЭН БАЙДАЛ (DATA INTEGRITY) ===
def check_data_integrity():
    print("🔍 [1/4] Өгөгдлийн бүрэн байдлыг шалгаж байна...")
    repo = SqliteDatasetRepository("researchos.db")
    dataset = repo.find_by_symbol_and_timeframe("XAUUSD", "1d")
    if not dataset:
        print("❌ XAUUSD өгөгдөл олдсонгүй")
        return None

    df = pd.DataFrame([{"date": r.timestamp, "close": r.close} for r in dataset._records])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")

    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")
    missing_days = full_range.difference(df.index)
    missing_pct = len(missing_days) / len(full_range) * 100

    returns = df["close"].pct_change().dropna()
    outliers = returns[abs(returns) > returns.std() * 3]

    print(f"   ✅ Нийт өдөр: {len(full_range)}")
    print(f"   ⚠️  Алга болсон өдөр: {len(missing_days)} ({missing_pct:.2f}%)")
    print(f"   ⚠️  Хэвийн бус өөрчлөлт: {len(outliers)}")

    return {
        "total_days": len(full_range),
        "missing_days": len(missing_days),
        "missing_pct": missing_pct,
        "outliers": len(outliers),
    }


# === 2. БЭКТЕСТИЙН БАТЛАГА (Backtest Validation) ===
def run_validation_backtest(sma_short, sma_long):
    repo = SqliteDatasetRepository("researchos.db")
    dataset = repo.find_by_symbol_and_timeframe("XAUUSD", "1d")
    if not dataset:
        return None

    df = pd.DataFrame([{"close": r.close} for r in dataset._records])
    df["sma_short"] = df["close"].rolling(sma_short).mean()
    df["sma_long"] = df["close"].rolling(sma_long).mean()
    df["signal"] = 0
    df.loc[df["sma_short"] > df["sma_long"], "signal"] = 1
    df.loc[df["sma_short"] <= df["sma_long"], "signal"] = -1

    position = 0
    trades = []
    for i in range(1, len(df)):
        if df["signal"].iloc[i] == 1 and position == 0:
            entry = df["close"].iloc[i]
            position = 1
        elif df["signal"].iloc[i] == -1 and position == 1:
            exit_ = df["close"].iloc[i]
            trades.append((exit_ - entry) / entry)
            position = 0

    if not trades:
        return {"return": 0, "trades": 0, "win_rate": 0}

    returns = pd.Series(trades)
    total_return = (1 + returns).prod() - 1
    win_rate = (returns > 0).sum() / len(returns)

    return {"return": total_return, "trades": len(trades), "win_rate": win_rate, "returns": returns}


# === 3. ПАРАМЕТРИЙН ТОГТВОРТОЙ БАЙДАЛ (Sensitivity) ===
def sensitivity_analysis():
    print("🔍 [2/4] Параметрийн тогтвортой байдлыг шалгаж байна...")
    variants = [(5, 20), (10, 30), (15, 45), (20, 50), (30, 70)]
    results = []
    for short, long in variants:
        res = run_validation_backtest(short, long)
        if res:
            results.append(
                {
                    "params": f"SMA {short}/{long}",
                    "return": res["return"] * 100,
                    "trades": res["trades"],
                    "win_rate": res["win_rate"] * 100,
                }
            )
            print(
                f"   {short}/{long}: Return {res['return'] * 100:.1f}%, Trades {res['trades']}, Win Rate {res['win_rate'] * 100:.1f}%"
            )

    return results


# === 4. МОНТЕ КАРЛО СИМУЛЯЦИ (Санамсаргүй харьцуулалт) ===
def monte_carlo_validation(actual_returns):
    print("🔍 [3/4] Монте Карло симуляци хийж байна (санамсаргүй арилжаатай харьцуулалт)...")
    if not actual_returns:
        return None

    actual_returns = np.array(actual_returns)
    actual_mean = np.mean(actual_returns)

    random_means = []
    for _ in range(10000):
        random_returns = np.random.normal(0, np.std(actual_returns), len(actual_returns))
        random_means.append(np.mean(random_returns))

    p_value = (np.array(random_means) > actual_mean).sum() / 10000
    print(f"   Бодит дундаж өгөөж: {actual_mean:.4f}")
    print(f"   Санамсаргүйн P-Value: {p_value:.4f}")
    print(f"   {'✅ Стратеги ач холбогдолтой' if p_value < 0.05 else '⚠️ Стратеги санамсаргүй байж болзошгүй'}")

    return p_value


# === 5. BUY & HOLD ХАРЬЦУУЛАЛТ ===
def compare_to_buy_hold():
    print("🔍 [4/4] Buy & Hold-той харьцуулж байна...")
    repo = SqliteDatasetRepository("researchos.db")
    dataset = repo.find_by_symbol_and_timeframe("XAUUSD", "1d")
    if not dataset:
        return None

    df = pd.DataFrame([{"close": r.close} for r in dataset._records])
    buy_hold_return = (df["close"].iloc[-1] / df["close"].iloc[0]) - 1

    res = run_validation_backtest(10, 30)
    if res:
        diff = res["return"] - buy_hold_return
        print(f"   Buy & Hold Return: {buy_hold_return * 100:.2f}%")
        print(f"   Strategy Return: {res['return'] * 100:.2f}%")
        print(f"   Зөрүү: {diff * 100:.2f}%")
        print(f"   {'✅ Стратеги Buy & Hold-оос илүү' if diff > 0 else '⚠️ Стратеги Buy & Hold-оос муу'}")
        return {"buy_hold": buy_hold_return, "strategy": res["return"], "diff": diff}
    return None


# === 6. ДҮГНЭЛТ (FINAL VERDICT) ===
def generate_trust_report(results):
    print("\n" + "=" * 50)
    print("🏆 ТҮЛШҮҮРЛЭЛТИЙН ДҮГНЭЛТ")
    print("=" * 50)

    score = 0
    max_score = 0

    if results["integrity"]:
        max_score += 10
        if results["integrity"]["missing_pct"] < 5:
            score += 10
            print("✅ Өгөгдөл: Бүрэн (Алдагдал 5%-с бага)")
        else:
            print("⚠️ Өгөгдөл: Дунд зэрэг (Алдагдал 5%-с их)")

    if results["sensitivity"]:
        max_score += 10
        returns = [r["return"] for r in results["sensitivity"]]
        std_dev = np.std(returns)
        if std_dev < 10:
            score += 10
            print("✅ Параметр: Тогтвортой (Стандарт хазайлт 10%-с бага)")
        else:
            print("⚠️ Параметр: Тогтворгүй (Стандарт хазайлт 10%-с их)")

    if results["p_value"] is not None:
        max_score += 10
        if results["p_value"] < 0.05:
            score += 10
            print("✅ Статистик: Ач холбогдолтой (p < 0.05)")
        else:
            print("⚠️ Статистик: Ач холбогдолгүй (p >= 0.05)")

    if results["benchmark"]:
        max_score += 10
        if results["benchmark"]["diff"] > 0:
            score += 10
            print("✅ Харьцуулалт: Стратеги Buy & Hold-оос илүү")
        else:
            print("⚠️ Харьцуулалт: Стратеги Buy & Hold-оос муу")

    trust_pct = (score / max_score) * 100 if max_score > 0 else 0

    print("\n" + "-" * 30)
    if trust_pct >= 80:
        print(f"🔥 Итгэх түвшин: {trust_pct:.0f}% → САЙН (Та үр дүнд итгэж болно)")
    elif trust_pct >= 50:
        print(f"⚠️  Итгэх түвшин: {trust_pct:.0f}% → ДУНД (Болгоомжтой хандах, нэмэлт шалгалт хийх)")
    else:
        print(f"❌ Итгэх түвшин: {trust_pct:.0f}% → МУУ (Үр дүнд итгэх боломжгүй)")

    print("=" * 50)
    print(f"📊 Шалгуур үзүүлэлт: {score}/{max_score}")

    return trust_pct


# === MAIN ===
if __name__ == "__main__":
    print("🚀 ДАВХАР ШҮҮЛТҮҮР АЖИЛЛУУЛАЛТ")
    print("=" * 40)

    results = {}

    results["integrity"] = check_data_integrity()
    results["sensitivity"] = sensitivity_analysis()

    base_res = run_validation_backtest(10, 30)
    if base_res:
        results["p_value"] = monte_carlo_validation(base_res["returns"].tolist())
    else:
        results["p_value"] = None

    results["benchmark"] = compare_to_buy_hold()

    generate_trust_report(results)

    print("\n📌 Зөвлөмж: Бусад хөрөнгө (BTCUSD, AAPL)-өөр туршиж, үр дүнг харьцуул.")
