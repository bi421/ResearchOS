"""
Certification tests for the Certified Analytical Compute Surface (Phase 5.1).

Phase 5.1 — Certified Analytical Compute Surface (WP-1 + WP-4).
These tests validate that the research backends (Python reference + C++
candidate) satisfy the certification contract:

    - capability declaration (deterministic, stateless, no timestamps)
    - determinism (identical inputs -> identical hashes/outputs)
    - parity (C++ candidate output matches Python reference)
    - NaN/Inf deterministic handling via canonical hashing
    - edge cases / error propagation
    - provenance chaining (input_hash -> result_hash)
    - ResearchResult structure

Pure research-only tests; no trading logic.
"""

import pytest

from researchos.quant_engine.research_cpp_backend import ResearchCppBackend
from researchos.quant_engine.research_engine import (
    PythonResearchBackend,
    ResearchEngine,
    research_capabilities,
)
from researchos.quant_engine.research_interface import (
    RESEARCH_OPERATIONS,
    RESEARCH_SURFACE_VERSION,
    ResearchResult,
)
from researchos.quant_engine.technical.contracts import Bars, IndicatorSpec


def _bars(length: int = 50) -> Bars:
    open_prices = [100.0 + (i * 0.5) for i in range(length)]
    high_prices = [o + 1.5 for o in open_prices]
    low_prices = [o - 1.0 for o in open_prices]
    close_prices = [o + 0.5 for o in open_prices]
    volumes = [1000.0 + i * 10.0 for i in range(length)]
    return Bars(
        open=open_prices,
        high=high_prices,
        low=low_prices,
        close=close_prices,
        volume=volumes,
    )


def _returns(length: int = 60) -> list:
    return [0.01 if i % 2 == 0 else -0.008 for i in range(length)]


class TestCapabilities:
    def test_research_operations_defined(self):
        assert "research_technical" in RESEARCH_OPERATIONS
        assert "research_probabilistic_fit" in RESEARCH_OPERATIONS
        assert "research_probabilistic_hypothesis" in RESEARCH_OPERATIONS
        assert "research_portfolio_metrics" in RESEARCH_OPERATIONS
        assert "research_historical" in RESEARCH_OPERATIONS
        assert "research_fundamental" in RESEARCH_OPERATIONS
        assert "research_econometric_analysis" in RESEARCH_OPERATIONS
        assert "research_validation" in RESEARCH_OPERATIONS

    def test_surface_version(self):
        assert RESEARCH_SURFACE_VERSION == "1.0.0"

    def test_python_backend_capabilities(self):
        backend = PythonResearchBackend()
        caps = backend.capabilities()
        assert caps.deterministic is True
        assert caps.stateless is True
        assert caps.no_timestamps is True
        assert caps.no_randomness is True
        assert caps.explicit_typing is True
        assert caps.backend_name == "PythonResearchBackend"

    def test_capabilities_support_research_ops(self):
        backend = PythonResearchBackend()
        # The research operations are exposed via research_capabilities().
        caps = research_capabilities(backend)
        for op in RESEARCH_OPERATIONS:
            assert op in caps.supported_operations

    def test_cpp_backend_capabilities(self):
        backend = ResearchCppBackend()
        caps = backend.capabilities()
        assert caps.deterministic is True
        assert caps.stateless is True
        assert caps.no_timestamps is True
        assert caps.no_randomness is True
        assert caps.explicit_typing is True


class TestResearchResultStructure:
    def test_result_has_hashes(self):
        backend = PythonResearchBackend()
        result = backend.research_probabilistic_fit(_returns(40), "normal")
        assert isinstance(result, ResearchResult)
        assert result.operation == "research_probabilistic_fit"
        assert result.domain == "probability"
        assert result.input_hash != ""
        assert result.result_hash != ""
        assert result.backend == "PythonResearchBackend"
        assert result.methodology_version == RESEARCH_SURFACE_VERSION

    def test_result_to_dict_roundtrip(self):
        backend = PythonResearchBackend()
        result = backend.research_probabilistic_fit(_returns(40), "normal")
        data = result.to_dict()
        restored = ResearchResult.from_dict(data)
        assert restored.operation == result.operation
        assert restored.result_hash == result.result_hash
        assert restored.output == result.output


class TestDeterminism:
    def test_probability_fit_deterministic(self):
        backend = PythonResearchBackend()
        r1 = backend.research_probabilistic_fit(_returns(40), "normal")
        r2 = backend.research_probabilistic_fit(_returns(40), "normal")
        assert r1.output == r2.output
        assert r1.result_hash == r2.result_hash

    def test_historical_deterministic(self):
        backend = PythonResearchBackend()
        r1 = backend.research_historical(_returns(50), "features")
        r2 = backend.research_historical(_returns(50), "features")
        assert r1.output == r2.output
        assert r1.result_hash == r2.result_hash

    def test_technical_deterministic(self):
        backend = PythonResearchBackend()
        bars = _bars(50)
        specs = [IndicatorSpec(name="SMA", params={"period": 5})]
        r1 = backend.research_technical(bars, specs)
        r2 = backend.research_technical(bars, specs)
        assert r1.output == r2.output
        assert r1.result_hash == r2.result_hash

    def test_econometric_deterministic(self):
        backend = PythonResearchBackend()
        r1 = backend.research_econometric_analysis(_returns(50), "arima")
        r2 = backend.research_econometric_analysis(_returns(50), "arima")
        assert r1.output == r2.output
        assert r1.result_hash == r2.result_hash


