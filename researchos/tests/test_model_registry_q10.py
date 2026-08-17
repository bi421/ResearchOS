"""
Tests: Model Registry (Q10).

The registry stores immutable model identity contracts and supports a
deterministic lifecycle (register / get / list / remove / clear).  It never
trains models and never executes trading.

All tests verify:
    * immutability of registered contracts
    * deterministic ordering of ``list_models()``
    * error handling for duplicate / unknown model ids
    * matching inputs produce identical outputs (determinism)
"""

from __future__ import annotations

import unittest

from researchos.quant_engine.models import (
    MODEL_CONTRACT_VERSION,
    MODEL_REGISTRY_VERSION,
    ModelAlreadyExistsError,
    ModelContract,
    ModelContractError,
    ModelMetadata,
    ModelNotFoundError,
    ModelRegistry,
    ModelRegistryError,
    SimulationRequest,
)


def _make_contract(model_id: str = "xauusd_direction_v1") -> ModelContract:
    return ModelContract(
        model_id=model_id,
        name="XAUUSD Direction",
        version="1.0.0",
        algorithm="random_forest",
        feature_names=("returns_1", "returns_5", "rsi_14"),
        label_name="direction",
        dataset_hash="abc123",
        validation_hash="def456",
        parameters={"n_estimators": 100, "max_depth": 4},
        created_at="2024-01-01T00:00:00Z",
        metadata={"framework": "sklearn", "author": "test"},
    )


class TestModelContract(unittest.TestCase):
    def test_constructs_with_required_fields(self):
        c = _make_contract()
        self.assertEqual(c.model_id, "xauusd_direction_v1")
        self.assertEqual(c.version, "1.0.0")
        self.assertEqual(tuple(c.feature_names), ("returns_1", "returns_5", "rsi_14"))
        self.assertEqual(c.metadata["framework"], "sklearn")

    def test_is_immutable_dataclass(self):
        c = _make_contract()
        with self.assertRaises(Exception):
            c.name = "Mutated"  # type: ignore[misc]
        with self.assertRaises(Exception):
            c.parameters["n_estimators"] = 999  # mappingproxy is read-only

    def test_params_metadata_are_proxies(self):
        c = _make_contract()
        # mappingproxy satisfies the collections.abc.Mapping contract.
        from collections.abc import Mapping as _Mapping

        self.assertIsInstance(c.parameters, _Mapping)
        self.assertIsInstance(c.metadata, _Mapping)
        with self.assertRaises(TypeError):
            c.parameters["new"] = 1  # type: ignore[index]
        with self.assertRaises(TypeError):
            c.metadata["new"] = 1  # type: ignore[index]
        # They are immutable: item assignment fails (no __setitem__).
        self.assertFalse(hasattr(c.parameters, "__setitem__"))
        self.assertFalse(hasattr(c.metadata, "__setitem__"))

    def test_hashable_and_equality(self):
        a = _make_contract()
        b = _make_contract()
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertEqual(len({a, b}), 1)

    def test_to_dict_roundtrip(self):
        a = _make_contract()
        b = ModelContract.from_dict(a.to_dict())
        self.assertEqual(a, b)

    def test_invalid_model_id(self):
        with self.assertRaises(ModelContractError):
            ModelContract(
                model_id="bad id!",
                name="x",
                version="1.0.0",
                algorithm="x",
                feature_names=(),
                label_name="y",
                dataset_hash="dh",
                validation_hash="vh",
            )

    def test_invalid_version(self):
        with self.assertRaises(ModelContractError):
            ModelContract(
                model_id="ok_id",
                name="x",
                version="not-semver",
                algorithm="x",
                feature_names=(),
                label_name="y",
                dataset_hash="dh",
                validation_hash="vh",
            )

    def test_metadata_from_model_metadata(self):
        md = ModelMetadata(author="test", framework="xgboost", tags=("a", "b"))
        c = ModelContract(
            model_id="m1",
            name="x",
            version="1.0.0",
            algorithm="x",
            feature_names=(),
            label_name="y",
            dataset_hash="dh",
            validation_hash="vh",
            metadata=md,
        )
        self.assertEqual(c.metadata["framework"], "xgboost")
        self.assertEqual(tuple(c.metadata["tags"]), ("a", "b"))


class TestModelRegistry(unittest.TestCase):
    def test_register_and_get(self):
        r = ModelRegistry()
        r.register(_make_contract("a"))
        got = r.get("a")
        self.assertEqual(got.model_id, "a")
        self.assertEqual(r.count(), 1)

    def test_duplicate_raises(self):
        r = ModelRegistry()
        r.register(_make_contract("same"))
        with self.assertRaises(ModelAlreadyExistsError):
            r.register(_make_contract("same"))

    def test_get_missing_raises(self):
        r = ModelRegistry()
        with self.assertRaises(ModelNotFoundError):
            r.get("nope")

    def test_remove(self):
        r = ModelRegistry()
        r.register(_make_contract("a"))
        r.remove("a")
        self.assertFalse(r.exists("a"))
        self.assertEqual(r.count(), 0)

    def test_remove_missing_raises(self):
        r = ModelRegistry()
        with self.assertRaises(ModelNotFoundError):
            r.remove("nope")

    def test_clear(self):
        r = ModelRegistry()
        r.register(_make_contract("a"))
        r.register(_make_contract("b"))
        r.clear()
        self.assertEqual(r.count(), 0)

    def test_list_models_deterministic_order(self):
        r = ModelRegistry()
        r.register(_make_contract("zebra"))
        r.register(_make_contract("alpha"))
        r.register(_make_contract("middle"))
        ids = [c.model_id for c in r.list_models()]
        self.assertEqual(ids, sorted(ids))

    def test_list_models_repeatable(self):
        r = ModelRegistry()
        r.register(_make_contract("zebra"))
        r.register(_make_contract("alpha"))
        r.register(_make_contract("middle"))
        self.assertEqual(r.list_models(), r.list_models())

    def test_rejects_non_contract(self):
        r = ModelRegistry()
        with self.assertRaises(TypeError):
            r.register("not a contract")  # type: ignore[arg-type]

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(ModelAlreadyExistsError, ModelRegistryError))
        self.assertTrue(issubclass(ModelNotFoundError, ModelRegistryError))

    def test_to_dict_roundtrip(self):
        r = ModelRegistry()
        r.register(_make_contract("a"))
        r.register(_make_contract("b"))
        r2 = ModelRegistry.from_dict(r.to_dict())
        self.assertEqual(r.list_models(), r2.list_models())


class TestBackwardCompatibility(unittest.TestCase):
    def test_legacy_simulation_request_reexported(self):
        # Existing callers do ``from researchos.quant_engine.models import SimulationRequest``
        self.assertTrue(callable(SimulationRequest))

    def test_contract_version(self):
        self.assertEqual(MODEL_CONTRACT_VERSION, "1.0.0")

    def test_registry_version(self):
        self.assertEqual(MODEL_REGISTRY_VERSION, "1.0.0")


if __name__ == "__main__":
    unittest.main()
