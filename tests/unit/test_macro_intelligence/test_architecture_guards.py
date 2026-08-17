"""
ResearchOS Macro Intelligence Layer - Architecture Guard Tests (CI)

Tests for the runtime-enforceable architecture guards in
``macro_intelligence/audit/guards.py``.

These tests enforce the MIL architecture invariants:
  - MIL-GRD-001: no reverse dependency (lower tier importing higher tier)
  - MIL-GRD-002: no forbidden V1 core / quant / experiment imports
  - MIL-GRD-003: hash functions are deterministic (no runtime random)
  - MIL-GRD-004: persistent IDs are content-derived and deterministic
  - MIL-GRD-005: the full guard set is clean
  - Econometric algorithms are owned exclusively by the econometrics tier
"""

from __future__ import annotations

import pytest

from macro_intelligence.audit import guards


@pytest.fixture(scope="module")
def guard_report() -> dict:
    """Run all guards once for the whole module."""
    return guards.run_all()


class TestArchitectureGuards:
    """CI architecture guard tests."""

    def test_mil_grd_001_no_reverse_dependency(self, guard_report):
        """MIL-GRD-001: Lower tier must not import a higher tier."""
        violations = guard_report["reverse_dependencies"]
        # Yield a useful message listing any violations.
        assert violations == [], "Reverse dependency violations found: " + str(violations)

    def test_mil_grd_002_no_forbidden_import(self, guard_report):
        """MIL-GRD-002: No V1 core / quant / experiment imports."""
        violations = guard_report["forbidden_imports"]
        assert violations == [], "Forbidden V1/quant/experiment imports found: " + str(violations)

    def test_mil_grd_003_no_runtime_random_in_hash(self, guard_report):
        """MIL-GRD-003: Hash functions must be deterministic."""
        violations = guard_report["runtime_random_in_hash"]
        assert violations == [], "Non-deterministic runtime source in hash functions: " + str(
            violations
        )

    def test_mil_grd_004_persistent_id_determinism(self, guard_report):
        """MIL-GRD-004: Persistent IDs must be content-derived."""
        violations = guard_report["persistent_id_determinism"]
        assert violations == [], "Non-content-derived persistent ID generation found: " + str(
            violations
        )

    def test_mil_grd_005_full_guard_set_clean(self, guard_report):
        """MIL-GRD-005: The entire guard set is clean."""
        assert guards.is_clean(guard_report)


class TestGuardHelpers:
    """Unit tests for the guard helper functions."""

    def test_tier_ordering(self):
        """Tier ordering is monotonic and complete."""
        assert guards.TIERS[0] == "contracts"
        assert guards.TIERS[-1] == "audit"
        # Every tier maps to an index.
        for i, name in enumerate(guards.TIERS):
            assert guards.TIER_INDEX[name] == i

    def test_run_all_returns_all_checks(self):
        """run_all returns every guard category."""
        report = guards.run_all()
        assert set(report.keys()) == {
            "reverse_dependencies",
            "forbidden_imports",
            "runtime_random_in_hash",
            "persistent_id_determinism",
            "econometric_single_owner",
        }

    def test_is_clean_true_when_clean(self):
        """is_clean returns True when all categories are empty."""
        report = {
            "reverse_dependencies": [],
            "forbidden_imports": [],
            "runtime_random_in_hash": [],
            "persistent_id_determinism": [],
            "econometric_single_owner": [],
        }
        assert guards.is_clean(report) is True

    def test_is_clean_false_when_violation(self):
        """is_clean returns False when any category has a violation."""
        report = {
            "reverse_dependencies": [("a", "b")],
            "forbidden_imports": [],
            "runtime_random_in_hash": [],
            "persistent_id_determinism": [],
            "econometric_single_owner": [],
        }
        assert guards.is_clean(report) is False

    def test_econometric_single_owner_guard(self):
        """Econometric algorithms are owned exclusively by the econometrics tier."""
        violations = guards.check_econometric_single_owner()
        assert violations == [], (
            "Econometric algorithm implemented outside econometrics tier: " + str(violations)
        )
