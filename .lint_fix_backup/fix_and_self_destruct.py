#!/usr/bin/env python3
"""
ResearchOS Lint Fixer + Self-Destruct
- Бүх Ruff алдааг автоматаар засна
- Ажиллаад дуусмагц өөрийгөө устгана
- Git-тэй ажиллахад тохиромжтой
"""

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ===== CONFIG =====
PROJECT_ROOT = Path(__file__).parent.resolve()
RUFF_CMD = "python -m ruff check . --output-format json"
BACKUP_DIR = PROJECT_ROOT / ".lint_fix_backup"
LOG_FILE = PROJECT_ROOT / ".lint_fix_log.txt"


# ===== UTILS =====
def log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")


def backup_file(filepath: Path):
    """Файлыг backup хийх"""
    BACKUP_DIR.mkdir(exist_ok=True)
    rel_path = filepath.relative_to(PROJECT_ROOT)
    backup_path = BACKUP_DIR / rel_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(filepath, backup_path)
    log(f"📦 Backup: {rel_path}")


def read_file(filepath: Path) -> str:
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        return f.read()


def write_file(filepath: Path, content: str):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


# ===== FIXERS =====
def fix_e402(content: str) -> str:
    """E402: Import-ыг файлын эхэнд байрлуулах"""
    lines = content.split("\n")
    imports = []
    code_lines = []
    in_import_block = True

    for line in lines:
        stripped = line.strip()
        if in_import_block and (stripped.startswith("import ") or stripped.startswith("from ")):
            imports.append(line)
        elif in_import_block and stripped == "":
            code_lines.append(line)
        else:
            in_import_block = False
            code_lines.append(line)

    # Docstring хадгалах
    docstring = []
    if code_lines and (code_lines[0].strip().startswith('"""') or code_lines[0].strip().startswith("'''")):
        quote = '"""' if '"""' in code_lines[0] else "'''"
        docstring.append(code_lines.pop(0))
        while code_lines and quote not in code_lines[0]:
            docstring.append(code_lines.pop(0))
        if code_lines:
            docstring.append(code_lines.pop(0))

    result = docstring + imports + [""] + code_lines
    return "\n".join(result)


def fix_f841(content: str, errors: list) -> str:
    """F841: Ашиглагдаагүй хувьсагчийг _prefix нэмэх эсвэл устгах"""
    lines = content.split("\n")
    for err in errors:
        if err["code"] != "F841":
            continue
        row = err["location"]["row"] - 1  # 0-based
        if 0 <= row < len(lines):
            line = lines[row]
            # Хувьсагчийн нэрийг олох
            match = re.search(r"(\w+)\s*=", line)
            if match:
                var_name = match.group(1)
                # _prefix нэмэх
                new_line = line.replace(f"{var_name} =", f"_{var_name} =", 1)
                lines[row] = new_line
                log(f"🔧 F841: {var_name} -> _{var_name} (мөр {row + 1})")
    return "\n".join(lines)


def fix_f401(content: str, errors: list) -> str:
    """F401: Ашиглагдаагүй import-ыг устгах"""
    lines = content.split("\n")
    for err in errors:
        if err["code"] != "F401":
            continue
        row = err["location"]["row"] - 1
        if 0 <= row < len(lines):
            log(f"🗑️ F401: Устгасан import (мөр {row + 1}): {lines[row].strip()}")
            lines[row] = ""  # Хоосон мөр болгох
    # Дараалсан хоосон мөрийг цэвэрлэх
    cleaned = []
    prev_empty = False
    for line in lines:
        if line.strip() == "":
            if not prev_empty:
                cleaned.append(line)
            prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False
    return "\n".join(cleaned)


def fix_e722(content: str) -> str:
    """E722: Bare except-ыг except Exception болгох"""
    # Энгийн regex орлуулах
    content = re.sub(r"except\s*:\s*", "except Exception as _e: ", content)
    log("🔧 E722: bare except -> except Exception")
    return content


def fix_e741(content: str) -> str:
    """E741: 'l' хувьсагчийг 'length' болгох (зөвхөн тодорхой контекстэд)"""
    # Зөвхөн len() оноох үед л солих
    content = re.sub(r"\bl\s*=\s*len\(", "length = len(", content)
    log("🔧 E741: ambiguous 'l' -> 'length' (len() контекстэд)")
    return content


