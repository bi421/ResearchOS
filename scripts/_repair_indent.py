"""One-shot repair: rewrite the XAUUSD dict-entry line to a clean, ASCII-only line.

Removes any stray non-printable/control characters that may have been injected,
and collapses indentation to exactly 4 spaces (inside the SYMBOLS dict the brace
context ignores indentation, but we keep it clean). Preserves a leading UTF-8
BOM if present.
"""

import pathlib
import re

FILES = [
    "run_verified.py",
    "run_trend_analysis.py",
    "run_trend_analysis_fixed.py",
    "run_full_analysis.py",
    "run_full_analysis_fixed.py",
    "run_full_analysis_fixed2.py",
    "run_full_analysis_fixed3.py",
    "run_full_analysis_fixed4.py",
]

CLEAN = "    'XAUUSD': resolve_xauusd_spot_proxy(),  # XAUUSD spot proxy (canonical yfinance spot ref; NOT real data)"

# Match a line beginning (after optional leading whitespace) with the literal
# 'XAUUSD': dict entry. Does NOT match the loop guard (which is
# `assert_xauusd_identity(...)` and contains "as XAUUSD spot", no `'XAUUSD':`).
ENTRY = re.compile(r"^[ \t]*'XAUUSD':.*$", re.M)


def repair(path: pathlib.Path) -> None:
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw[3 if has_bom else 0 :].decode("utf-8")
    new_text, n = ENTRY.subn(lambda _m: CLEAN, text, count=1)
    if n:
        out = (b"\xef\xbb\xbf" if has_bom else b"") + new_text.encode("utf-8")
        path.write_bytes(out)
        print(f"repaired {path.name} ({n} line)")
    else:
        print(f"NO MATCH in {path.name}")


def main() -> None:
    for name in FILES:
        repair(pathlib.Path(name))


if __name__ == "__main__":
    main()
