# 1. Fix bootstrap.py
with open("researchos/market_memory/bootstrap.py", "r", encoding="utf-8") as f:
    content = f.read()
if "from typing import Sequence" in content and "Any" not in content:
    content = content.replace("from typing import Sequence", "from typing import Any, Sequence")
with open("researchos/market_memory/bootstrap.py", "w", encoding="utf-8") as f:
    f.write(content)

# 2. Fix benchmark_runtime.py
with open("benchmarks/benchmark_runtime.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('if p.exists(): print(f"Binary: {p.stat().st_size/1024:.0f}KB (pybind11 was 684KB+26MB PDB)")', 'if p.exists():\n    print(f"Binary: {p.stat().st_size/1024:.0f}KB (pybind11 was 684KB+26MB PDB)")')

content = content.replace("t0=tm.perf_counter(); b.market_data_load(req); times.append((tm.perf_counter()-t0)*1000)", "t0 = tm.perf_counter()\n    b.market_data_load(req)\n    times.append((tm.perf_counter() - t0) * 1000)")

with open("benchmarks/benchmark_runtime.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Үлдсэн 4 алдааг амжилттай заслаа!")
