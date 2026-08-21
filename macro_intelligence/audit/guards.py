"""
ResearchOS Macro Intelligence Layer - Architecture Guards (CI)

Runtime-enforceable architecture invariants for the Macro Intelligence Layer.

These guards mirror the static audit performed by ``audit_mil.py`` but are
importable inside the package so CI tests can enforce them directly. They
encode the same MIL tier ordering and forbidden-import rules.

Guards included:
  - ``check_no_reverse_dependency``   lower tier must not import higher tier
  - ``check_no_forbidden_import``     no V1 core / quant / experiment imports
  - ``check_no_runtime_random_in_hash``  hash functions must be deterministic
  - ``check_persistent_id_determinism``  persistent IDs derive from content

All guards are pure AST-based, stdlib-only, and read-only. They never modify
source; they only inspect and report.
"""

from __future__ import annotations

import ast
import os
from typing import Any

# Layer tiers in dependency order (lower -> higher). Mirrors audit_mil.py.
TIERS = [
    "contracts",
    "time",
    "interfaces",
    "revision",
    "provenance",
    "revision_provenance",
    "features",
    "statistics",
    "econometrics",
    "relationships",
    "regime",
    "knowledge",
    "storage",
    "audit",
]
TIER_INDEX = {name: i for i, name in enumerate(TIERS)}

# Econometric algorithms that MUST be owned exclusively by the econometrics
# tier. If any implementation appears in another tier, the CI guard fails.
# (The statistics tier is the sole owner of OLS; econometrics reuses it, so
# OLS is deliberately NOT in this single-owner list.)
ECONOMETRIC_SINGLE_OWNER = [
    "augmented_dickey_fuller",
    "adf",
    "kpss",
    "granger",
    "engle_granger",
    "variance_inflation_factor",
    "vif",
    "breusch_pagan",
    "jarque_bera",
    "durbin_watson",
    "partial_autocorrelation",
    "autocorrelation",
]

FORBIDDEN_ROOT = [
    "researchos",  # V1 core
    "quant_engine",
    "cpp_quant_engine",
    "experiment",
    "strategy",
    "execution",
]
FORBIDDEN_PATTERNS = [
    "researchos.core",
    "researchos.quant_engine",
    "researchos.experiment",
]

# Function/subroutine names that indicate non-deterministic runtime sources.
_RUNTIME_RANDOM = frozenset({"random", "uuid4", "randint", "utcnow", "now", "secrets"})


