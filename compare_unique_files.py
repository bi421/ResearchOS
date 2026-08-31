"""
CONTENT COMPARISON for the 19 "unique" files flagged by
safety_check_before_delete.py. For each one, finds every OTHER file in
the codebase with the same filename (regardless of directory) and shows
a side-by-side size + first-lines comparison, so you can judge whether
they are:
  - genuinely unique logic (keep, not a duplicate)
  - a near-duplicate / older-or-newer version of the same thing
  - actually unrelated code that happens to share a filename

READ-ONLY. Deletes and modifies nothing.

Run in C:\\Users\\User\\Desktop\\ResearchOS
    python compare_unique_files.py
"""
import os
from pathlib import Path

ROOT = Path(__file__).parent

SKIP_DIRS = {
    ".git",
    "__pycache__",
    "build",
    "build-linux",
    "_deps",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    "htmlcov",
    "googletest-src",
}

UNIQUE_FILES = [
    "researchos/engines/scenario/dataset_emission.py",
    "researchos/engines/scenario/evidence.py",
    "researchos/engines/scenario/experiment_emission.py",
    "researchos/engines/scenario/lineage.py",
    "researchos/engines/scenario/probability.py",
    "researchos/engines/scenario/reasoner.py",
    "researchos/engines/scenario/report.py",
    "researchos/engines/scenario/repository.py",
    "researchos/engines/scenario/reproduction.py",
    "researchos/engines/scenario/result_emission.py",
    "researchos/engines/scenario/run_emission.py",
    "researchos/engines/scenario/score.py",
    "researchos/engines/scenario/validation_emission.py",
    "researchos/engines/validation/validators.py",
    "researchos/engines/reasoning/evidence.py",
    "researchos/engines/reasoning/validation.py",
    "researchos/engines/quant/python/cpp_quant_engine/backend.py",
    "researchos/engines/quant/python/cpp_quant_engine/backend_wrapper.py",
    "researchos/engines/quant/python/cpp_quant_engine/__init__.py",
]


def all_files():
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            files.append(Path(dirpath) / fn)
    return files


def main():
    everything = all_files()
    by_name = {}
    for f in everything:
        by_name.setdefault(f.name, []).append(f)

    print("=" * 78)
    print("CONTENT COMPARISON REPORT")
    print("=" * 78)

    for rel_str in UNIQUE_FILES:
        target = ROOT / rel_str
        name = target.name
        print("\n" + "-" * 78)
        print(f"FILE: {rel_str}")
        if not target.exists():
            print("  (does not exist -- skipping)")
            continue

        candidates = [f for f in by_name.get(name, []) if f != target]
        if not candidates:
            print(f"  No other file named '{name}' exists anywhere in the codebase.")
            print("  -> This looks like GENUINELY UNIQUE content. Do not delete.")
            continue

        target_size = target.stat().st_size
        try:
            target_lines = target.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            target_lines = []

        print(f"  Size: {target_size} bytes, {len(target_lines)} lines")
        print(f"  Other files named '{name}' found:")
        for c in candidates:
            rel_c = c.relative_to(ROOT)
            c_size = c.stat().st_size
            try:
                c_lines = c.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                c_lines = []
            size_diff = abs(c_size - target_size)
            print(f"\n    {rel_c}")
            print(f"      Size: {c_size} bytes, {len(c_lines)} lines " f"(diff from target: {size_diff} bytes)")
            print("      First 3 non-empty lines of candidate:")
            shown = 0
            for line in c_lines:
                if line.strip():
                    print(f"        {line.strip()[:100]}")
                    shown += 1
                    if shown >= 3:
                        break

    print("\n" + "=" * 78)
    print("Review the above manually. Files with no candidates are likely")
    print("genuinely unique. Files with a same-named candidate need a real")
    print("diff (not just size) before deciding which is canonical.")
    print("=" * 78)


if __name__ == "__main__":
    main()
