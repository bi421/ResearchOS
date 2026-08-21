"""
Tests for Phase 5.3c Step 1 — Deterministic Contract Resolvers.

Covers:
    - ``SimulationConfig`` deterministic round-trip (to_dict → from_dict → to_dict).
    - ``DatasetConfig`` deterministic round-trip.
    - ``ResearchDataset.from_payload`` reconstruction from a dataset evidence
      payload (feature_names, features, labels, metadata, label_name, version).
    - Invalid payload rejection (missing keys, bad dims, non-mapping).
    - Deterministic hash preservation (origin dataset and reconstructed dataset
      have identical identity when re-emitted).
    - Backward compatibility with existing snapshots.

Verification requirements:
    - round trip is exact and deterministic
    - from_dict is backward compatible (missing keys → defaults)
    - payload reconstruction preserves all content and does not mutate input
    - deterministic hash preservation
"""

from __future__ import annotations

import copy

import pytest

from researchos.evidence.dataset_emission import (
    build_dataset_envelope,
    research_dataset_payload,
)
from researchos.experiments.contracts import DatasetConfig, SimulationConfig
from researchos.quant_engine.machine_learning.dataset_contracts import (
    ResearchDataset,
)

# =============================================================================
# SimulationConfig round-trip
# =============================================================================


class TestSimulationConfigRoundTrip:
    def test_round_trip_identity(self):
        config = SimulationConfig(
            seed=7,
            initial_capital=250_000.0,
            commission="pct:0.001",
            slippage="fixed:0.0005",
            max_positions=5,
            parameters={"mode": "monte_carlo", "paths": 1000},
        )
        restored = SimulationConfig.from_dict(config.to_dict())
        assert restored.to_dict() == config.to_dict()

    def test_round_trip_is_deterministic(self):
        config = SimulationConfig(seed=1, parameters={"a": 1})
        d1 = SimulationConfig.from_dict(config.to_dict()).to_dict()
        d2 = SimulationConfig.from_dict(config.to_dict()).to_dict()
        assert d1 == d2

    def test_default_config_round_trip(self):
        config = SimulationConfig()
        restored = SimulationConfig.from_dict(config.to_dict())
        assert restored.to_dict() == config.to_dict()

    def test_empty_parameters_round_trip(self):
        config = SimulationConfig(seed=42, parameters={})
        assert SimulationConfig.from_dict(config.to_dict()).to_dict() == config.to_dict()


# =============================================================================
# DatasetConfig round-trip
# =============================================================================


class TestDatasetConfigRoundTrip:
    def test_round_trip_identity(self):
        config = DatasetConfig(
            source="yahoo",
            start_date="2020-01-01",
            end_date="2021-01-01",
            symbols=["AAPL", "MSFT", "GOOG"],
            resolution="1d",
            filters=["market_hours", "liquid"],
            parameters={"adjust": "split"},
        )
        restored = DatasetConfig.from_dict(config.to_dict())
        assert restored.to_dict() == config.to_dict()

    def test_round_trip_sorts_lists_deterministically(self):
        config = DatasetConfig(
            source="s",
            symbols=["b", "a", "c"],
            filters=["z", "y"],
        )
        d = config.to_dict()
        assert d["symbols"] == ["a", "b", "c"]
        assert d["filters"] == ["y", "z"]
        restored = DatasetConfig.from_dict(d).to_dict()
        assert restored == d

    def test_backward_compatible_minimal(self):
        # A legacy snapshot that predates optional fields must still load.
        legacy = {"source": "yahoo"}
        config = DatasetConfig.from_dict(legacy)
        assert config.source == "yahoo"
        assert config.symbols == []
        assert config.resolution == "1d"
        assert config.parameters == {}

    def test_empty_config_round_trip(self):
        config = DatasetConfig(source="x")
        assert DatasetConfig.from_dict(config.to_dict()).to_dict() == config.to_dict()


# =============================================================================
# ResearchDataset.from_payload
# =============================================================================


class TestResearchDatasetFromPayload:
    def _make_dataset(self):
        return ResearchDataset(
            feature_names=("a", "b", "c"),
            features=(
                (1.0, 2.0, 3.0),
                (4.0, 5.0, 6.0),
            ),
            labels=(0.0, 1.0),
            metadata={"source": "yahoo", "periods": 2},
            sample_count=2,
            feature_count=3,
            label_name="target",
            version="1.0.0",
        )

    def test_reconstructs_all_fields(self):
        ds = self._make_dataset()
        payload = research_dataset_payload(ds)
        restored = ResearchDataset.from_payload(payload)
        assert restored.feature_names == ds.feature_names
        assert restored.features == ds.features
        assert restored.labels == ds.labels
        assert dict(restored.metadata) == dict(ds.metadata)
        assert restored.label_name == ds.label_name
        assert restored.version == ds.version
        assert restored.sample_count == ds.sample_count
        assert restored.feature_count == ds.feature_count

    def test_does_not_mutate_input_payload(self):
        ds = self._make_dataset()
        payload = research_dataset_payload(ds)
        snapshot = copy.deepcopy(payload)
        ResearchDataset.from_payload(payload)
        assert payload == snapshot

    def test_deterministic_hash_preservation(self):
        ds = self._make_dataset()
        payload = research_dataset_payload(ds)
        restored = ResearchDataset.from_payload(payload)
        e1 = build_dataset_envelope(ds, version="1.0.0")
        e2 = build_dataset_envelope(restored, version="1.0.0")
        assert e1.artifact_hash == e2.artifact_hash

    def test_empty_dataset_round_trip(self):
        ds = ResearchDataset(
            feature_names=(),
            features=(),
            labels=(),
            metadata={},
            sample_count=0,
            feature_count=0,
            label_name="t",
            version="1.0.0",
        )
        payload = research_dataset_payload(ds)
        restored = ResearchDataset.from_payload(payload)
        assert restored.feature_names == ()
        assert restored.labels == ()
        assert restored.sample_count == 0


