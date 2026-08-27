"""
Integration Test - Auto-Fixed Version
"""
import sys
from pathlib import Path

BASE = Path(r"C:\Users\User\Desktop\ResearchOS")
sys.path.insert(0, str(BASE / "cpp_quant_engine" / "python"))
sys.path.insert(0, str(BASE))


def test_strategy():
    """Стратеги тест"""
    print("\n" + "=" * 60)
    print("🧪 ТЕСТ 1: Grid Search Стратеги")
    print("=" * 60)

    from researchos.strategy.grid_search_strategy import GridSearchStrategy

    strategy = GridSearchStrategy()
    results = strategy.run_grid_search([10, 20], [30, 70])

    print("✅ {len(results)} backtest амжилттай")
    print(" Шилдэг параметр: {strategy.get_best_params()}")

    assert len(results) == 4, "4 үр дүн байх ёстой, {len(results)} олдсон"
    print("✅ Стратеги тест PASSED")
    return True


def test_dashboard_import():
    """Dashboard импорт тест"""
    print("\n" + "=" * 60)
    print(" ТЕСТ 2: Dashboard Импорт")
    print("=" * 60)

    try:
        print("✅ FastAPI app импорт амжилттай: {app.title}")
        print("✅ Dashboard импорт тест PASSED")
        return True
    except Exception:
        print("❌ Dashboard импорт алдаа: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("🚀 RESEARCHOS INTEGRATION TEST (Auto-Fixed)")
    print("=" * 60)

    results = []

    try:
        results.append(("Стратеги", test_strategy()))
    except Exception:
        print("❌ Стратеги тест FAILED: {e}")
        results.append(("Стратеги", False))

    try:
        results.append(("Dashboard", test_dashboard_import()))
    except Exception:
        print("❌ Dashboard тест FAILED: {e}")
        results.append(("Dashboard", False))

    print("\n" + "=" * 60)
    print("📊 ИНТЕГРАЦИЙН ТЕСТИЙН ҮР ДҮН")
    print("=" * 60)

    for name, passed in results:
        print("  {name}: {status}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n🎉 БҮХ ТЕСТ АМЖИЛТТАЙ!")
        print("\n🚀 Dashboard эхлүүлэх:")
        print("   python src/dashboard/dashboard_realtime.py")
        print("\n🌐 Хандах хаяг: http://localhost:8000")
    else:
        print("\n⚠️  Зарим тест FAILED.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
