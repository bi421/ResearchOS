from pathlib import Path

dashboard_code = '''"""
Real-time Dashboard - FastAPI + WebSocket + C++ Engine (FIXED)
"""
import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from pathlib import Path
import sys
import random

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cpp_quant_engine" / "python"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from researchos.strategy.grid_search_strategy import GridSearchStrategy
    USE_REAL_ENGINE = True
except Exception as e:
    print(f"⚠️  Mock mode: {e}")
    USE_REAL_ENGINE = False

app = FastAPI(title="ResearchOS Real-time Dashboard")

# HTML Dashboard (FIXED VERSION)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ResearchOS Quant Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .status { padding: 15px; background: #4CAF50; color: white; border-radius: 5px; margin-bottom: 20px; font-weight: bold; }
        .results { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #2196F3; color: white; }
        tr:hover { background: #f5f5f5; }
        #chart { width: 100%; height: 400px; margin-top: 20px; }
        .loading { text-align: center; padding: 20px; color: #666; }
        .best { background: #C8E6C9 !important; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 ResearchOS Quant Engine Dashboard</h1>
        <div class="status" id="status">🔄 WebSocket холбогдож байна...</div>
        
        <div class="results">
            <h2>📊 Grid Search Үр Дүн</h2>
            <div id="loading" class="loading">Өгөгдөл ачаалагдаж байна...</div>
            <table id="resultsTable" style="display:none;">
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
        console.log("Dashboard ачаалагдаж байна...");
        
        // WebSocket холболт
        const ws = new WebSocket(ws://\/ws/grid-search);
        
        ws.onopen = () => {
            console.log("✅ WebSocket холбогдсон");
            document.getElementById("status").innerHTML = "🟢 WebSocket холбогдсон";
            document.getElementById("status").style.background = "#4CAF50";
        };
        
        ws.onmessage = (event) => {
            console.log("📨 Өгөгдөл ирлээ:", event.data);
            const data = JSON.parse(event.data);
            
            if (data.status === "completed" && data.results) {
                console.log("Grid search results:", data.results);
                updateTable(data.results);
                updateChart(data.results);
                
                document.getElementById("loading").style.display = "none";
                document.getElementById("resultsTable").style.display = "table";
            } else if (data.status === "error") {
                console.error("❌ Алдаа:", data.message);
                document.getElementById("status").innerHTML = "🔴 Алдаа: " + data.message;
                document.getElementById("status").style.background = "#f44336";
            }
        };
        
        ws.onerror = (error) => {
            console.error("WebSocket алдаа:", error);
            document.getElementById("status").innerHTML = "🔴 WebSocket алдаа";
            document.getElementById("status").style.background = "#f44336";
        };
        
        ws.onclose = () => {
            console.log("WebSocket хаагдсан");
            document.getElementById("status").innerHTML = "🔴 WebSocket салсан";
            document.getElementById("status").style.background = "#f44336";
        };
        
        function updateTable(results) {
            const tbody = document.getElementById("resultsBody");
            tbody.innerHTML = "";
            
            results.forEach((r, index) => {
                const isBest = index === 0;
                const rowClass = isBest ? 'class="best"' : '';
                const bestBadge = isBest ? '🏆 ' : '';
                
                const row = <tr \>
                    <td>\\</td>
                    <td>\</td>
                    <td>\</td>
                    <td>\%</td>
                    <td>\%</td>
                </tr>;
                tbody.innerHTML += row;
            });
            
            console.log(\✅ \ мөр хүснэгтэд нэмэгдлээ\);
        }
        
        function updateChart(results) {
            const maPeriods = results.map(r => \MA\ (RSI:\)\);
            const sharpeRatios = results.map(r => r.sharpe_ratio);
            const returns = results.map(r => r.total_return * 100);
            
            const trace1 = {
                x: maPeriods,
                y: sharpeRatios,
                type: 'bar',
                name: 'Sharpe Ratio',
                marker: { color: '#2196F3' },
                yaxis: 'y1'
            };
            
            const trace2 = {
                x: maPeriods,
                y: returns,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Total Return (%)',
                marker: { color: '#4CAF50', size: 8 },
                line: { color: '#4CAF50', width: 2 },
                yaxis: 'y2'
            };
            
            const layout = {
                title: 'Grid Search Үр Дүн - Performance Comparison',
                xaxis: { title: 'Strategy Parameters', tickangle: -45 },
                yaxis: { title: 'Sharpe Ratio', side: 'left' },
                yaxis2: { title: 'Total Return (%)', side: 'right', overlaying: 'y' },
                barmode: 'group',
                showlegend: true,
                legend: { x: 0, y: 1 }
            };
            
            Plotly.newPlot('chart', [trace1, trace2], layout);
            console.log("✅ График зурлаа");
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
    print("🔌 WebSocket холбогдлоо")
    
    try:
        await websocket.send_json({
            "status": "started",
            "message": "Grid search эхэлж байна..."
        })
        
        if USE_REAL_ENGINE:
            print(" Бодит C++ engine ашиглаж байна...")
            strategy = GridSearchStrategy()
            results = strategy.run_grid_search(
                ma_periods=[10, 20, 50],
                rsi_thresholds=[30, 50, 70]
            )
        else:
            print("️  Mock өгөгдөл үүсгэж байна...")
            await asyncio.sleep(1)  # Бага зэрэг хүлээх (реалистик байлгах)
            
            # Mock үр дүн үүсгэх
            results = []
            for ma in [10, 20, 50]:
                for rsi in [30, 50, 70]:
                    results.append({
                        "ma_period": ma,
                        "rsi_threshold": rsi,
                        "sharpe_ratio": round(random.uniform(0.8, 2.5), 3),
                        "max_drawdown": round(random.uniform(0.05, 0.20), 3),
                        "total_return": round(random.uniform(0.10, 0.50), 3)
                    })
            
            # Sharpe ratio-гоор эрэмбэлэх
            results.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
        
        print(f"✅ {len(results)} үр дүн бэлэн")
        
        await websocket.send_json({
            "status": "completed",
            "results": results,
            "best_params": results[0] if results else None,
            "count": len(results)
        })
        
        print("📤 Өгөгдөл илгээгдлээ")
        
    except Exception as e:
        print(f"❌ Алдаа: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_json({
            "status": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()
        print("🔌 WebSocket хаагдлаа")

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("🚀 ResearchOS Dashboard Server")
    print("="*60)
    print(f"📊 Mode: {'REAL C++ Engine' if USE_REAL_ENGINE else 'MOCK DATA'}")
    print("🌐 URL: http://localhost:8000")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

dashboard_file = Path(r"C:\Users\User\Desktop\ResearchOS\src\dashboard\dashboard_realtime.py")
dashboard_file.write_text(dashboard_code, encoding="utf-8")
print("✅ Dashboard засварлагдлаа!")
print(f"📁 Файл: {dashboard_file}")
print("\\n🚀 Дахин эхлүүлэх:")
print("   1. Одоогийн серверийг зогсоох (Ctrl+C)")
print("   2. python src/dashboard/dashboard_realtime.py")
print("   3. http://localhost:8000 хаягийг шинэчлэх (F5)")
