import re
from pathlib import Path

FORBIDDEN_TRADING_APIS = re.compile(r"order_send|order_modify|order_close|order_delete|" r"OrderSend|OrderModify|OrderClose|OrderDelete")


def test_mt5_no_trading():
    """
    Constitutional invariant:

    ResearchOS source code must not contain broker
    trade-execution API calls.

    The test itself is excluded from scanning.
    Python cache files are excluded.
    """

    roots = [
        Path("researchos"),
        Path("scripts"),
    ]

    test_file = Path(__file__).resolve()

    excluded_parts = {
        "__pycache__",
    }

    violations = []

    for root in roots:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if path.resolve() == test_file:
                continue

            if any(part in excluded_parts for part in path.parts):
                continue

            if path.suffix.lower() not in {
                ".py",
                ".pyw",
                ".pyi",
                ".cpp",
                ".h",
                ".hpp",
                ".c",
                ".cc",
                ".cxx",
            }:
                continue

            try:
                text = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except OSError:
                continue

            for line_number, line in enumerate(
                text.splitlines(),
                start=1,
            ):
                if FORBIDDEN_TRADING_APIS.search(line):
                    violations.append(f"{path}:{line_number}: {line.strip()}")

    assert not violations, "Forbidden broker execution references found:\n" + "\n".join(violations)
