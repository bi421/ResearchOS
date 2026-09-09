from __future__ import annotations

import pytest

from researchos.market_memory.production_quant_backend import (
    run_production_quant_backend_audit,
)
from researchos.quant_engine.cpp_backend import has_cpp_engine


pytestmark = pytest.mark.skipif(
    not has_cpp_engine(),
    reason="compiled C++ Quant Engine not available",
)


def test_production_quant_audit_requires_and_records_cpp_backend() -> None:
    audit = run_production_quant_backend_audit(
        [100.0, 101.0, 100.5, 102.0, 103.0],
        require_cpp=True,
    )

    assert audit.returns["backend"] == "CppQuantAdapter"
    assert audit.returns["fallback_used"] is False
    assert audit.returns["validation_status"] == "passed"
    assert audit.returns["error_code"] == "ok"
    assert audit.returns["count"] == 4

    assert audit.statistics["backend"] == "CppQuantAdapter"
    assert audit.statistics["fallback_used"] is False
    assert audit.statistics["validation_status"] == "passed"
    assert audit.statistics["error_code"] == "ok"
    assert audit.statistics["count"] == 4
    assert "mean" in audit.statistics
    assert "stddev" in audit.statistics
