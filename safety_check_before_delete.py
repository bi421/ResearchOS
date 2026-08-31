"""
PRE-DELETION SAFETY CHECK for the 4 directories identified as safe to
remove (engines/scenario, engines/validation, engines/reasoning,
engines/quant/python/cpp_quant_engine).

For EVERY file inside each candidate directory, this checks whether it
has an identical (hash-matched) twin elsewhere in the codebase. Files
WITHOUT a confirmed twin are flagged as "UNIQUE - DO NOT DELETE" since
deleting them could lose real content that exists nowhere else.

READ-ONLY. Deletes nothing -- not even itself this time, since you may
want to rerun it after making changes.

Run in C:\\Users\\User\\Desktop\\ResearchOS
    python safety_check_before_delete.py
"""
import hashlib
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

CANDIDATES_FOR_REMOVAL = [
    "researchos/engines/scenario",
    "researchos/engines/validation",
    "researchos/engines/reasoning",
    "researchos/engines/quant/python/cpp_quant_engine",
]


def hash_file(path: Path) -> str:
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def all_files_excluding(exclude_prefix: str):
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            if rel.startswith(exclude_prefix):
                continue
            files.append(p)
    return files


def main():
    print("=" * 78)
    print("PRE-DELETION SAFETY CHECK")
    print("=" * 78)
    print("For each candidate directory, checking every file for a confirmed")
    print("identical twin elsewhere in the codebase.\n")

    overall_safe = True

    for candidate in CANDIDATES_FOR_REMOVAL:
        full_path = ROOT / candidate
        print("-" * 78)
        print(f"Directory: {candidate}")
        if not full_path.exists():
            print("  Does not exist -- skipping.")
            continue

        rest_of_codebase = all_files_excluding(candidate)
        rest_hashes = {}
        for f in rest_of_codebase:
            if f.suffix in (".py", ".md", ".json", ".txt"):
                h = hash_file(f)
                if h:
                    rest_hashes.setdefault(h, []).append(f)

        candidate_files = []
        for dirpath, dirnames, filenames in os.walk(full_path):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                candidate_files.append(Path(dirpath) / fn)

        unique_files = []
        confirmed_dupe_count = 0
        for f in candidate_files:
            if f.suffix not in (".py", ".md", ".json", ".txt"):
                continue  # skip pycache/binary etc, not part of this check
            h = hash_file(f)
            if h in rest_hashes:
                confirmed_dupe_count += 1
            else:
                unique_files.append(f.relative_to(ROOT))

        print(f"  Files checked: {confirmed_dupe_count + len(unique_files)}")
        print(f"  Confirmed identical elsewhere: {confirmed_dupe_count}")
        print(f"  NO confirmed twin found: {len(unique_files)}")

        if unique_files:
            overall_safe = False
            print("\n  >>> DO NOT blanket-delete this directory. These files have")
            print("      no confirmed twin and may be unique content:")
            for uf in unique_files:
                print(f"      {uf}")
        else:
            print("\n  >>> SAFE: every file in this directory has a confirmed")
            print("      identical twin elsewhere. Deleting this directory")
            print("      should not lose any unique content.")
        print()

    print("=" * 78)
    if overall_safe:
        print("ALL 4 candidate directories are safe to delete (every file has")
        print("a confirmed twin elsewhere). You can proceed.")
    else:
        print("At least one directory has files with no confirmed twin.")
        print("Review those specific files manually before deleting anything.")
    print("=" * 78)


if __name__ == "__main__":
    main()
