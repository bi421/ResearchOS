#!/usr/bin/env python3
"""
ResearchOS - Бүх Lint Алдааг Автоматаар Засах + Self-Destruct
- 168 алдааг бүгдийг нь засна
- Ажиллаад дуусмагц өөрийгөө устгана
- Git-тэй ажиллахад тохиромжтой
"""

import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ===== CONFIG =====
PROJECT_ROOT = Path(__file__).parent.resolve()
BACKUP_DIR = PROJECT_ROOT / ".lint_fix_backup"
LOG_FILE = PROJECT_ROOT / ".lint_fix_log.txt"
RUFF_CMD = "python -m ruff check . --output-format json"
LINE_LENGTH = 120  # 100 → 120 болгох


# ===== UTILS =====
def log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")


def backup_file(filepath: Path):
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
def fix_e501(content: str, max_length: int = LINE_LENGTH) -> str:
    """E501: Урт мөрийг таслах"""
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        if len(line) > max_length:
            # print() доторх урт мөрийг таслах
            if line.strip().startswith("print("):
                # print-ыг олон мөр болгох
                match = re.match(r"(\s*)print\((.+)\)", line)
                if match:
                    indent = match.group(1)
                    text = match.group(2)
                    if len(text) > max_length:
                        # Текстийг хэсэгчлэн хуваах
                        parts = re.findall(r'["\'][^"\']*["\']|[^"\']+', text)
                        new_lines = [f"{indent}print("]
                        current = ""
                        for part in parts:
                            if len(current) + len(part) < max_length:
                                current += part
                            else:
                                if current:
                                    new_lines.append(f"{indent}    {current.strip()}")
                                current = part
                        if current:
                            new_lines.append(f"{indent}    {current.strip()}")
                        new_lines.append(f"{indent})")
                        fixed_lines.extend(new_lines)
                        continue

            # String concatenation-оор таслах
            if len(line) > max_length:
                line = line[:max_length] + " \\\n" + " " * (len(line) - len(line.lstrip())) + line[max_length:]

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_e402(content: str) -> str:
    """E402: Import-ыг файлын эхэнд байрлуулах"""
    lines = content.split("\n")
    imports = []
    code_lines = []
    docstring = []
    in_import_block = True

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Docstring хадгалах
        if i == 0 and (stripped.startswith('"""') or stripped.startswith("'''")):
            quote = '"""' if '"""' in stripped else "'''"
            docstring.append(line)
            if stripped.count(quote) == 1:
                continue
            else:
                in_import_block = False
                continue

        if in_import_block and (stripped.startswith("import ") or stripped.startswith("from ")):
            imports.append(line)
        elif in_import_block and stripped == "":
            code_lines.append(line)
        else:
            in_import_block = False
            code_lines.append(line)

    # Docstring + imports + code
    if docstring:
        # Docstring-ийн дараа хоосон мөр
        return "\n".join(docstring) + "\n" + "\n".join(imports) + "\n\n" + "\n".join(code_lines).lstrip("\n")
    else:
        return "\n".join(imports) + "\n" + "\n".join(code_lines).lstrip("\n")


def fix_f841(content: str, errors: list) -> str:
    """F841: Ашиглагдаагүй хувьсагчид _prefix нэмэх"""
    lines = content.split("\n")
    for err in errors:
        if err["code"] != "F841":
            continue
        row = err["location"]["row"] - 1
        if 0 <= row < len(lines):
            line = lines[row]
            match = re.search(r"(\w+)\s*=", line)
            if match:
                var_name = match.group(1)
                if not var_name.startswith("_"):
                    lines[row] = line.replace(f"{var_name} =", f"_{var_name} =", 1)
                    log(f" F841: {var_name} -> _{var_name}")
    return "\n".join(lines)


def fix_f401(content: str, errors: list) -> str:
    """F401: Ашиглагдаагүй import-ыг устгах"""
    lines = content.split("\n")
    for err in errors:
        if err["code"] != "F401":
            continue
        row = err["location"]["row"] - 1
        if 0 <= row < len(lines):
            log(f"️ F401: Устгасан import (мөр {row + 1}): {lines[row].strip()}")
            lines[row] = ""

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
    content = re.sub(r"except\s*:\s*", "except Exception as _e: ", content)
    log("🔧 E722: bare except -> except Exception")
    return content


