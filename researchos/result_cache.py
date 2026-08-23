# researchos/result_cache.py
import json
import subprocess
from datetime import datetime
from pathlib import Path

CACHE_FILE = Path("reports/latest_results.json")


def load_cache():
    """Сүүлийн үр дүнг унших"""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_cache(data):
    """Үр дүнг хадгалах"""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_cache():
    """Шинжилгээг ажиллуулж, кэшийг шинэчлэх"""
    # main.py-г ажиллуулах
    result = subprocess.run(["python", "main.py"], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
    # Эндээс бодит үр дүнг гаргаж авах (жишээнд загвар)
    # Та бодит үр дүнг `trading_signal.py` эсвэл шууд файлаас уншиж болно
    data = {
        "timestamp": datetime.now().isoformat(),
        "status": "success" if result.returncode == 0 else "error",
        "backtest_return": 120.61,  # энэ утгыг динамикаар авах
        "ml_signal": "BUY",
        "decision": "AVOID",
        "reason": "Backtest болон ML найдваргүй",
    }
    # Хэрэв та бодит утгыг файлаас уншихыг хүсвэл:
    try:
        # market_report_v3.md-ээс унших
        with open("reports/market_report_v3.md", "r", encoding="utf-8") as f:
            content = f.read()
        import re

        score = re.search(r"\*\*Total Score\*\* \| \*\*([\d.-]+)\*\*", content)
        if score:
            data["evidence_score"] = float(score.group(1))
        dxy = re.search(r"DXY \| ([\d.-]+)", content)
        if dxy:
            data["dxy_correlation"] = float(dxy.group(1))
        # бусад...
    except Exception:
        pass

    save_cache(data)
    return data
