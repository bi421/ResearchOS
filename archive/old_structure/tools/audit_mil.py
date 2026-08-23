"""
ResearchOS Macro Intelligence Layer - Architecture Audit & Consolidation
Static analysis tool (read-only). Produces audit reports for the audit phase.
This is a verification utility, NOT part of the MIL runtime.
"""

import ast
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIL = os.path.join(ROOT, "macro_intelligence")

# Layer tiers in dependency order (lower -> higher)
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

# Top-level module -> tier rank
TIER_INDEX = {name: i for i, name in enumerate(TIERS)}
# aliases
TIER_INDEX.update(
    {
        "features": 6,
        "statistics": 7,
        "econometrics": 8,
        "relationships": 9,
        "regime": 10,
        "knowledge": 11,
        "storage": 12,
        "audit": 13,
    }
)

FORBIDDEN_ROOT = [
    "researchos",  # V1 core
    "quant_engine",
    "cpp_quant_engine",
    "experiment",
    "strategy",
    "execution",
]
FORBIDDEN_PATTERNS = ["researchos.core", "researchos.quant_engine", "researchos.experiment"]


def get_module_name(path):
    """Convert a file path under macro_intelligence to module name."""
    rel = os.path.relpath(path, MIL)
    parts = rel.replace("\\", "/").split("/")
    parts = ["macro_intelligence"] + parts
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def top_level_pkg(module):
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] == "macro_intelligence":
        return parts[1]
    return parts[0]


def analyze_imports(path):
    """Return list of (module, imported_name, is_relative) for a file."""
    results = []
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except Exception as e:
        return [("__PARSE_ERROR__", str(e), False)]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                results.append((alias.name, alias.asname or "", False))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                results.append((node.module or "", alias.name, node.level > 0))
    return results


def dependency_audit():
    """Build import graph, detect reverse/circular/forbidden deps."""
    edges = []  # (from_module, to_top_pkg, to_module)
    for r, _, fs in os.walk(MIL):
        for f in fs:
            if not f.endswith(".py"):
                continue
            path = os.path.join(r, f)
            src_module = get_module_name(path)
            src_pkg = top_level_pkg(src_module)
            for imp, _, is_rel in analyze_imports(path):
                if not imp:
                    continue
                if imp.startswith("macro_intelligence"):
                    target = imp
                else:
                    continue
                edges.append((src_module, target))

    # Detect reverse dependency (higher tier importing lower tier is OK; lower importing higher is a violation)
    reversals = []
    for src, tgt in edges:
        src_pkg = top_level_pkg(src)
        tgt_pkg = top_level_pkg(tgt)
        if src_pkg == tgt_pkg:
            continue
        s_r = TIER_INDEX.get(src_pkg)
        t_r = TIER_INDEX.get(tgt_pkg)
        if s_r is None or t_r is None:
            continue
        if t_r > s_r:
            # higher tier imported by lower tier => reverse dependency violation
            reversals.append((src, tgt))

    # Forbidden imports
    forbidden_hits = []
    for src, tgt in edges:
        for fp in FORBIDDEN_PATTERNS:
            if fp in tgt:
                forbidden_hits.append((src, tgt))
        for froot in FORBIDDEN_ROOT:
            if tgt.startswith(froot):
                forbidden_hits.append((src, tgt))

    return edges, reversals, forbidden_hits


def immutability_audit():
    """Check @dataclass(frozen=True) usage and mutable defaults."""
    findings = []
    for r, _, fs in os.walk(MIL):
        for f in fs:
            if not f.endswith(".py"):
                continue
            path = os.path.join(r, f)
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call) and getattr(dec.func, "id", "") == "dataclass":
                            frozen = False
                            for kw in dec.keywords:
                                if kw.arg == "frozen" and isinstance(kw.value, ast.Constant):
                                    frozen = kw.value.value
                            if not frozen:
                                findings.append(("NON_FROZEN_DATACLASS", get_module_name(path), node.name))
                # Mutable defaults in dataclass fields
                if isinstance(node, ast.ClassDef):
                    for stmt in node.body:
                        if isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                            # check for default_factory or mutable literal
                            v = stmt.value
                            if isinstance(v, ast.List) or isinstance(v, ast.Dict) or isinstance(v, ast.Set):
                                findings.append(
                                    (
                                        "MUTABLE_DEFAULT",
                                        get_module_name(path),
                                        node.name + "." + (stmt.target.id if isinstance(stmt.target, ast.Name) else "?"),
                                    )
                                )
    return findings


def determinism_audit():
    """Detect random/uuid4/utcnow usage in hash functions."""
    findings = []
    for r, _, fs in os.walk(MIL):
        for f in fs:
            if not f.endswith(".py"):
                continue
            path = os.path.join(r, f)
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and "hash" in node.name.lower():
                    for sub in ast.walk(node):
                        if isinstance(sub, ast.Call):
                            fn = sub.func
                            if isinstance(fn, ast.Attribute):
                                name = fn.attr
                            elif isinstance(fn, ast.Name):
                                name = fn.id
                            else:
                                name = ""
                            if name in ("random", "uuid4", "randint", "utcnow", "now", "secrets"):
                                findings.append(
                                    (
                                        "HASH_RUNTIME_RANDOM",
                                        get_module_name(path),
                                        node.name + " -> " + name,
                                    )
                                )
    return findings


