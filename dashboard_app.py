"""
LIVE RESEARCH DASHBOARD — reruns real scripts, shows real output.

Every result on this page comes from actually executing the underlying
Python script via subprocess at the moment you click "Run". Nothing is
cached, pre-computed, or fabricated — if a script errors, the error is
shown as-is.

Run in C:\\Users\\User\\Desktop\\ResearchOS
    pip install fastapi uvicorn --break-system-packages
    python dashboard_app.py

Then open http://localhost:8000 in a browser.
"""
import subprocess
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()

PROJECT_DIR = Path(__file__).parent

SCRIPTS = {
    "feature_test": "manual_feature_test.py",
    "context_report": "pretrade_context_report.py",
    "output_verifier": "output_verifier.py",
    "smc_test": "smc_signal_test.py",
}

LABELS = {
    "feature_test": "Statistical Edge Test (non-overlapping + Bonferroni)",
    "context_report": "Pre-Trade Context Report",
    "output_verifier": "Output Verifier (sanity checks)",
    "smc_test": "SMC Signal Statistical Test",
}


def run_script(script_name: str) -> dict:
    script_path = PROJECT_DIR / script_name
    if not script_path.exists():
        return {"ok": False, "output": f"File not found: {script_path}"}
    try:
        result = subprocess.run(
            ["python", str(script_path)],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=180,
        )
        output = result.stdout
        if result.returncode != 0:
            output += "\n\n--- STDERR ---\n" + result.stderr
        return {"ok": result.returncode == 0, "output": output}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": "Script timed out after 180 seconds."}
    except Exception as e:
        return {"ok": False, "output": f"Failed to run script: {e}"}


@app.get("/api/run/{key}")
def api_run(key: str):
    if key not in SCRIPTS:
        return JSONResponse({"ok": False, "output": "Unknown script key"}, status_code=404)
    result = run_script(SCRIPTS[key])
    return JSONResponse(result)


PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ResearchOS Live Dashboard</title>
<style>
  body { font-family: -apple-system, Segoe UI, sans-serif; background: #0e0e12; color: #e5e5e5; margin: 0; padding: 24px; }
  h1 { font-size: 20px; margin-bottom: 4px; }
  .subtitle { color: #999; font-size: 13px; margin-bottom: 24px; }
  .panel { background: #1a1a20; border: 1px solid #2a2a32; border-radius: 8px; margin-bottom: 16px; overflow: hidden; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #202028; }
  .panel-title { font-weight: 600; font-size: 14px; }
  button { background: #3b5bfd; color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; }
  button:hover { background: #2f4bd8; }
  button:disabled { background: #444; cursor: wait; }
  .status { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
  .status.ok { background: #1e3a1e; color: #7fd97f; }
  .status.fail { background: #3a1e1e; color: #d97f7f; }
  .status.idle { background: #2a2a32; color: #888; }
  pre { margin: 0; padding: 16px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word;
        max-height: 500px; overflow-y: auto; color: #ccc; background: #0e0e12; }
  #run-all { margin-bottom: 20px; }
</style>
</head>
<body>
  <h1>ResearchOS Live Dashboard</h1>
  <div class="subtitle">Every result below comes from actually running the script at click time. No cached or fabricated numbers.</div>
  <button id="run-all" onclick="runAll()">Run All</button>
  <div id="panels"></div>

<script>
const scripts = {
  "feature_test": "Statistical Edge Test (non-overlapping + Bonferroni)",
  "context_report": "Pre-Trade Context Report",
  "output_verifier": "Output Verifier (sanity checks)",
  "smc_test": "SMC Signal Statistical Test",
};

const panelsDiv = document.getElementById("panels");

for (const key in scripts) {
  const panel = document.createElement("div");
  panel.className = "panel";
  panel.innerHTML = `
    <div class="panel-header">
      <span class="panel-title">${scripts[key]}</span>
      <div>
        <span class="status idle" id="status-${key}">not run</span>
        <button onclick="runOne('${key}')">Run</button>
      </div>
    </div>
    <pre id="output-${key}">(no output yet — click Run)</pre>
  `;
  panelsDiv.appendChild(panel);
}

async function runOne(key) {
  const statusEl = document.getElementById(`status-${key}`);
  const outputEl = document.getElementById(`output-${key}`);
  statusEl.textContent = "running...";
  statusEl.className = "status idle";
  outputEl.textContent = "Running — this may take a moment...";
  try {
    const res = await fetch(`/api/run/${key}`);
    const data = await res.json();
    outputEl.textContent = data.output || "(empty output)";
    statusEl.textContent = data.ok ? "ok" : "error";
    statusEl.className = data.ok ? "status ok" : "status fail";
  } catch (e) {
    outputEl.textContent = "Request failed: " + e;
    statusEl.textContent = "error";
    statusEl.className = "status fail";
  }
}

async function runAll() {
  const btn = document.getElementById("run-all");
  btn.disabled = true;
  for (const key in scripts) {
    await runOne(key);
  }
  btn.disabled = false;
}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE


if __name__ == "__main__":
    import uvicorn

    print("Starting dashboard at http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