class TestParity:
    def test_cpp_backend_matches_python_reference_probability(self):
        python = PythonResearchBackend()
        cpp = ResearchCppBackend()
        samples = _returns(40)
        r_py = python.research_probabilistic_fit(samples, "normal")
        r_cpp = cpp.research_probabilistic_fit(samples, "normal")
        assert r_cpp.output == r_py.output

    def test_cpp_backend_matches_python_reference_historical(self):
        python = PythonResearchBackend()
        cpp = ResearchCppBackend()
        r_py = python.research_historical(_returns(50), "features")
        r_cpp = cpp.research_historical(_returns(50), "features")
        assert r_cpp.output == r_py.output

    def test_cpp_backend_matches_python_reference_technical(self):
        python = PythonResearchBackend()
        cpp = ResearchCppBackend()
        bars = _bars(50)
        specs = [IndicatorSpec(name="SMA", params={"period": 5})]
        r_py = python.research_technical(bars, specs)
        r_cpp = cpp.research_technical(bars, specs)
        assert r_cpp.output == r_py.output

    def test_cpp_backend_matches_core_ops(self):
        cpp = ResearchCppBackend()
        prices = [100.0, 101.0, 102.0, 101.5, 103.0]
        ret = cpp.calculate_returns(prices)
        assert len(ret) == len(prices) - 1


class TestEdgeCases:
    def test_unknown_distribution_raises(self):
        backend = PythonResearchBackend()
        with pytest.raises(ValueError):
            backend.research_probabilistic_fit(_returns(40), "weibull")

    def test_unknown_hypothesis_test_raises(self):
        backend = PythonResearchBackend()
        with pytest.raises(ValueError):
            backend.research_probabilistic_hypothesis(_returns(40), "mann_whitney")

    def test_unknown_historical_metric_raises(self):
        backend = PythonResearchBackend()
        with pytest.raises(ValueError):
            backend.research_historical(_returns(40), "nonexistent")

    def test_unknown_econometric_model_raises(self):
        backend = PythonResearchBackend()
        with pytest.raises(ValueError):
            backend.research_econometric_analysis(_returns(40), "bayesian_var")

    def test_historical_empty_raises(self):
        backend = PythonResearchBackend()
        with pytest.raises(ValueError):
            backend.research_historical([], "features")


class TestNaNInfHandling:
    def test_nan_in_probability_is_deterministic(self):
        # NaN is canonicalized deterministically (stable_float) rather than
        # rejected — identical inputs still produce identical hashes.
        backend = PythonResearchBackend()
        bad = _returns(40)
        bad.append(float("nan"))
        r1 = backend.research_probabilistic_fit(bad, "normal")
        r2 = backend.research_probabilistic_fit(bad, "normal")
        assert r1.output == r2.output
        assert r1.result_hash == r2.result_hash

    def test_inf_in_historical_is_deterministic(self):
        backend = PythonResearchBackend()
        bad = _returns(40)
        bad.append(float("inf"))
        r1 = backend.research_historical(bad, "features")
        r2 = backend.research_historical(bad, "features")
        assert r1.output == r2.output
        assert r1.result_hash == r2.result_hash


class TestProvenanceChaining:
    def test_input_hash_changes_with_params(self):
        backend = PythonResearchBackend()
        r1 = backend.research_probabilistic_fit(_returns(40), "student_t", df=5.0)
        r2 = backend.research_probabilistic_fit(_returns(40), "student_t", df=10.0)
        assert r1.input_hash != r2.input_hash
        assert r1.result_hash != r2.result_hash

    def test_result_hash_changes_with_backend(self):
        python = PythonResearchBackend()
        cpp = ResearchCppBackend()
        samples = _returns(40)
        r_py = python.research_probabilistic_fit(samples, "normal")
        r_cpp = cpp.research_probabilistic_fit(samples, "normal")
        # Same output/inputs but different backend identity -> different hash.
        assert r_cpp.output == r_py.output
        assert r_cpp.result_hash != r_py.result_hash
        assert r_cpp.backend == "ResearchCppBackend"


class TestResearchEngineFacade:
    def test_facade_wraps_backend(self):
        engine = ResearchEngine()
        result = engine.probabilistic_fit(_returns(40), "normal")
        assert isinstance(result, ResearchResult)
        assert result.backend == "PythonResearchBackend"

    def test_facade_get_version(self):
        engine = ResearchEngine()
        assert engine.get_version() == "python_research_1.0.0"

    def test_facade_capabilities(self):
        engine = ResearchEngine()
        caps = engine.capabilities()
        assert caps.deterministic is True
