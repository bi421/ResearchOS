"""
Tests: BackendCapabilities — immutable certification contract.

Phase 4.1: backend certification and trust-boundary hardening.
"""

from __future__ import annotations

import pytest

from researchos.quant_engine import (
    QUANT_OPERATIONS,
    REFERENCE_BACKEND_NAME,
    REFERENCE_BACKEND_VERSION,
    BackendCapabilities,
    BackendCapabilitiesError,
    PythonQuantBackend,
    default_capabilities,
)


def make_caps(**kwargs) -> BackendCapabilities:
    defaults = dict(
        backend_name="TestBackend",
        version="1.0.0",
        supported_operations=("calculate_returns",),
    )
    defaults.update(kwargs)
    return BackendCapabilities(**defaults)


class TestBackendCapabilitiesConstruction:
    def test_constructs_with_required_fields(self):
        caps = make_caps()
        assert caps.backend_name == "TestBackend"
        assert caps.version == "1.0.0"
        assert caps.supported_operations == ("calculate_returns",)

    def test_default_guarantees_all_true(self):
        caps = make_caps()
        assert caps.deterministic is True
        assert caps.stateless is True
        assert caps.no_timestamps is True
        assert caps.no_randomness is True
        assert caps.explicit_typing is True

    def test_explicit_guarantees(self):
        caps = make_caps(deterministic=False, explicit_typing=False)
        assert caps.deterministic is False
        assert caps.explicit_typing is False

    def test_empty_backend_name_raises(self):
        with pytest.raises(BackendCapabilitiesError):
            make_caps(backend_name="")

    def test_blank_backend_name_raises(self):
        with pytest.raises(BackendCapabilitiesError):
            make_caps(backend_name="   ")

    def test_empty_version_raises(self):
        with pytest.raises(BackendCapabilitiesError):
            make_caps(version="")

    def test_bad_supported_operations_raises(self):
        with pytest.raises(BackendCapabilitiesError):
            make_caps(supported_operations="calculate_returns")


class TestBackendCapabilitiesImmutability:
    def test_is_frozen(self):
        caps = make_caps()
        with pytest.raises(Exception):
            caps.backend_name = "Mutated"  # type: ignore[misc]

    def test_supported_operations_frozen_tuple(self):
        caps = make_caps(supported_operations=["a", "b"])
        assert isinstance(caps.supported_operations, tuple)

    def test_is_hashable(self):
        a = make_caps()
        b = make_caps()
        assert hash(a) == hash(b)
        assert len({a, b, make_caps(backend_name="Other")}) == 2


class TestBackendCapabilitiesBehavior:
    def test_supports_true(self):
        caps = make_caps(supported_operations=("calculate_returns", "run_simulation"))
        assert caps.supports("calculate_returns") is True
        assert caps.supports("run_simulation") is True

    def test_supports_false(self):
        caps = make_caps(supported_operations=("calculate_returns",))
        assert caps.supports("calculate_volatility") is False

    def test_quanta_operations_are_complete(self):
        assert "calculate_returns" in QUANT_OPERATIONS
        assert "run_simulation" in QUANT_OPERATIONS
        assert len(QUANT_OPERATIONS) >= 6

    def test_reference_constants(self):
        assert REFERENCE_BACKEND_NAME == "PythonQuantBackend"
        assert REFERENCE_BACKEND_VERSION == "1.0.0"


class TestBackendCapabilitiesSerialization:
    def test_roundtrip(self):
        caps = make_caps(
            supported_operations=("a", "b"),
            deterministic=False,
            stateless=False,
        )
        restored = BackendCapabilities.from_dict(caps.to_dict())
        assert restored == caps

    def test_to_dict_is_json_compatible(self):
        import json

        data = make_caps().to_dict()
        json.dumps(data)
        assert set(data.keys()) == {
            "backend_name",
            "version",
            "supported_operations",
            "deterministic",
            "stateless",
            "no_timestamps",
            "no_randomness",
            "explicit_typing",
        }

    def test_to_dict_deterministic(self):
        caps = make_caps(supported_operations=("b", "a"))
        assert caps.to_dict() == caps.to_dict()


class TestDefaultCapabilities:
    def test_default_for_python_backend(self):
        caps = default_capabilities(PythonQuantBackend())
        assert caps.backend_name == "PythonQuantBackend"
        # default_capabilities derives version from get_version(); PythonQuantBackend
        # keeps the interface default (class name) for compatibility with the
        # existing parity tests that assert "PythonQuantBackend".
        assert caps.version == "PythonQuantBackend"
        assert caps.supports("calculate_returns") is True

    def test_default_guarantees(self):
        caps = default_capabilities(PythonQuantBackend())
        assert caps.deterministic and caps.stateless
        assert caps.no_timestamps and caps.no_randomness and caps.explicit_typing

    def test_interface_default_capabilities(self):
        backend = PythonQuantBackend()
        caps = backend.capabilities()
        assert isinstance(caps, BackendCapabilities)
        assert caps.backend_name == REFERENCE_BACKEND_NAME