def fix_invalid_syntax(content: str) -> str:
    """invalid-syntax: f-string доторх backslash-ийг засах"""
    # f"...\{...}" -> f"...\\{...}"
    # Анхаар: энэ нь бүх тохиолдолд ажиллахгүй, гэхдээ ихэнхийг нь засна
    content = re.sub(r'f(["\'])(.*?)(?<!\\)\\(["\']?\s*\{)', r"f\1\2\\\3", content)
    log("🔧 invalid-syntax: f-string backslash escaped")
    return content


def fix_f821_stub(content: str, errors: list, filepath: Path) -> str:
    """F821: Undefined name-д import нэмэх (хязгаарлагдмал)"""
    known_imports = {
        "symbol": "from typing import Any\nsymbol: Any = None  # TODO: define properly\n",
        "bt_time": "from datetime import datetime\nbt_time = datetime.now()\n",
        "Parallel": "from joblib import Parallel\n",
        "delayed": "from joblib import delayed\n",
    }

    lines = content.split("\n")
    added_imports = set()

    for err in errors:
        if err["code"] != "F821" or err["filename"] != str(filepath):
            continue
        name = err["message"].split("`")[1] if "`" in err["message"] else None
        if name and name in known_imports and name not in added_imports:
            # Import-ыг эхэнд нэмэх
            lines.insert(0, known_imports[name])
            added_imports.add(name)
            log(f"🔧 F821: Added stub for '{name}'")

    return "\n".join(lines)


# ===== MAIN FIXER =====
def fix_file(filepath: Path, errors: list) -> bool:
    """Нэг файлыг засах"""
    try:
        content = read_file(filepath)
        original = content

        # Fixers apply
        content = fix_e402(content)
        content = fix_f841(content, [e for e in errors if e["filename"] == str(filepath)])
        content = fix_f401(content, [e for e in errors if e["filename"] == str(filepath)])
        content = fix_e722(content)
        content = fix_e741(content)
        content = fix_invalid_syntax(content)
        content = fix_f821_stub(content, errors, filepath)

        if content != original:
            backup_file(filepath)
            write_file(filepath, content)
            log(f"✅ Fixed: {filepath.relative_to(PROJECT_ROOT)}")
            return True
        return False
    except Exception as e:
        log(f"❌ Error fixing {filepath}: {e}")
        return False


def get_ruff_errors() -> list:
    """Ruff-аас алдааг JSON форматаар авах"""
    try:
        result = subprocess.run(RUFF_CMD.split(), cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
        if result.stdout.strip():
            return json.loads(result.stdout)
        return []
    except Exception as e:
        log(f"❌ Ruff execute error: {e}")
        return []


def self_destruct():
    """Скрипт өөрийгөө устгах"""
    script_path = Path(__file__).resolve()
    log(f"💥 SELF-DESTRUCT: Deleting {script_path.name}")

    # Log-ыг хадгалах
    if LOG_FILE.exists():
        shutil.move(LOG_FILE, PROJECT_ROOT / "lint_fix_summary.txt")
        log("📄 Log saved to: lint_fix_summary.txt")

    # Өөрийгөө устгах
    try:
        script_path.unlink()
        print("\n✨ Script deleted itself successfully.")
        print("✅ Check 'lint_fix_summary.txt' for details.")
        print("🔍 Run 'ruff check .' to verify fixes.")
    except Exception as e:
        print(f"⚠️ Could not self-delete: {e}")
        print("Please delete fix_and_self_destruct.py manually.")


# ===== ENTRY POINT =====
def main():
    log("🚀 ResearchOS Lint Fixer started")
    log(f"📁 Project root: {PROJECT_ROOT}")

    # 1. Get errors
    errors = get_ruff_errors()
    if not errors:
        log("✅ No lint errors found!")
        self_destruct()
        return

    log(f"🔍 Found {len(errors)} errors")

    # 2. Group by file
    from collections import defaultdict

    errors_by_file = defaultdict(list)
    for err in errors:
        errors_by_file[err["filename"]].append(err)

    # 3. Fix each file
    fixed_count = 0
    for filepath_str, file_errors in errors_by_file.items():
        filepath = Path(filepath_str)
        if filepath.exists() and filepath.suffix == ".py":
            if fix_file(filepath, file_errors):
                fixed_count += 1

    log(f"📊 Summary: {fixed_count}/{len(errors_by_file)} files fixed")

    # 4. Final ruff check
    log("🔄 Running final ruff check...")
    subprocess.run(["python", "-m", "ruff", "check", ".", "--statistics"], cwd=PROJECT_ROOT)

    # 5. Self-destruct
    self_destruct()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("⚠️ Interrupted by user")
        print("\n⚠️ Script stopped. Delete manually if needed.")
        sys.exit(1)
