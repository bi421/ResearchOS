import sys
from pathlib import Path

# Таны C++ backend-ийн замыг нэмэх
sys.path.insert(0, str(Path("cpp_quant_engine/python").resolve()))
sys.path.insert(0, str(Path("cpp_quant/python").resolve()))

print("=" * 60)
print("🚀 C++ BACKEND: Таны cpp_quant_engine системийг ашиглаж байна...")
print("=" * 60)

try:
    # Таны C++ модулийг импортлох (.pyd файл)
    import cpp_quant_engine

    print("✅ C++ Backend амжилттай ачаалагдлаа!")

    # Өгөгдлийн файл
    data_file = Path("data/curated/xauusd/xauusd_h1_2026_recent_real.csv").resolve()
    print(f"📂 Ашиглах өгөгдөл: {data_file.name}")

    # Таны C++ системийн ResearchRunner эсвэл Optimizer-ийг дуудах (Жишээ API)
    # Хэрэв таны API өөр нэртэй бол доорх хэсгийг тохируулна
    if hasattr(cpp_quant_engine, "ResearchRunner"):
        runner = cpp_quant_engine.ResearchRunner()
        runner.load_data(str(data_file))

        # H1-д зориулсан параметрүүд
        horizons = [1, 3, 5, 10, 20]
        thresholds = [0.0000, 0.0010, 0.0020, 0.0030]

        print("\n🔄 C++ Engine дээр sweep эхэлж байна...")
        # Таны C++ кодод тохируулан run_sweep эсвэл optimize гэсэн функцийг дуудна
        # results = runner.run_sweep(horizons, thresholds)
        print(
            "⚠️ Санамж: C++ API-ын яг нарийн функцийн нэрийг (жишээ нь: run_sweep, optimize) баталгаажуулсны дараа бүрэн ажиллуулна."
        )

    elif hasattr(cpp_quant_engine, "Optimizer"):
        print("✅ Optimizer олдлоо. Үүнийг ашиглан sweep хийнэ.")
    else:
        print("\n🔍 C++ Модульд дараах функцүүд/классууд байна:")
        print([attr for attr in dir(cpp_quant_engine) if not attr.startswith("_")])

except ImportError as e:
    print(f"❌ C++ Backend импортлох алдаа: {e}")
    print("   PYTHONPATH зөв тохируулагдсан эсэхийг шалгана уу.")
except Exception as e:
    print(f"❌ Гүйцэтгэх үеийн алдаа: {e}")

print("=" * 60)