def provenance_audit():
    """Check provenance fields exist in key models."""
    findings = []
    targets = {
        "evidence": "ProvenanceChain",
        "knowledge": "KnowledgeProvenance",
    }
    for name, klass in targets.items():
        found = False
        for r, _, fs in os.walk(MIL):
            for f in fs:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(r, f)
                try:
                    tree = ast.parse(open(path, encoding="utf-8").read())
                except Exception:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == klass:
                        found = True
        findings.append((name, klass, "PRESENT" if found else "MISSING"))
    return findings


def version_audit():
    """Collect version constants."""
    versions = []
    pat = re.compile(r"(VERSION|ALGORITHM_VERSION|RULES_VERSION|_VERSION)\s*=\s*[\"']([^\"']+)[\"']")
    for r, _, fs in os.walk(MIL):
        for f in fs:
            if not f.endswith(".py"):
                continue
            path = os.path.join(r, f)
            try:
                content = open(path, encoding="utf-8").read()
            except Exception:
                continue
            for m in pat.finditer(content):
                versions.append((get_module_name(path), m.group(1), m.group(2)))
    return versions


def duplicate_stat_audit():
    """Detect duplicate IMPLEMENTATIONS of statistical functions.

    A function is a genuine duplicate owner if it:
    - names a statistical algorithm (pearson/spearman/mean/std/...)
    - is NOT a thin delegating wrapper (i.e. its body contains an actual
      arithmetic/mathematical implementation, not just a call to another
      module).
    """
    stat_funcs = [
        "mean",
        "median",
        "std",
        "variance",
        "var",
        "pearson",
        "spearman",
        "regression",
        "cusum",
        "rolling",
        "ema",
        "moving_average",
        "trend",
        "zscore",
        "z_score",
        "volatility",
    ]
    owners = defaultdict(list)
    for r, _, fs in os.walk(MIL):
        for f in fs:
            if not f.endswith(".py"):
                continue
            path = os.path.join(r, f)
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except Exception:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                for sf in stat_funcs:
                    if sf not in node.name.lower():
                        continue
                    # Inspect ONLY the executable statement body for a real
                    # implementation (excludes `returns` and argument type
                    # annotations which can contain BinOp like `float | None`).
                    # A pure delegating wrapper body is exactly:
                    #   try: return X(...) except Exception: return ...
                    # or   return other_fn(...)
                    # We detect real implementation by the presence of
                    # arithmetic operators (BinOp Add/Sub/Mult/Div/Pow)
                    # or a loop (For/While) or math.sqrt / sum-based math.
                    has_math = False
                    for stmt in node.body:
                        for sub in ast.walk(stmt):
                            if isinstance(sub, ast.BinOp) and isinstance(
                                sub.op,
                                (
                                    ast.Add,
                                    ast.Sub,
                                    ast.Mult,
                                    ast.Div,
                                    ast.Pow,
                                    ast.Mod,
                                ),
                            ):
                                has_math = True
                                break
                            if isinstance(sub, (ast.For, ast.While)):
                                has_math = True
                                break
                            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr in ("sqrt", "exp", "log", "pow"):
                                has_math = True
                                break
                    if has_math:
                        owners[sf].append(get_module_name(path) + "." + node.name)
    return dict(owners)


def main():
    report = {}
    report["import_edges"] = dependency_audit()[0]
    report["reverse_deps"] = dependency_audit()[1]
    report["forbidden_hits"] = dependency_audit()[2]
    report["immutability"] = immutability_audit()
    report["determinism"] = determinism_audit()
    report["provenance"] = provenance_audit()
    report["versions"] = version_audit()
    report["stat_owners"] = duplicate_stat_audit()

    print("=== REVERSE DEPENDENCY VIOLATIONS (lower tier importing higher tier) ===")
    for src, tgt in report["reverse_deps"]:
        print(f"  {src}  ->  {tgt}")
    if not report["reverse_deps"]:
        print("  NONE")

    print("\n=== FORBIDDEN / V1 / QUANT / EXPERIMENT IMPORTS ===")
    for src, tgt in report["forbidden_hits"]:
        print(f"  {src}  ->  {tgt}")
    if not report["forbidden_hits"]:
        print("  NONE")

    print("\n=== NON-FROZEN DATACLASSES / MUTABLE DEFAULTS ===")
    for kind, mod, cls in report["immutability"]:
        print(f"  [{kind}] {mod}.{cls}")
    if not report["immutability"]:
        print("  NONE")

    print("\n=== DETERMINISM (runtime random in hash functions) ===")
    for kind, mod, fn in report["determinism"]:
        print(f"  [{kind}] {mod}.{fn}")
    if not report["determinism"]:
        print("  NONE")

    print("\n=== PROVENANCE PRESENCE ===")
    for name, klass, status in report["provenance"]:
        print(f"  {name}.{klass}: {status}")

    print("\n=== STATISTICAL FUNCTION OWNERSHIP (duplicate check) ===")
    for fn, owners in sorted(report["stat_owners"].items()):
        if len(owners) > 1:
            print(f"  {fn}: {len(owners)} owners ->")
            for o in owners:
                print(f"      {o}")
    print("  (only multi-owner functions listed above)")

    print("\n=== VERSION CONSTANTS ===")
    for mod, var, val in report["versions"]:
        print(f"  {mod}: {var} = {val}")

    with open(os.path.join(ROOT, "audit_mil_data.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    print("\nSaved audit_mil_data.json")


if __name__ == "__main__":
    main()
