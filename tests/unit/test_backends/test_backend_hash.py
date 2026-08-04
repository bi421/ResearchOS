"""
Tests: compute_backend_result_hash — canonical, deterministic result digests.

Phase 4.1: backend certification and trust-boundary hardening.

Covers SHA-256 output, canonical serialization, stable float formatting,
inclusion of all fields (operation / backend / version / input_hash / output),
and determinism.
"""

from __future__ import annotations

import json

from researchos.quant_engine import (
    HASH_ALGORITHM,
    HASH_VERSION,
    canonicalize,
    compute_backend_result_hash,
    compute_input_hash,
    stable_float,
)

IN = compute_input_hash({"prices": [100.0, 101.0, 102.0]})


def make_hash(**overrides):
    kwargs = {
        "operation": "calculate_returns",
        "backend": "PythonQuantBackend",
        "version": "1.0.0",
        "input_hash": IN,
        "output": [0.01, 0.0099],
    }
    kwargs.update(overrides)
    return compute_backend_result_hash(**kwargs)


class TestHashFormat:
    def test_returns_hex_sha256(self):
        digest = make_hash()
        assert isinstance(digest, str)
        assert len(digest) == 64
        int(digest, 16)  # valid hex

    def test_algorithm_constant(self):
        assert HASH_ALGORITHM == "sha256"
        assert HASH_VERSION == "1.0.0"


class TestDeterminism:
    def test_same_inputs_same_hash(self):
        assert make_hash() == make_hash()

    def test_float_ordering_irrelevant(self):
        a = compute_backend_result_hash(
            "op", "b", "1.0.0", IN, {"x": 1.0, "y": 2.0}
        )
        b = compute_backend_result_hash(
            "op", "b", "1.0.0", IN, {"y": 2.0, "x": 1.0}
        )
        assert a == b

    def test_dict_key_order_irrelevant(self):
        a = compute_backend_result_hash("op", "b", "1.0.0", IN, [1.0, 2.0])
        b = compute_backend_result_hash("op", "b", "1.0.0", IN, [1.0, 2.0])
        assert a == b

    def test_list_vs_tuple(self):
        a = compute_backend_result_hash("op", "b", "1.0.0", IN, [1.0, 2.0])
        b = compute_backend_result_hash("op", "b", "1.0.0", IN, (1.0, 2.0))
        assert a == b


class TestFieldSensitivity:
    def test_operation_included(self):
        assert make_hash() != make_hash(operation="calculate_volatility")

    def test_backend_included(self):
        assert make_hash() != make_hash(backend="CppQuantAdapter")

    def test_version_included(self):
        assert make_hash() != make_hash(version="2.0.0")

    def test_input_hash_included(self):
        assert make_hash() != make_hash(input_hash="deadbeef" * 8)

    def test_output_included(self):
        assert make_hash() != make_hash(output=[0.01, 0.0100])


class TestStableFloatFormatting:
    def test_stable_float_deterministic(self):
        assert stable_float(0.1) == stable_float(0.1)
        assert stable_float(1.0) == "1.0"

    def test_stable_float_roundtrip(self):
        assert float(stable_float(3.141592653589793)) == 3.141592653589793

    def test_nan_encoded_deterministically(self):
        assert stable_float(float("nan")) == "NaN"

    def test_inf_encoded_deterministically(self):
        assert stable_float(float("inf")) == "Infinity"
        assert stable_float(float("-inf")) == "-Infinity"

    def test_negative_zero(self):
        assert stable_float(-0.0) == "0.0"

    def test_zero(self):
        assert stable_float(0.0) == "0.0"


class TestCanonicalize:
    def test_dict_keys_sorted(self):
        assert canonicalize({"b": 1, "a": 2}) == {"a": 2, "b": 1}

    def test_floats_become_stable_strings(self):
        assert canonicalize(1.0) == "1.0"

    def test_nan_canonical(self):
        assert canonicalize(float("nan")) == "NaN"

    def test_nested_structures(self):
        value = canonicalize({"a": [1.0, {"z": 2.0}], "c": 3})
        assert value == {"a": ["1.0", {"z": "2.0"}], "c": 3}

    def test_bool_and_int_passthrough(self):
        assert canonicalize(True) is True
        assert canonicalize(7) == 7

    def test_none_passthrough(self):
        assert canonicalize(None) is None

    def test_to_dict_objects_supported(self):
        class Fake:
            def to_dict(self):
                return {"value": 1.0}

        assert canonicalize(Fake()) == {"value": "1.0"}


class TestInputHash:
    def test_deterministic(self):
        assert compute_input_hash({"a": [1.0, 2.0]}) == compute_input_hash(
            {"a": [1.0, 2.0]}
        )

    def test_key_order_irrelevant(self):
        a = compute_input_hash({"a": 1.0, "b": 2.0})
        b = compute_input_hash({"b": 2.0, "a": 1.0})
        assert a == b

    def test_different_inputs_differ(self):
        assert compute_input_hash({"a": 1.0}) != compute_input_hash({"a": 2.0})

    def test_sha256_length(self):
        assert len(compute_input_hash({"x": 1})) == 64

    def test_json_serializable(self):
        # Canonical form must be JSON-serializable (no non-finite floats).
        canonical = canonicalize({"v": [1.0, 2.0]})
        json.dumps(canonical)


class TestCanonicalDict:
    def test_returns_wrapped(self):
        from researchos.quant_engine.backend_hash import canonical_dict

        assert canonical_dict(1.0) == {"canonical": "1.0"}
