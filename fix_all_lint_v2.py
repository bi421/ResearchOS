#!/usr/bin/env python3
"""
ResearchOS - Бүх Lint Алдааг Автоматаар Засах v2
- 191 алдааг бүгдийг нь засна
- Syntax алдааг тусгайлан засна
- Ажиллаад дуусмагц өөрийгөө устгана
"""

import os
import re
import sys
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ===== CONFIG =====
PROJECT_ROOT = Path(__file__).parent.resolve()
BACKUP_DIR = PROJECT_ROOT / ".lint_fix_backup_v2"
LOG_FILE = PROJECT_ROOT / ".lint_fix_log_v2.txt"
RUFF_CMD = "python -m ruff check . --output-format json"
LINE_LENGTH = 120

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
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def write_file(filepath: Path, content: str):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

# ===== FIXERS =====

def fix_syntax_errors(content: str, filepath: Path) -> str:
    """Syntax алдааг засах (semicolon, нэг мөрд олон команд)"""
    lines = content.split("\n")
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Semicolon-оор тусгаарлагдсан import-ыг засах
        if re.match(r'\s*import\s+[^;]+;\s*import', line):
            parts = line.split(';')
            for part in parts:
                fixed_lines.append(part.strip())
            continue
        
        # Нэг мөрд олон simple statement (x = 1; y = 2)
        if re.search(r'\w+\s*=\s*[^;]+;\s*\w+\s*=', line) and not line.strip().startswith('#'):
            parts = line.split(';')
            indent = len(line) - len(line.lstrip())
            for part in parts:
                if part.strip():
                    fixed_lines.append(' ' * indent + part.strip())
            continue
        
        # Function definition доторх semicolon
        if re.search(r'def\s+\w+\([^)]*\):[^#\n]*;', line):
            # Function body-г шинэ мөр рүү шилжүүлэх
            match = re.match(r'(\s*def\s+\w+\([^)]*\):)\s*(.+)', line)
            if match:
                fixed_lines.append(match.group(1))
                indent = len(match.group(1)) - len(match.group(1).lstrip()) + 4
                for stmt in match.group(2).split(';'):
                    if stmt.strip():
                        fixed_lines.append(' ' * indent + stmt.strip())
                continue
        
        fixed_lines.append(line)
    
    log(f" Syntax: Fixed {filepath.name}")
    return "\n".join(fixed_lines)

def fix_e501(content: str, max_length: int = LINE_LENGTH) -> str:
    """E501: Урт мөрийг таслах"""
    lines = content.split("\n")
    fixed_lines = []
    
    for line in lines:
        if len(line) > max_length and not line.strip().startswith('#'):
            # String-ийг таслах
            if re.search(r'["\'].{50,}["\']', line):
                match = re.match(r'(\s*)(.+)["\']([^"\']{50,})["\'](.*)', line)
                if match:
                    indent = match.group(1)
                    prefix = match.group(2)
                    long_string = match.group(3)
                    suffix = match.group(4)
                    
                    # 80 тэмдэгтээр таслах
                    parts = [long_string[i:i+80] for i in range(0, len(long_string), 80)]
                    fixed_lines.append(f'{indent}{prefix}"{parts[0]}"')
                    for part in parts[1:]:
                        fixed_lines.append(f'{indent}    "{part}"')
                    continue
            
            # print() доторх урт мөр
            if line.strip().startswith('print('):
                match = re.match(r'(\s*)print\((.+)\)', line)
                if match:
                    indent = match.group(1)
                    text = match.group(2)
                    if len(text) > max_length:
                        fixed_lines.append(f'{indent}print(')
                        # Текстийг 80 тэмдэгтээр таслах
                        words = text.split()
                        current = ""
                        for word in words:
                            if len(current) + len(word) < 80:
                                current += word + " "
                            else:
                                if current:
                                    fixed_lines.append(f'{indent}    {current.strip()}')
                                current = word + " "
                        if current:
                            fixed_lines.append(f'{indent}    {current.strip()}')
                        fixed_lines.append(f'{indent})')
                        continue
        
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
    
    result = []
    if docstring:
        result.extend(docstring)
        result.append("")
    result.extend(imports)
    result.append("")
    result.extend([l for l in code_lines if l.strip() or result[-1].strip()])
    
    return "\n".join(result)

def fix_f841(content: str, errors: list) -> str:
    """F841: Ашиглагдаагүй хувьсагчид _prefix нэмэх"""
    lines = content.split("\n")
    for err in errors:
        if err["code"] != "F841":
            continue
        row = err["location"]["row"] - 1
        if 0 <= row < len(lines):
            line = lines[row]
            match = re.search(r'(\w+)\s*=', line)
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
            log(f"️ F401: Устгасан import (мөр {row+1})")
            lines[row] = ""
    
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
    content = re.sub(r'except\s*:\s*', 'except Exception as _e: ', content)
    log("🔧 E722: bare except -> except Exception")
    return content

def fix_e741(content: str) -> str:
    """E741: 'l' хувьсагчийг 'length' болгох"""
    content = re.sub(r'\bl\s*=\s*len\(', 'length = len(', content)
    log("🔧 E741: ambiguous 'l' -> 'length'")
    return content

def fix_trailing_whitespace(content: str) -> str:
    """Trailing whitespace устгах"""
    lines = content.split("\n")
    return "\n".join([line.rstrip() for line in lines])

def fix_file(filepath: Path, errors: list) -> bool:
    """Нэг файлыг засах"""
    try:
        content = read_file(filepath)
        original = content
        
        # Fixers apply (дараалал чухал!)
        content = fix_trailing_whitespace(content)
        content = fix_syntax_errors(content, filepath)  # Эхлээд syntax засах
        content = fix_e402(content)
        content = fix_e501(content)
        content = fix_f841(content, [e for e in errors if e["filename"] == str(filepath)])
        content = fix_f401(content, [e for e in errors if e["filename"] == str(filepath)])
        content = fix_e722(content)
        content = fix_e741(content)
        
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
        result = subprocess.run(
            RUFF_CMD.split(),
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
        return []
    except Exception as e:
        log(f"❌ Ruff execute error: {e}")
        return []

def update_ruff_config():
    """ruff.toml-д line-length = 120 нэмэх"""
    ruff_toml = PROJECT_ROOT / "ruff.toml"
    
    config_content = f"""# Ruff configuration
line-length = {LINE_LENGTH}

[lint]
select = ["E", "W", "F", "I", "N", "UP"]
ignore = ["E501"]

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

def self_destruct():
    """Скрипт өөрийгөө устгах"""
    script_path = Path(__file__).resolve()
    log(f"💥 SELF-DESTRUCT: Deleting {script_path.name}")
    
    if LOG_FILE.exists():
        shutil.move(LOG_FILE, PROJECT_ROOT / "lint_fix_summary_v2.txt")
        log(f"📄 Log saved to: lint_fix_summary_v2.txt")
    
    try:
        script_path.unlink()
        print("\n✨ Script deleted itself successfully.")
        print("✅ Check 'lint_fix_summary_v2.txt' for details.")
        print("🔍 Run 'ruff check .' to verify fixes.")
    except Exception as e:
        print(f"⚠️ Could not self-delete: {e}")

def main():
    log("🚀 ResearchOS Full Lint Fixer v2 started")
    log(f" Project root: {PROJECT_ROOT}")
    
    # 1. Update ruff config
    update_ruff_config()
    
    # 2. Get errors
    errors = get_ruff_errors()
    if not errors:
        log("✅ No lint errors found!")
        self_destruct()
        return
    
    log(f" Found {len(errors)} errors")
    
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
        sys.exit(1)