# =============================================================================
# Invalid payload rejection
# =============================================================================


class TestResearchDatasetInvalidPayload:
    def test_rejects_non_mapping(self):
        with pytest.raises(TypeError):
            ResearchDataset.from_payload(["not", "a", "mapping"])  # type: ignore[arg-type]

    def test_rejects_missing_required_key(self):
        payload = {
            "feature_names": ["a"],
            "features": [[1.0]],
            "labels": [0.0],
        }
        with pytest.raises(ValueError):
            ResearchDataset.from_payload(payload)

    def test_rejects_sample_count_mismatch(self):
        payload = {
            "feature_names": ["a"],
            "features": [[1.0], [2.0]],
            "labels": [0.0, 1.0],
            "metadata": {},
            "sample_count": 99,  # mismatch
            "feature_count": 1,
            "label_name": "t",
            "version": "1.0.0",
        }
        with pytest.raises(ValueError):
            ResearchDataset.from_payload(payload)

    def test_rejects_feature_count_mismatch(self):
        payload = {
            "feature_names": ["a"],
            "features": [[1.0]],
            "labels": [0.0],
            "metadata": {},
            "sample_count": 1,
            "feature_count": 5,  # mismatch
            "label_name": "t",
            "version": "1.0.0",
        }
        with pytest.raises(ValueError):
            ResearchDataset.from_payload(payload)

    def test_rejects_inconsistent_feature_widths(self):
        payload = {
            "feature_names": ["a", "b"],
            "features": [[1.0, 2.0], [3.0]],  # second row wrong width
            "labels": [0.0, 1.0],
            "metadata": {},
            "sample_count": 2,
            "feature_count": 2,
            "label_name": "t",
            "version": "1.0.0",
        }
        with pytest.raises(ValueError):
            ResearchDataset.from_payload(payload)


# =============================================================================
# Acceptance tracking
# =============================================================================


class TestAcceptanceCriteria:
    def test_acceptance_simulation_round_trip(self):
        config = SimulationConfig(seed=5, initial_capital=1_000.0, parameters={"x": 2})
        assert SimulationConfig.from_dict(config.to_dict()).to_dict() == config.to_dict()

    def test_acceptance_dataset_config_round_trip(self):
        config = DatasetConfig(source="s", symbols=["q", "r"])
        assert DatasetConfig.from_dict(config.to_dict()).to_dict() == config.to_dict()

    def test_acceptance_payload_round_trip(self):
        ds = ResearchDataset(
            feature_names=("a",),
            features=((1.0,), (2.0,)),
            labels=(0.0, 1.0),
            metadata={"k": "v"},
            sample_count=2,
            feature_count=1,
            label_name="t",
            version="1.5.0",
        )
        restored = ResearchDataset.from_payload(research_dataset_payload(ds))
        assert restored.feature_names == ds.feature_names
        assert restored.features == ds.features
        assert restored.labels == ds.labels
        assert dict(restored.metadata) == dict(ds.metadata)
        assert restored.label_name == ds.label_name
        assert restored.version == ds.version

    def test_acceptance_invalid_payload_rejected(self):
        with pytest.raises(ValueError):
            ResearchDataset.from_payload({"feature_names": []})

    def test_acceptance_deterministic_hash_preserved(self):
        ds = ResearchDataset(
            feature_names=("a",),
            features=((1.0,),),
            labels=(0.0,),
            metadata={},
            sample_count=1,
            feature_count=1,
            label_name="t",
            version="1.0.0",
        )
        restored = ResearchDataset.from_payload(research_dataset_payload(ds))
        assert build_dataset_envelope(ds).artifact_hash == build_dataset_envelope(restored).artifact_hash

    def test_acceptance_backward_compatible_snapshots(self):
        # A legacy SimulationConfig snapshot with only seed present.
        sc = SimulationConfig.from_dict({"seed": 9})
        assert sc.seed == 9
        assert sc.initial_capital == 100_000.0
        assert sc.max_positions == 10
        # A legacy DatasetConfig snapshot with only source present.
        dc = DatasetConfig.from_dict({"source": "legacy"})
        assert dc.source == "legacy"
        assert dc.symbols == []
        assert dc.resolution == "1d"
