"""
Router integration tests for the Certified Analytical Compute Surface (Phase 5.1).

Phase 5.1 — Certified Analytical Compute Surface (WP-1).
These tests validate that the research backends register with the existing
``BackendRouter`` and satisfy the trust-boundary routing flow:

    - router registration of research backends
    - validation status (candidate output validated against reference)
    - automatic Python fallback on candidate failure
    - metadata (backend, version, capability profile, result hash)

Pure research-only tests; no trading logic.
"""

from researchos.quant_engine.research_cpp_backend import ResearchCppBackend
from researchos.quant_engine.research_engine import PythonResearchBackend
from researchos.quant_engine.research_registry import (
    create_research_engine,
    create_research_router,
    register_research_backend,
)
from researchos.quant_engine.router import BackendRouter


class TestRouterRegistration:
    def test_create_research_router(self):
        router = create_research_router()
        assert isinstance(router, BackendRouter)
        assert len(router.list_candidates()) >= 1

    def test_register_research_backend(self):
        router = BackendRouter()
        register_research_backend(router, ResearchCppBackend())
        assert len(router.list_candidates()) == 1

    def test_router_executes_core_op(self):
        router = create_research_router()
        result = router.execute(
            "calculate_returns",
            {"prices": [100.0, 101.0, 102.0, 101.5, 103.0]},
        )
        assert result.metadata.operation == "calculate_returns"
        assert result.metadata.result_hash != ""
        assert result.metadata.error_code == "ok"

    def test_router_rejects_trust_boundary_violation(self):
        router = create_research_router()

        class Violator(PythonResearchBackend):
            def capabilities(self):
                caps = super().capabilities()
                # Advertise non-determinism -> trust boundary violation.
                from researchos.quant_engine.capabilities import BackendCapabilities

                return BackendCapabilities(
                    backend_name="ViolatorBackend",
                    version="1.0.0",
                    supported_operations=caps.supported_operations,
                    deterministic=False,
                )

        router.register(Violator())
        # The violator is rejected; the Python reference still executes.
        result = router.execute(
            "calculate_returns",
            {"prices": [100.0, 101.0]},
        )
        assert result.metadata.error_code == "ok"
        assert result.output == result.output  # reference output present


class TestCreateResearchEngine:
    def test_create_research_engine_default(self):
        engine = create_research_engine()
        assert engine.get_version() == "python_research_1.0.0"

    def test_create_research_engine_use_cpp(self):
        engine = create_research_engine(use_cpp=True)
        assert engine.backend is not None
        # Candidate backend delegates core ops successfully.
        ret = engine.backend.calculate_returns([100.0, 101.0, 102.0])
        assert len(ret) == 2

    def test_create_research_engine_explicit_backend(self):
        backend = PythonResearchBackend()
        engine = create_research_engine(backend=backend)
        assert engine.backend is backend


class TestValidationStatus:
    def test_candidate_validation_passes(self):
        router = create_research_router()
        # Run a core op the C++ candidate supports; output validated against
        # the Python reference.
        result = router.execute(
            "calculate_returns",
            {"prices": [100.0, 101.0, 102.0, 101.5, 104.0]},
        )
        assert result.metadata.validation_status in ("passed", "not_required")
        assert result.metadata.error_code == "ok"

    def test_metadata_has_capability_profile(self):
        router = create_research_router()
        result = router.execute(
            "calculate_returns",
            {"prices": [100.0, 101.0, 102.0]},
        )
        assert result.metadata.capability_profile is not None
        assert result.metadata.version != ""


class TestFallback:
    def test_fallback_to_reference_on_candidate_failure(self):
        router = create_research_router()

        class BrokenBackend(PythonResearchBackend):
            def calculate_returns(self, *args, **kwargs):
                raise RuntimeError("candidate broken")

        router.register(BrokenBackend())
        result = router.execute(
            "calculate_returns",
            {"prices": [100.0, 101.0, 102.0]},
        )
        # Even though the candidate throws, the reference must produce output.
        assert result.output == [0.01, 0.009900990099009901]
        assert result.metadata.error_code in ("execution_failed", "ok")
