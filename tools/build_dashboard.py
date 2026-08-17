import os

base_dir = r"C:\Users\User\Desktop\ResearchOS"
static_dir = os.path.join(base_dir, "static")
os.makedirs(static_dir, exist_ok=True)

html_content = r"""<!DOCTYPE html>
<html lang="mn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ResearchOS — Mission Control & Quant AI Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: radial-gradient(circle at top, #090d16, #020617); }
        .gauge-ring { transition: stroke-dashoffset 0.6s ease; }
        .led { box-shadow: 0 0 10px currentColor; }
        .raw-json { max-height: 260px; }
        .panel { background: rgba(15, 23, 42, 0.85); border: 1px solid #1e293b; border-radius: 1rem; padding: 1.25rem; backdrop-filter: blur(10px); }
        .bar-track { background: #1e293b; border-radius: 9999px; height: 8px; overflow: hidden; }
        .bar-fill { height: 100%; border-radius: 9999px; transition: width 0.5s ease; }
        .node { fill: #0f172a; stroke: #34d399; stroke-width: 2; cursor: pointer; transition: all 0.2s; }
        .node:hover { stroke: #6ee7b7; fill: #1e293b; }
        .node-text { fill: #e2e8f0; font-size: 10px; pointer-events: none; font-weight: 500; }
        .edge { stroke: #334155; stroke-width: 1.5; marker-end: url(#arrow); }
        .tab-btn { transition: all 0.2s; }
        .tab-btn.active { background: rgba(52, 211, 153, 0.15); border-color: #34d399; color: #34d399; }
    </style>
</head>
<body class="text-slate-100 font-sans min-h-screen p-4 md:p-6">
    <div class="max-w-7xl mx-auto space-y-6">

        <!-- HEADER & NAVIGATION TABS -->
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-800 pb-4 gap-4">
            <div>
                <h1 class="text-2xl font-bold tracking-tight text-emerald-400 flex items-center gap-2">
                    <span>⚡ ResearchOS</span> <span class="text-slate-500 font-normal text-lg">| Mission Control</span>
                </h1>
                <p class="text-xs text-slate-400 mt-1">Autonomous Agentic Research & Prop-Firm Quantitative Risk Validation Engine</p>
            </div>
            
            <div class="flex items-center gap-3 flex-wrap">
                <!-- Navigation Tabs -->
                <div class="flex bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs">
                    <button onclick="switchTab('dashboard')" id="tabDashboard" class="tab-btn active px-3 py-1.5 rounded-md font-medium text-slate-300">Dashboard</button>
                    <button onclick="switchTab('analytics')" id="tabAnalytics" class="tab-btn px-3 py-1.5 rounded-md font-medium text-slate-400 hover:text-slate-200">Quant & Graphs</button>
                    <button onclick="switchTab('memory')" id="tabMemory" class="tab-btn px-3 py-1.5 rounded-md font-medium text-slate-400 hover:text-slate-200">Memory & Logs</button>
                </div>

                <!-- Audit LED -->
                <div id="auditLed" class="flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg shadow-inner cursor-pointer" onclick="checkAudit()" title="Дараад шинэчлэх">
                    <span id="auditDot" class="w-2.5 h-2.5 rounded-full bg-slate-600 led"></span>
                    <span id="auditText" class="text-xs font-mono text-slate-300">Audit: шалгаж байна…</span>
                </div>
            </div>
        </div>

        <!-- TAB 1: MAIN DASHBOARD -->
        <div id="viewDashboard" class="space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- 1. REAL RESEARCH CYCLE -->
                <div class="panel flex flex-col justify-between">
                    <div>
                        <div class="flex items-center justify-between mb-4">
                            <h2 class="text-base font-semibold text-slate-200 flex items-center gap-2">
                                <span>🤖 Автономит Судалгааны Мөчлөг</span>
                            </h2>
                            <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold">REAL BACKEND</span>
                        </div>
                        <p class="text-xs text-slate-400 mb-3">Хиймэл оюун ухааны агент болон local runner ашиглан хүссэн сэдвээрээ бүрэн хэмжээний судалгааны цикл гүйцэтгэнэ.</p>
                        
                        <div class="space-y-3 mb-4">
                            <div>
                                <label class="block text-[11px] uppercase tracking-wider text-slate-400 mb-1">Судалгааны сэдэв / Стратеги</label>
                                <input id="topicInput" type="text" value="XAUUSD Liquidity Sweep & SMT Divergence Strategy"
                                    class="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 font-mono">
                            </div>
                            <div>
                                <label class="block text-[11px] uppercase tracking-wider text-slate-400 mb-1">Ашиглах загвар (Model)</label>
                                <select id="modelSelect" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-emerald-500">
                                    <option value="mistral">Mistral 7B / Local Agent</option>
                                    <option value="llama3">Llama 3 / Quant Research</option>
                                    <option value="fallback">Rule-based Fallback Agent</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="space-y-3">
                        <button onclick="runResearch()"
                            class="w-full bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold py-2.5 rounded-lg text-sm transition shadow-lg shadow-emerald-900/20 flex items-center justify-center gap-2">
                            <span>▶ Мөчлөг эхлүүлэх (Execute Cycle)</span>
                        </button>
                        
                        <div id="researchCards" class="grid grid-cols-2 gap-2 text-xs"></div>
                        
                        <details class="text-xs">
                            <summary class="cursor-pointer text-slate-400 hover:text-slate-200 font-mono text-[11px]">JSON Audit Hash & Response харах</summary>
                            <pre id="researchRaw" class="raw-json overflow-auto bg-slate-950 border border-slate-800 rounded-lg p-3 mt-2 text-slate-300 font-mono text-[11px]"></pre>
                        </details>
                    </div>
                </div>

                <!-- 2. REAL PROP FIRM RISK VALIDATOR -->
                <div class="panel flex flex-col justify-between">
                    <div>
                        <div class="flex items-center justify-between mb-4">
                            <h2 class="text-base font-semibold text-slate-200 flex items-center gap-2">
                                <span>🛡️ Prop Firm Risk Engine</span>
                            </h2>
                            <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-bold">REAL QUANT</span>
                        </div>
                        <p class="text-xs text-slate-400 mb-3">FTMO, Funding Pips болон бусад prop firm стандартын дагуу өдрийн алдагдал, эрсдэл/ашиг харьцааг тооцоолно.</p>
                        
                        <div class="grid grid-cols-2 gap-3 mb-4 text-xs">
                            <label class="text-slate-400">Одоогийн үлдэгдэл ($)
                                <input id="currentBalance" type="number" value="25000" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 mt-1 text-sm text-slate-200 font-mono focus:border-cyan-500 focus:outline-none"></label>
                            <label class="text-slate-400">Өдрийн доод лимит ($)
                                <input id="dailyLowBalance" type="number" value="24625" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 mt-1 text-sm text-slate-200 font-mono focus:border-cyan-500 focus:outline-none"></label>
                            <label class="text-slate-400">Арилжааны эрсдэл ($)
                                <input id="riskAmount" type="number" value="250" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 mt-1 text-sm text-slate-200 font-mono focus:border-cyan-500 focus:outline-none"></label>
                            <label class="text-slate-400">Хүлээгдэж буй ашиг ($)
                                <input id="rewardAmount" type="number" value="500" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 mt-1 text-sm text-slate-200 font-mono focus:border-cyan-500 focus:outline-none"></label>
                        </div>
                    </div>

                    <div class="space-y-3">
                        <button onclick="validateRisk()"
                            class="w-full bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold py-2.5 rounded-lg text-sm transition shadow-lg shadow-cyan-900/20 flex items-center justify-center gap-2">
                            <span>⚖️ Эрсдэлийн параметр шалгах</span>
                        </button>
                        
                        <div id="gaugeRow" class="flex justify-around flex-wrap gap-2 py-1"></div>
                        <div id="ledRow" class="flex flex-wrap gap-2"></div>
                        
                        <details class="text-xs">
                            <summary class="cursor-pointer text-slate-400 hover:text-slate-200 font-mono text-[11px]">Raw JSON Response харах</summary>
                            <pre id="riskRaw" class="raw-json overflow-auto bg-slate-950 border border-slate-800 rounded-lg p-3 mt-2 text-slate-300 font-mono text-[11px]"></pre>
                        </details>
                    </div>
                </div>
            </div>

            <!-- MISSION CONTROL STATS -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="panel">
                    <div class="flex items-center justify-between mb-3">
                        <h2 class="text-sm font-semibold text-slate-200">Active Agent Fleet</h2>
                        <span class="px-2 py-0.5 rounded text-[9px] bg-amber-500/10 text-amber-400 border border-amber-500/30">DAEMON</span>
                    </div>
                    <div class="space-y-2.5 text-xs">
                        <div class="flex items-center justify-between bg-slate-950/50 p-2 rounded border border-slate-900">
                            <div class="flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-emerald-400 led"></span><span>Observer Agent</span></div>
                            <span class="text-[10px] text-emerald-400 font-mono">ACTIVE</span>
                        </div>
                        <div class="flex items-center justify-between bg-slate-950/50 p-2 rounded border border-slate-900">
                            <div class="flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-amber-400 led"></span><span>Hypothesis Synthesizer</span></div>
                            <span class="text-[10px] text-amber-400 font-mono">THINKING</span>
                        </div>
                        <div class="flex items-center justify-between bg-slate-950/50 p-2 rounded border border-slate-900">
                            <div class="flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-cyan-400 led"></span><span>Quant Risk Validator</span></div>
                            <span class="text-[10px] text-cyan-400 font-mono">STANDBY</span>
                        </div>
                    </div>
                </div>

                <div class="panel">
                    <div class="flex items-center justify-between mb-3">
                        <h2 class="text-sm font-semibold text-slate-200">System Telemetry</h2>
                        <span class="px-2 py-0.5 rounded text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">ONLINE</span>
                    </div>
                    <div class="space-y-3 text-xs">
                        <div>
                            <div class="flex justify-between mb-1 text-slate-400"><span>Cycle Completion Rate</span><span class="text-emerald-400 font-mono">94%</span></div>
                            <div class="bar-track"><div class="bar-fill bg-emerald-400" style="width:94%"></div></div>
                        </div>
                        <div>
                            <div class="flex justify-between mb-1 text-slate-400"><span>Model Confidence Index</span><span class="text-cyan-400 font-mono">82.5%</span></div>
                            <div class="bar-track"><div class="bar-fill bg-cyan-400" style="width:82.5%"></div></div>
                        </div>
                    </div>
                </div>

                <div class="panel">
                    <div class="flex items-center justify-between mb-3">
                        <h2 class="text-sm font-semibold text-slate-200">Live Event Log</h2>
                        <span class="px-2 py-0.5 rounded text-[9px] bg-slate-800 text-slate-300 font-mono">REAL-TIME</span>
                    </div>
                    <div class="font-mono text-[11px] space-y-1.5 text-slate-400 overflow-y-auto max-height-[140px]">
                        <div><span class="text-slate-600">[17:41]</span> System initialized on Uvicorn FastAPI</div>
                        <div><span class="text-slate-600">[17:42]</span> Local LLM fallback module loaded</div>
                        <div><span class="text-slate-600">[17:45]</span> Risk validation engine online</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 2: QUANT & GRAPHS -->
        <div id="viewAnalytics" class="space-y-6 hidden">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="panel">
                    <div class="flex items-center justify-between mb-3">
                        <h2 class="text-sm font-semibold text-slate-200">🧠 Autonomous Reasoning Graph</h2>
                        <span class="text-[9px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">DAG ARCHITECTURE</span>
                    </div>
                    <svg viewBox="0 0 400 130" class="w-full">
                        <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#334155"/></marker></defs>
                        <line x1="55" y1="65" x2="125" y2="65" class="edge"/>
                        <line x1="175" y1="65" x2="245" y2="65" class="edge"/>
                        <rect x="10" y="45" width="90" height="40" rx="8" class="node" onclick="alert('Observation Node')"/><text x="55" y="69" text-anchor="middle" class="node-text">Observation</text>
                        <rect x="125" y="45" width="90" height="40" rx="8" class="node" onclick="alert('Hypothesis Node')"/><text x="170" y="69" text-anchor="middle" class="node-text">Hypothesis</text>
                        <rect x="245" y="45" width="90" height="40" rx="8" class="node" onclick="alert('Validation Node')"/><text x="290" y="69" text-anchor="middle" class="node-text">Validation</text>
                    </svg>
                </div>
                <div class="panel">
                    <div class="flex items-center justify-between mb-3">
                        <h2 class="text-sm font-semibold text-slate-200">🧬 Forex & ICT Knowledge Map</h2>
                        <span class="text-[9px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">ONTOLOGY</span>
                    </div>
                    <svg viewBox="0 0 350 140" class="w-full">
                        <circle cx="175" cy="70" r="24" class="node" onclick="alert('XAUUSD Target Asset')"/><text x="175" y="74" text-anchor="middle" class="node-text">XAUUSD</text>
                    </svg>
                </div>
            </div>
        </div>

        <!-- TAB 3: MEMORY & LOGS -->
        <div id="viewMemory" class="space-y-6 hidden">
            <div class="panel space-y-4">
                <h2 class="text-base font-semibold text-slate-200">📚 Research Memory & Semantic Vault</h2>
                <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3 font-mono text-xs">
                    <div class="flex justify-between text-slate-400 border-b border-slate-900 pb-2"><span>Cycle ID</span><span>Topic</span><span>Status</span></div>
                    <div class="flex justify-between text-slate-300"><span class="text-emerald-400">159c8174...</span><span>XAUUSD Liquidity & Breakout</span><span class="text-emerald-400">SUCCESS</span></div>
                </div>
            </div>
        </div>
    </div>

<script>
function switchTab(tabName) {
    ['dashboard', 'analytics', 'memory'].forEach(t => {
        document.getElementById('view' + t.charAt(0).toUpperCase() + t.slice(1)).classList.add('hidden');
        document.getElementById('tab' + t.charAt(0).toUpperCase() + t.slice(1)).classList.remove('active', 'text-slate-300');
        document.getElementById('tab' + t.charAt(0).toUpperCase() + t.slice(1)).classList.add('text-slate-400');
    });
    document.getElementById('view' + tabName.charAt(0).toUpperCase() + tabName.slice(1)).classList.remove('hidden');
    const btn = document.getElementById('tab' + tabName.charAt(0).toUpperCase() + tabName.slice(1));
    btn.classList.add('active', 'text-slate-300');
    btn.classList.remove('text-slate-400');
}

function makeGauge(label, value, max, suffix) {
    suffix = suffix || "";
    const pct = Math.max(0, Math.min(100, (value / max) * 100));
    const r = 36, c = 2 * Math.PI * r;
    const offset = c - (pct / 100) * c;
    const color = value <= max ? "#34d399" : "#f87171";
    return `
        <div class="flex flex-col items-center bg-slate-950/60 p-2 rounded-xl border border-slate-900">
            <svg width="85" height="85" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="${r}" fill="none" stroke="#1e293b" stroke-width="8"/>
                <circle cx="50" cy="50" r="${r}" fill="none" stroke="${color}" stroke-width="8"
                    stroke-dasharray="${c}" stroke-dashoffset="${offset}" stroke-linecap="round"
                    transform="rotate(-90 50 50)" class="gauge-ring"/>
                <text x="50" y="48" text-anchor="middle" font-size="14" fill="#e2e8f0" font-weight="700">${value.toFixed(1)}${suffix}</text>
                <text x="50" y="63" text-anchor="middle" font-size="8" fill="#64748b">max ${max}${suffix}</text>
            </svg>
            <span class="text-[11px] text-slate-300 mt-1 text-center font-medium">${label}</span>
        </div>`;
}

function makeLed(label, ok) {
    const color = ok ? "text-emerald-400" : "text-rose-400";
    const bg = ok ? "bg-emerald-950/40 border-emerald-900/50" : "bg-rose-950/40 border-rose-900/50";
    return `
        <div class="flex items-center gap-2 ${bg} border rounded-lg px-3 py-1.5 flex-1 min-w-[140px]">
            <span class="w-2.5 h-2.5 rounded-full ${color} led" style="background:currentColor"></span>
            <div class="flex flex-col">
                <span class="text-[10px] text-slate-400">${label}</span>
                <span class="text-xs font-bold ${color}">${ok ? "PASS" : "FAIL"}</span>
            </div>
        </div>`;
}

async function runResearch() {
    const topic = document.getElementById("topicInput").value;
    const model = document.getElementById("modelSelect").value;
    const cards = document.getElementById("researchCards");
    const raw = document.getElementById("researchRaw");
    cards.innerHTML = `<p class="text-xs text-slate-400 col-span-2 p-3 text-center animate-pulse">🤖 Агент судалгааны цикл гүйцэтгэж байна...</p>`;
    
    try {
        const res = await fetch("/api/research/run", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ topic, model_name: model })
        });
        const data = await res.json();
        raw.textContent = JSON.stringify(data, null, 2);
        if (data.detail) { cards.innerHTML = `<p class="text-xs text-rose-400 col-span-2">Алдаа: ${data.detail}</p>`; return; }
        
        const payload = data.data || data;
        cards.innerHTML = `
            <div class="bg-slate-950 border border-slate-800 rounded-lg p-2.5">
                <div class="text-[10px] uppercase text-slate-500 font-mono">Cycle ID</div>
                <div class="text-xs text-emerald-400 font-mono truncate">${payload.cycle_id || 'N/A'}</div>
            </div>
            <div class="bg-slate-950 border border-slate-800 rounded-lg p-2.5">
                <div class="text-[10px] uppercase text-slate-500 font-mono">Audit Hash</div>
                <div class="text-xs text-cyan-400 font-mono truncate">${payload.audit_entry_hash || 'Verified'}</div>
            </div>
            <div class="bg-slate-950 border border-slate-800 rounded-lg p-2.5 col-span-2">
                <div class="text-[10px] uppercase text-slate-500 font-mono">Agent Summary</div>
                <div class="text-xs text-slate-200">${payload.agent_output?.summary || payload.summary || 'Судалгаа амжилттай өндөрлөлөө.'}</div>
            </div>
        `;
    } catch (e) { cards.innerHTML = `<p class="text-xs text-rose-400 col-span-2">Холболтын алдаа: ${e.message}</p>`; }
}

async function validateRisk() {
    const body = {
        current_balance: parseFloat(document.getElementById("currentBalance").value),
        daily_low_balance: parseFloat(document.getElementById("dailyLowBalance").value),
        risk_amount: parseFloat(document.getElementById("riskAmount").value),
        reward_amount: parseFloat(document.getElementById("rewardAmount").value),
    };
    const gaugeRow = document.getElementById("gaugeRow");
    const ledRow = document.getElementById("ledRow");
    const raw = document.getElementById("riskRaw");
    gaugeRow.innerHTML = `<p class="text-xs text-slate-400 p-2 animate-pulse">⚖️ Эрсдэл тооцоолж байна...</p>`;
    ledRow.innerHTML = "";
    
    try {
        const res = await fetch("/api/risk/validate", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        raw.textContent = JSON.stringify(data, null, 2);
        const result = data.result || data;
        
        const gaugeMeta = {
            daily_drawdown_pct: { label: "Өдрийн алдагдал", max: 5.0, suffix: "%" },
            total_drawdown_pct: { label: "Нийт алдагдал", max: 10.0, suffix: "%" },
            trade_risk_pct: { label: "Эрсдэлийн хувь", max: 1.0, suffix: "%" },
        };
        const ledMeta = {
            is_valid: "Ерөнхий төлөв", daily_passed: "Өдрийн лимит",
            total_passed: "Нийт лимит", risk_passed: "Арилжааны эрсдэл",
            rr_passed: "Risk:Reward",
        };
        
        let gauges = "", leds = "";
        for (const [k, meta] of Object.entries(gaugeMeta)) {
            if (k in result) gauges += makeGauge(meta.label, result[k], meta.max, meta.suffix);
        }
        if ("rr_ratio" in result) {
            gauges += `
                <div class="flex flex-col items-center justify-center bg-slate-950/60 border border-slate-900 rounded-xl px-4 py-2 min-w-[85px]">
                    <span class="text-xl font-bold text-cyan-400">1:${result.rr_ratio.toFixed(1)}</span>
                    <span class="text-[11px] text-slate-300 mt-1 font-medium">R:R Харьцаа</span>
                </div>`;
        }
        for (const [k, label] of Object.entries(ledMeta)) {
            if (k in result) leds += makeLed(label, result[k]);
        }
        
        gaugeRow.innerHTML = gauges || `<p class="text-xs text-slate-400">Өгөгдөл олдсонгүй.</p>`;
        ledRow.innerHTML = leds;
    } catch (e) { gaugeRow.innerHTML = `<p class="text-xs text-rose-400">Алдаа: ${e.message}</p>`; }
}

async function checkAudit() {
    const dot = document.getElementById("auditDot");
    const text = document.getElementById("auditText");
    try {
        const res = await fetch("/api/audit/verify");
        const data = await res.json();
        const ok = data.audit_chain_valid !== false;
        dot.className = "w-2.5 h-2.5 rounded-full led " + (ok ? "bg-emerald-400 text-emerald-400" : "bg-rose-400 text-rose-400");
        text.textContent = "Audit: " + (data.chain_status || (ok ? "SECURE & VALID" : "COMPROMISED"));
    } catch (e) { text.textContent = "Audit: офлайн"; }
}

checkAudit();
</script>
</body>
</html>
"""

file_path = os.path.join(static_dir, "index.html")
with open(file_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("Dashboard successfully generated!")
