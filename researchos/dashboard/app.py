from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
from datetime import datetime

app = FastAPI()


@app.get("/")
async def get():
    return HTMLResponse("""
    <html><head><title>ResearchOS Live</title></head>
    <body>
    <h1>ResearchOS Live Dashboard</h1>
    <div id="data">Waiting...</div>
    <script>
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onmessage = (e) => document.getElementById('data').innerHTML = e.data;
    </script>
    </body></html>
    """)


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps({"time": str(datetime.now()), "status": "OK"}))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
