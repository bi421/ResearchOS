import os
from pathlib import Path

# Үндсэн зам
BASE = Path(r"C:\Users\User\Desktop\ResearchOS")
STRATEGY_DIR = BASE / "researchos" / "strategy"
DASHBOARD_DIR = BASE / "src" / "dashboard"

# Директори үүсгэх
STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

print(" Директори бэлэн:")
print(f"   {STRATEGY_DIR}")
print(f"   {DASHBOARD_DIR}")
print()

# ============================================
# 1. GRID SEARCH СТРАТЕГИ
# ============================================
strategy_code = '''"""
Grid Search Strategy - C++ Engine Integration
MA period + RSI threshold оновчлол
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cpp_quant_engine" / "python"))

import cpp_quant_engine.cpp_quant_backend as backend

class GridSearchStrategy:
    """C++ engine дээр grid search хийх стратеги"""
    
    def __init__(self):
        self.engine = backend.Backend()
        self.results = []
    
    def run_grid_search(self, ma_periods=[10, 20, 50], rsi_thresholds=[30, 50, 70]):
        """MA period + RSI threshold комбинаци бүрээр backtest"""
        print(f"🔍 Grid Search эхэлж байна: {len(ma_periods)} x {len(rsi_thresholds)} = {len(ma_periods)*len(rsi_thresholds)} комбинаци")
        
        for ma in ma_periods:
            for rsi in rsi_thresholds:
                # C++ engine-д параметр илгээх
                result = self.engine.run_backtest(
                    strategy="ma_rsi",
                    ma_period=ma,
                    rsi_threshold=rsi,
                    initial_capital=100000
                )
                
                self.results.append({
                    "ma_period": ma,
                    "rsi_threshold": rsi,
                    "sharpe_ratio": result.get("sharpe_ratio", 0),
                    "max_drawdown": result.get("max_drawdown", 0),
                    "total_return": result.get("total_return", 0)
                })
        
        # Үр дүн эрэмбэлэх
        self.results.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
        return self.results
    
    def get_best_params(self):
        """Шилдэг параметр буцаах"""
        if not self.results:
            return None
        return self.results[0]

# Тест
if __name__ == "__main__":
    strategy = GridSearchStrategy()
    results = strategy.run_grid_search([10, 20], [30, 70])
    print(f"✅ {len(results)} backtest дууссан")
    print(f"🏆 Шилдэг: {strategy.get_best_params()}")
'''

strategy_file = STRATEGY_DIR / "grid_search_strategy.py"
strategy_file.write_text(strategy_code, encoding="utf-8")
print(f"✅ Стратеги үүсгэсэн: {strategy_file}")

# ============================================
# 2. FASTAPI + WEBSOCKET DASHBOARD
# ============================================
dashboard_code = '''"""
Real-time Dashboard - FastAPI + WebSocket + C++ Engine
"""
import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cpp_quant_engine" / "python"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from researchos.strategy.grid_search_strategy import GridSearchStrategy

app = FastAPI(title="ResearchOS Real-time Dashboard")

# HTML Dashboard (No Jinja)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ResearchOS Quant Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .status { padding: 10px; background: #4CAF50; color: white; border-radius: 5px; margin-bottom: 20px; }
        .results { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #2196F3; color: white; }
        #chart { width: 100%; height: 400px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 ResearchOS Quant Engine Dashboard</h1>
        <div class="status" id="status"> WebSocket холбогдсон</div>
        
        <div class="results">
            <h2>📊 Grid Search Үр Дүн</h2>
            <table id="resultsTable">
                <thead>
                    <tr>
                        <th>MA Period</th>
                        <th>RSI Threshold</th>
                        <th>Sharpe Ratio</th>
                        <th>Max Drawdown</th>
                        <th>Total Return</th>
                    </tr>
                </thead>
                <tbody id="resultsBody">
                </tbody>
            </table>
        </div>
        
        <div id="chart"></div>
    </div>

    <script>
        // WebSocket холболт
        const ws = new WebSocket(ws:///ws/grid-search);
        
        ws.onopen = () => {
            console.log("WebSocket холбогдсон");
            document.getElementById("status").innerHTML = "🟢 WebSocket холбогдсон";
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateTable(data.results);
            updateChart(data.results);
        };
        
        ws.onerror = (error) => {
            document.getElementById("status").innerHTML = "🔴 WebSocket алдаа";
            console.error("WebSocket алдаа:", error);
        };
        
        function updateTable(results) {
            const tbody = document.getElementById("resultsBody");
            tbody.innerHTML = "";
            results.forEach(r => {
                const row = <tr>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td>%</td>
                    <td>%</td>
                </tr>;
                tbody.innerHTML += row;
            });
        }
        
        function updateChart(results) {
            const maPeriods = results.map(r => r.ma_period);
            const sharpeRatios = results.map(r => r.sharpe_ratio);
            
            const data = [{
                x: maPeriods,
                y: sharpeRatios,
                type: 'bar',
                marker: { color: '#2196F3' }
            }];
            
            const layout = {
                title: 'MA Period vs Sharpe Ratio',
                xaxis: { title: 'MA Period' },
                yaxis: { title: 'Sharpe Ratio' }
            };
            
            Plotly.newPlot('chart', data, layout);
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Үндсэн dashboard хуудас"""
    return DASHBOARD_HTML

@app.websocket("/ws/grid-search")
async def websocket_grid_search(websocket: WebSocket):
    """WebSocket-ээр grid search үр дүн бодит цагаар дамжуулах"""
    await websocket.accept()
    
    try:
        # Стратеги үүсгэх
        strategy = GridSearchStrategy()
        
        # WebSocket-оор мэдэгдэл илгээх
        await websocket.send_json({
            "status": "started",
            "message": "Grid search эхэлж байна..."
        })
        
        # Grid search ажиллуулах
        results = strategy.run_grid_search(
            ma_periods=[10, 20, 50],
            rsi_thresholds=[30, 50, 70]
        )
        
        # Үр дүнг JSON болгож илгээх
        await websocket.send_json({
            "status": "completed",
            "results": results,
            "best_params": strategy.get_best_params()
        })
        
    except Exception as e:
        await websocket.send_json({
            "status": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    print("🚀 Dashboard сервер эхэлж байна: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

dashboard_file = DASHBOARD_DIR / "dashboard_realtime.py"
dashboard_file.write_text(dashboard_code, encoding="utf-8")
print(f"✅ Dashboard үүсгэсэн: {dashboard_file}")

# ============================================
# 3. INTEGRATION ТЕСТ СКРИПТ
# ============================================
test_code = '''"""
Integration Test - Стратеги + Dashboard шалгах
"""
import sys
from pathlib import Path