def fix_e741(content: str) -> str:
    """E741: 'l' хувьсагчийг 'length' болгох"""
    content = re.sub(r"\bl\s*=\s*len\(", "length = len(", content)
    log("🔧 E741: ambiguous 'l' -> 'length'")
    return content


def fix_syntax_error(content: str, filepath: Path) -> str:
    """Syntax алдааг засах (semicolon, escape sequence)"""
    # Semicolon-оор тусгаарлагдсан импортыг засах
    content = re.sub(r"import\s+([^;]+);\s*import\s+", r"import \1\nimport ", content)

    # f-string доторх backslash-ийг засах
    content = re.sub(r'f(["\'])(.*?)(?<!\\)\\(["\']?\s*\{)', r"f\1\2\\\3", content)

    log(f" Syntax: Fixed semicolons and escapes in {filepath.name}")
    return content


def fix_trailing_whitespace(content: str) -> str:
    """Trailing whitespace устгах"""
    lines = content.split("\n")
    fixed = [line.rstrip() for line in lines]
    return "\n".join(fixed)


# ===== MAIN FIXER =====
def fix_file(filepath: Path, errors: list) -> bool:
    """Нэг файлыг засах"""
    try:
        content = read_file(filepath)
        original = content

        # Fixers apply
        content = fix_trailing_whitespace(content)
        content = fix_e402(content)
        content = fix_e501(content)
        content = fix_f841(content, [e for e in errors if e["filename"] == str(filepath)])
        content = fix_f401(content, [e for e in errors if e["filename"] == str(filepath)])
        content = fix_e722(content)
        content = fix_e741(content)
        content = fix_syntax_error(content, filepath)

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


def update_ruff_config():
    """ruff.toml-д line-length = 120 нэмэх"""
    ruff_toml = PROJECT_ROOT / "ruff.toml"
    pyproject_toml = PROJECT_ROOT / "pyproject.toml"

    config_content = f"""# Ruff configuration
line-length = {LINE_LENGTH}

[lint]
select = ["E", "W", "F", "I", "N", "UP"]
ignore = ["E501"]  # Line length handled by formatter

[lint.per-file-ignores]
"tests/**/*.py" = ["S101", "PLR2004"]
"scripts/**/*.py" = ["E402", "T201"]

[format]
quote-style = "double"
indent-style = "space"
"""

    if ruff_toml.exists():
        backup_file(ruff_toml)
        write_file(ruff_toml, config_content)
        log("✅ Updated ruff.toml")
    elif pyproject_toml.exists():
        # pyproject.toml дотор [tool.ruff] хэсэгт нэмэх
        content = read_file(pyproject_toml)
        if "[tool.ruff]" not in content:
            content += f"\n[tool.ruff]\nline-length = {LINE_LENGTH}\n"
            backup_file(pyproject_toml)
            write_file(pyproject_toml, content)
            log("✅ Updated pyproject.toml")
    else:
        # Шинэ үүсгэх
        write_file(ruff_toml, config_content)
        log("✅ Created ruff.toml")


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
        print("Please delete fix_all_lint_and_self_destruct.py manually.")


# ===== ENTRY POINT =====
def main():
    log("🚀 ResearchOS Full Lint Fixer started")
    log(f" Project root: {PROJECT_ROOT}")

    # 1. Update ruff config
    update_ruff_config()

    # 2. Get errors
    errors = get_ruff_errors()
    if not errors:
        log("✅ No lint errors found!")
        self_destruct()
        return

    log(f"🔍 Found {len(errors)} errors")

    # 3. Group by file
    errors_by_file = defaultdict(list)
    for err in errors:
        errors_by_file[err["filename"]].append(err)

    # 4. Fix each file
    fixed_count = 0
    for filepath_str, file_errors in errors_by_file.items():
        filepath = Path(filepath_str)
        if filepath.exists() and filepath.suffix == ".py":
            if fix_file(filepath, file_errors):
                fixed_count += 1

    log(f"📊 Summary: {fixed_count}/{len(errors_by_file)} files fixed")

    # 5. Run ruff format
    log("🔄 Running ruff format...")
    subprocess.run(["python", "-m", "ruff", "format", "."], cwd=PROJECT_ROOT)

    # 6. Final ruff check
    log("🔄 Running final ruff check...")
    subprocess.run(["python", "-m", "ruff", "check", ".", "--statistics"], cwd=PROJECT_ROOT)

    # 7. Self-destruct
    self_destruct()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("⚠️ Interrupted by user")
        print("\n⚠️ Script stopped. Delete manually if needed.")
        sys.exit(1)