def _milk_root() -> str:
    """Return the absolute path of the macro_intelligence package."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _python_files(base: str) -> list[str]:
    """Yield all ``.py`` files under ``base`` (recursively)."""
    files = []
    for r, _dirs, fs in os.walk(base):
        for f in fs:
            if f.endswith(".py"):
                files.append(os.path.join(r, f))
    return files


def _module_name(path: str) -> str:
    """Convert a file path under ``macro_intelligence`` to a dotted module name."""
    base = _milk_root()
    rel = os.path.relpath(path, base)
    parts = rel.replace("\\", "/").split("/")
    parts = ["macro_intelligence"] + parts
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _top_level_pkg(module: str) -> str:
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] == "macro_intelligence":
        return parts[1]
    return parts[0]


def _imports(path: str) -> list[tuple[str, str]]:
    """Return list of (module, imported_name) for a file."""
    results = []
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except Exception as exc:  # pragma: no cover - defensive
        return [("__PARSE_ERROR__", str(exc))]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                results.append((alias.name, alias.asname or ""))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                results.append((node.module or "", alias.name))
    return results


def check_no_reverse_dependency() -> list[tuple[str, str]]:
    """
    Return list of (source_module, target_module) reverse-dependency
    violations. A violation is a lower-tier module importing a higher-tier
    module.
    """
    violations = []
    for path in _python_files(_milk_root()):
        src = _module_name(path)
        src_pkg = _top_level_pkg(src)
        for imp, _name in _imports(path):
            if not imp.startswith("macro_intelligence"):
                continue
            tgt_pkg = _top_level_pkg(imp)
            if src_pkg == tgt_pkg:
                continue
            s_r = TIER_INDEX.get(src_pkg)
            t_r = TIER_INDEX.get(tgt_pkg)
            if s_r is None or t_r is None:
                continue
            if t_r > s_r:
                violations.append((src, imp))
    return violations


def check_no_forbidden_import() -> list[tuple[str, str]]:
    """Return list of (source_module, target_module) forbidden imports."""
    hits = []
    for path in _python_files(_milk_root()):
        src = _module_name(path)
        for imp, _name in _imports(path):
            for fp in FORBIDDEN_PATTERNS:
                if fp in imp:
                    hits.append((src, imp))
            for froot in FORBIDDEN_ROOT:
                if imp.startswith(froot):
                    hits.append((src, imp))
    return hits


def check_no_runtime_random_in_hash() -> list[tuple[str, str]]:
    """
    Return list of (module, function) where a hash-like function calls
    a non-deterministic runtime source (random/uuid4/utcnow/now/secrets).
    """
    hits = []
    for path in _python_files(_milk_root()):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or "hash" not in node.name.lower():
                continue
            for sub in ast.walk(node):
                if not isinstance(sub, ast.Call):
                    continue
                fn = sub.func
                if isinstance(fn, ast.Attribute):
                    name = fn.attr
                elif isinstance(fn, ast.Name):
                    name = fn.id
                else:
                    name = ""
                if name in _RUNTIME_RANDOM:
                    hits.append((_module_name(path), node.name + " -> " + name))
    return hits


def check_persistent_id_determinism() -> list[tuple[str, str]]:
    """
    Return list of (module, function) where a persistent-id generator uses a
    non-content-derived source (uuid4/random/utcnow/now) in its ID string.

    Persistent identifiers must be content-derived and deterministic:
    identical scientific inputs must produce identical identifiers. This
    guard catches any future regression that introduces wall-clock or random
    components into persistent IDs.
    """
    hits = []
    # Functions that plausibly generate persistent IDs (by name).
    id_hint = ("id", "identifier", "hash", "analysis_id", "transition_id", "classification_id")
    for path in _python_files(_milk_root()):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if not any(h in node.name.lower() for h in id_hint):
                continue
            for sub in ast.walk(node):
                if not isinstance(sub, ast.Call):
                    continue
                fn = sub.func
                if isinstance(fn, ast.Attribute):
                    name = fn.attr
                elif isinstance(fn, ast.Name):
                    name = fn.id
                else:
                    name = ""
                if name in ("uuid4", "random", "randint", "utcnow", "secrets"):
                    hits.append((_module_name(path), node.name + " -> " + name))
    return hits


def check_econometric_single_owner() -> list[tuple[str, str]]:
    """
    Return list of (module, function) where an econometric algorithm is
    implemented outside the ``econometrics`` tier.

    The econometrics tier is the ONLY owner of ADF, KPSS, Granger,
    Engle-Granger, VIF, Breusch-Pagan, Jarque-Bera, Durbin-Watson, and
    autocorrelation. If any of these appear as a function in another tier,
    this guard flags it.

    Returns:
        List of (module, function) violations.
    """
    violations = []
    for path in _python_files(_milk_root()):
        module = _module_name(path)
        pkg = _top_level_pkg(module)
        if pkg == "econometrics":
            continue
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            name = node.name.lower()
            for algo in ECONOMETRIC_SINGLE_OWNER:
                if algo in name:
                    violations.append((module, node.name))
    return violations


def run_all() -> dict[str, Any]:
    """Run every guard and return a structured report."""
    return {
        "reverse_dependencies": check_no_reverse_dependency(),
        "forbidden_imports": check_no_forbidden_import(),
        "runtime_random_in_hash": check_no_runtime_random_in_hash(),
        "persistent_id_determinism": check_persistent_id_determinism(),
        "econometric_single_owner": check_econometric_single_owner(),
    }


def is_clean(report: dict[str, Any] | None = None) -> bool:
    """Return True if every guard passes (no violations)."""
    if report is None:
        report = run_all()
    return all(not v for v in report.values())


__all__ = [
    "TIERS",
    "TIER_INDEX",
    "ECONOMETRIC_SINGLE_OWNER",
    "check_no_reverse_dependency",
    "check_no_forbidden_import",
    "check_no_runtime_random_in_hash",
    "check_persistent_id_determinism",
    "check_econometric_single_owner",
    "run_all",
    "is_clean",
]