# PYTHONPATH тохируулах
BASE = Path(r"C:\\Users\\User\\Desktop\\ResearchOS")
sys.path.insert(0, str(BASE / "cpp_quant_engine" / "python"))
sys.path.insert(0, str(BASE))

def test_strategy():
    """Стратеги тест"""
    print("\\n" + "="*60)
    print(" ТЕСТ 1: Grid Search Стратеги")
    print("="*60)
    
    from researchos.strategy.grid_search_strategy import GridSearchStrategy
    
    strategy = GridSearchStrategy()
    results = strategy.run_grid_search([10, 20], [30, 70])
    
    print(f"✅ {len(results)} backtest амжилттай")
    print(f"🏆 Шилдэг параметр: {strategy.get_best_params()}")
    
    assert len(results) == 4, f"4 үр дүн байх ёстой, {len(results)} олдсон"
    print("✅ Стратеги тест PASSED")
    return True

def test_dashboard_import():
    """Dashboard импорт тест"""
    print("\\n" + "="*60)
    print("🧪 ТЕСТ 2: Dashboard Импорт")
    print("="*60)
    
    try:
        from src.dashboard.dashboard_realtime import app
        print(f"✅ FastAPI app импорт амжилттай: {app.title}")
        print("✅ Dashboard импорт тест PASSED")
        return True
    except Exception as e:
        print(f"❌ Dashboard импорт алдаа: {e}")
        return False

def main():
    print("\\n" + "="*60)
    print("🚀 RESEARCHOS INTEGRATION TEST")
    print("="*60)
    
    results = []
    
    # Тест 1: Стратеги
    try:
        results.append(("Стратеги", test_strategy()))
    except Exception as e:
        print(f"❌ Стратеги тест FAILED: {e}")
        results.append(("Стратеги", False))
    
    # Тест 2: Dashboard
    try:
        results.append(("Dashboard", test_dashboard_import()))
    except Exception as e:
        print(f"❌ Dashboard тест FAILED: {e}")
        results.append(("Dashboard", False))
    
    # Дүгнэлт
    print("\\n" + "="*60)
    print("📊 ИНТЕГРАЦИЙН ТЕСТИЙН ҮР ДҮН")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\\n БҮХ ТЕСТ АМЖИЛТТАЙ!")
        print("\\n🚀 Dashboard эхлүүлэх:")
        print("   python src/dashboard/dashboard_realtime.py")
        print("\\n Хандах хаяг: http://localhost:8000")
    else:
        print("\\n⚠️  Зарим тест FAILED. Дээрх алдааг шалгана уу.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''

test_file = BASE / "test_integration.py"
test_file.write_text(test_code, encoding="utf-8")
print(f"✅ Integration тест үүсгэсэн: {test_file}")

print("\\n" + "="*60)
print("✅ БҮХ ФАЙЛ АМЖИЛТТАЙ ҮСГЭГДЛЭЭ!")
print("="*60)
print("\\n📁 Үүсгэсэн файлууд:")
print(f"   1. {strategy_file}")
print(f"   2. {dashboard_file}")
print(f"   3. {test_file}")
print("\\n🚀 Дараагийн алхам:")
print("   python test_integration.py")
print()
