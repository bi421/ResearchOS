"""
Phase 7.1 — DecisionContext tests.

Covers:
    - Basic creation with all reference types
    - Serialization (to_dict / from_dict round-trip)
    - Hash stability (deterministic hashing)
    - Deterministic ID generation
    - Reference management (add_* helpers)
    - DecisionContextValidator rules
    - Empty context
    - Large context (many references)
    - Duplicate detection
    - Empty ID rejection
    - Optional references (reasoning_chain_id, audit_entry_id)
    - Lifecycle tracking
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from researchos.decision_engine.context import (
    DecisionContext,
    DecisionContextValidator,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_timestamp() -> datetime:
    """Fixed timestamp for deterministic tests."""
    return datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_context(sample_timestamp: datetime) -> DecisionContext:
    """Create a fully populated DecisionContext with all references."""
    return DecisionContext(
        asset="XAUUSD",
        market_snapshot_id="snap_abc123",
        market_regime_id="regime_def456",
        macro_state_id="macro_ghi789",
        historical_scenario_ids=["hist_001", "hist_002", "hist_003"],
        experiment_result_ids=["exp_001", "exp_002"],
        validation_ids=["val_001"],
        research_ids=["res_001", "res_002"],
        market_memory_report_ids=["mmr_001"],
        simulation_result_ids=["sim_001", "sim_002"],
        reasoning_chain_id="chain_001",
        audit_entry_id="audit_001",
        symbol="XAU",
        timeframe="1h",
        decision_timestamp=sample_timestamp,
        dataset_version="DATASET_V2",
        calculation_version="DECISION_V2",
        context_version="CONTEXT_V2",
        ontology_tags=["gold", "forex", "decision_engine"],
    )


@pytest.fixture
def empty_context(sample_timestamp: datetime) -> DecisionContext:
    """Create a minimal DecisionContext with minimal references."""
    return DecisionContext(
        asset="BTCUSD",
        decision_timestamp=sample_timestamp,
    )


@pytest.fixture
def validator() -> DecisionContextValidator:
    return DecisionContextValidator()


# =============================================================================
# Basic Creation
# =============================================================================


class TestDecisionContextCreation:
    """Tests for basic DecisionContext creation."""

    def test_creation_with_all_references(self, sample_context: DecisionContext):
        """Verify a fully populated context has all fields set correctly."""
        ctx = sample_context
        assert ctx.asset == "XAUUSD"
        assert ctx.market_snapshot_id == "snap_abc123"
        assert ctx.market_regime_id == "regime_def456"
        assert ctx.macro_state_id == "macro_ghi789"
        assert ctx.historical_scenario_ids == ["hist_001", "hist_002", "hist_003"]
        assert ctx.experiment_result_ids == ["exp_001", "exp_002"]
        assert ctx.validation_ids == ["val_001"]
        assert ctx.research_ids == ["res_001", "res_002"]
        assert ctx.market_memory_report_ids == ["mmr_001"]
        assert ctx.simulation_result_ids == ["sim_001", "sim_002"]
        assert ctx.reasoning_chain_id == "chain_001"
        assert ctx.audit_entry_id == "audit_001"
        assert ctx.symbol == "XAU"
        assert ctx.timeframe == "1h"
        assert ctx.dataset_version == "DATASET_V2"
        assert ctx.calculation_version == "DECISION_V2"
        assert ctx.context_version == "CONTEXT_V2"
        assert ctx.ontology_tags == ["gold", "forex", "decision_engine"]

    def test_creation_with_minimal_references(self, empty_context: DecisionContext):
        """Verify a minimal context defaults correctly."""
        ctx = empty_context
        assert ctx.asset == "BTCUSD"
        assert ctx.market_snapshot_id == ""
        assert ctx.market_regime_id == ""
        assert ctx.macro_state_id == ""
        assert ctx.historical_scenario_ids == []
        assert ctx.experiment_result_ids == []
        assert ctx.validation_ids == []
        assert ctx.research_ids == []
        assert ctx.market_memory_report_ids == []
        assert ctx.simulation_result_ids == []
        assert ctx.reasoning_chain_id == ""
        assert ctx.audit_entry_id == ""
        assert ctx.symbol == ""
        assert ctx.timeframe == ""
        assert ctx.dataset_version == "DATASET_V1"
        assert ctx.calculation_version == "DECISION_V1"
        assert ctx.context_version == "CONTEXT_V1"

    def test_creation_with_optional_references(self, sample_timestamp: datetime):
        """Verify optional references can be left empty."""
        ctx = DecisionContext(
            asset="EURUSD",
            decision_timestamp=sample_timestamp,
            reasoning_chain_id="chain_xyz",
        )
        assert ctx.reasoning_chain_id == "chain_xyz"
        assert ctx.audit_entry_id == ""

    def test_creation_has_id(self, sample_context: DecisionContext):
        """Verify context has a deterministic ID."""
        assert sample_context.id is not None
        assert len(sample_context.id) > 0

    def test_creation_has_lifecycle(self, sample_context: DecisionContext):
        """Verify context has lifecycle tracking."""
        assert sample_context.lifecycle is not None
        assert sample_context.lifecycle.current_stage.value == "Created"


# =============================================================================
# Deterministic ID Generation
# =============================================================================


class TestDeterministicIds:
    """Tests for deterministic ID generation."""

    def test_same_inputs_same_id(self, sample_timestamp: datetime):
        """Two contexts with identical inputs must have the same ID."""
        ctx1 = DecisionContext(asset="XAUUSD", timeframe="1h", decision_timestamp=sample_timestamp)
        ctx2 = DecisionContext(asset="XAUUSD", timeframe="1h", decision_timestamp=sample_timestamp)
        assert ctx1.id == ctx2.id

    def test_different_asset_different_id(self, sample_timestamp: datetime):
        """Different asset must produce different IDs."""
        ctx1 = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp)
        ctx2 = DecisionContext(asset="BTCUSD", decision_timestamp=sample_timestamp)
        assert ctx1.id != ctx2.id

    def test_different_timestamp_different_id(self):
        """Different timestamps must produce different IDs."""
        ts1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
        ts2 = datetime(2025, 6, 15, tzinfo=timezone.utc)
        ctx1 = DecisionContext(asset="XAUUSD", decision_timestamp=ts1)
        ctx2 = DecisionContext(asset="XAUUSD", decision_timestamp=ts2)
        assert ctx1.id != ctx2.id

    def test_different_timeframe_different_id(self, sample_timestamp: datetime):
        """Different timeframes must produce different IDs."""
        ctx1 = DecisionContext(asset="XAUUSD", timeframe="1h", decision_timestamp=sample_timestamp)
        ctx2 = DecisionContext(asset="XAUUSD", timeframe="4h", decision_timestamp=sample_timestamp)
        assert ctx1.id != ctx2.id


# =============================================================================
# Serialization (to_dict / from_dict Round-Trip)
# =============================================================================


class TestSerialization:
    """Tests for to_dict / from_dict serialization."""

    def test_to_dict_contains_all_fields(self, sample_context: DecisionContext):
        """Verify all fields appear in to_dict output."""
        d = sample_context.to_dict()
        assert d["asset"] == "XAUUSD"
        assert d["market_snapshot_id"] == "snap_abc123"
        assert d["market_regime_id"] == "regime_def456"
        assert d["macro_state_id"] == "macro_ghi789"
        assert d["historical_scenario_ids"] == ["hist_001", "hist_002", "hist_003"]
        assert d["experiment_result_ids"] == ["exp_001", "exp_002"]
        assert d["validation_ids"] == ["val_001"]
        assert d["research_ids"] == ["res_001", "res_002"]
        assert d["market_memory_report_ids"] == ["mmr_001"]
        assert d["simulation_result_ids"] == ["sim_001", "sim_002"]
        assert d["reasoning_chain_id"] == "chain_001"
        assert d["audit_entry_id"] == "audit_001"
        assert d["symbol"] == "XAU"
        assert d["timeframe"] == "1h"
        assert d["dataset_version"] == "DATASET_V2"
        assert d["calculation_version"] == "DECISION_V2"
        assert d["context_version"] == "CONTEXT_V2"
        assert d["object_type"] == "DecisionContext"

    def test_round_trip(self, sample_context: DecisionContext):
        d = sample_context.to_dict()
        restored = DecisionContext.from_dict(d)
        assert restored.id == sample_context.id
        assert restored.asset == sample_context.asset
        assert restored.market_snapshot_id == sample_context.market_snapshot_id
        assert restored.market_regime_id == sample_context.market_regime_id
        assert restored.macro_state_id == sample_context.macro_state_id
        assert restored.historical_scenario_ids == sample_context.historical_scenario_ids
        assert restored.experiment_result_ids == sample_context.experiment_result_ids
        assert restored.validation_ids == sample_context.validation_ids
        assert restored.research_ids == sample_context.research_ids
        assert restored.market_memory_report_ids == sample_context.market_memory_report_ids
        assert restored.simulation_result_ids == sample_context.simulation_result_ids
        assert restored.reasoning_chain_id == sample_context.reasoning_chain_id
        assert restored.audit_entry_id == sample_context.audit_entry_id
        assert restored.symbol == sample_context.symbol
        assert restored.timeframe == sample_context.timeframe
        assert restored.dataset_version == sample_context.dataset_version
        assert restored.calculation_version == sample_context.calculation_version
        assert restored.context_version == sample_context.context_version
        assert restored.decision_timestamp == sample_context.decision_timestamp

    def test_round_trip_empty(self, empty_context: DecisionContext):
        d = empty_context.to_dict()
        restored = DecisionContext.from_dict(d)
        assert restored.id == empty_context.id
        assert restored.asset == "BTCUSD"
        assert restored.historical_scenario_ids == []

    def test_round_trip_optional_fields(self, sample_timestamp: datetime):
        ctx = DecisionContext(
            asset="EURUSD",
            decision_timestamp=sample_timestamp,
            reasoning_chain_id="chain_xyz",
            audit_entry_id="audit_xyz",
        )
        d = ctx.to_dict()
        restored = DecisionContext.from_dict(d)
        assert restored.reasoning_chain_id == "chain_xyz"
        assert restored.audit_entry_id == "audit_xyz"

    def test_json_serializable(self, sample_context: DecisionContext):
        d = sample_context.to_dict()
        json_str = json.dumps(d, indent=2, sort_keys=True, default=str)
        parsed = json.loads(json_str)
        assert parsed["asset"] == "XAUUSD"
        assert parsed["id"] == sample_context.id

    def test_round_trip_preserves_base_fields(self, sample_context: DecisionContext):
        d = sample_context.to_dict()
        restored = DecisionContext.from_dict(d)
        assert restored.id == sample_context.id
        assert restored.lifecycle.current_stage == sample_context.lifecycle.current_stage
        assert restored.compute_hash() == sample_context.compute_hash()


# =============================================================================
# Deterministic Hashing
# =============================================================================


class TestHashStability:
    """Tests for deterministic hash stability."""

    def test_same_context_same_hash(self, sample_timestamp: datetime):
        ctx1 = DecisionContext(asset="XAUUSD", timeframe="1h", decision_timestamp=sample_timestamp)
        ctx2 = DecisionContext(asset="XAUUSD", timeframe="1h", decision_timestamp=sample_timestamp)
        assert ctx1.compute_hash() == ctx2.compute_hash()

    def test_different_asset_different_hash(self, sample_timestamp: datetime):
        ctx1 = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp)
        ctx2 = DecisionContext(asset="BTCUSD", decision_timestamp=sample_timestamp)
        assert ctx1.compute_hash() != ctx2.compute_hash()

    def test_different_references_different_hash(self, sample_timestamp: datetime):
        ctx1 = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp, market_snapshot_id="snap_a")
        ctx2 = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp, market_snapshot_id="snap_b")
        assert ctx1.compute_hash() != ctx2.compute_hash()

    def test_hash_stable_across_serialization(self, sample_context: DecisionContext):
        original_hash = sample_context.compute_hash()
        d = sample_context.to_dict()
        restored = DecisionContext.from_dict(d)
        assert restored.compute_hash() == original_hash

    def test_hash_stable_over_time(self, sample_context: DecisionContext):
        h1 = sample_context.compute_hash()
        h2 = sample_context.compute_hash()
        h3 = sample_context.compute_hash()
        assert h1 == h2 == h3


# =============================================================================
# Reference Management
# =============================================================================


class TestReferenceManagement:
    """Tests for the add_* reference management helpers."""

    def test_add_historical_scenario(self, empty_context: DecisionContext):
        empty_context.add_historical_scenario("hist_099")
        assert "hist_099" in empty_context.historical_scenario_ids

    def test_add_experiment_result(self, empty_context: DecisionContext):
        empty_context.add_experiment_result("exp_099")
        assert "exp_099" in empty_context.experiment_result_ids

    def test_add_validation(self, empty_context: DecisionContext):
        empty_context.add_validation("val_099")
        assert "val_099" in empty_context.validation_ids

    def test_add_research(self, empty_context: DecisionContext):
        empty_context.add_research("res_099")
        assert "res_099" in empty_context.research_ids

    def test_add_market_memory_report(self, empty_context: DecisionContext):
        empty_context.add_market_memory_report("mmr_099")
        assert "mmr_099" in empty_context.market_memory_report_ids

    def test_add_simulation_result(self, empty_context: DecisionContext):
        empty_context.add_simulation_result("sim_099")
        assert "sim_099" in empty_context.simulation_result_ids

    def test_add_duplicate_historical_scenario(self, empty_context: DecisionContext):
        empty_context.add_historical_scenario("hist_001")
        empty_context.add_historical_scenario("hist_001")
        assert empty_context.historical_scenario_ids == ["hist_001"]

    def test_add_duplicate_experiment_result(self, empty_context: DecisionContext):
        empty_context.add_experiment_result("exp_001")
        empty_context.add_experiment_result("exp_001")
        assert empty_context.experiment_result_ids == ["exp_001"]

    def test_add_empty_id_ignored(self, empty_context: DecisionContext):
        empty_context.add_historical_scenario("")
        assert empty_context.historical_scenario_ids == []


# =============================================================================
# DecisionContextValidator
# =============================================================================


class TestValidator:
    """Tests for DecisionContextValidator."""

    def test_valid_context_passes(self, sample_context: DecisionContext, validator: DecisionContextValidator):
        errors = validator.validate(sample_context)
        assert errors == []

    def test_valid_empty_context_passes(self, empty_context: DecisionContext, validator: DecisionContextValidator):
        errors = validator.validate(empty_context)
        assert errors == []

    def test_missing_asset_fails(self, validator: DecisionContextValidator, sample_timestamp: datetime):
        ctx = DecisionContext(asset="", decision_timestamp=sample_timestamp)
        errors = validator.validate(ctx)
        assert any("asset" in e for e in errors)

    def test_duplicate_references_fail(self, validator: DecisionContextValidator, sample_timestamp: datetime):
        ctx = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp, historical_scenario_ids=["hist_001", "hist_001", "hist_002"])
        errors = validator.validate(ctx)
        assert any("Duplicate" in e for e in errors)
        assert any("historical_scenario_ids" in e for e in errors)

    def test_empty_ids_in_list_fail(self, validator: DecisionContextValidator, sample_timestamp: datetime):
        ctx = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp, experiment_result_ids=["exp_001", ""])
        errors = validator.validate(ctx)
        assert any("Empty ID" in e for e in errors)
        assert any("experiment_result_ids" in e for e in errors)

    def test_no_timestamp_fails(self, validator: DecisionContextValidator):
        ctx = DecisionContext(asset="XAUUSD")
        ctx.decision_timestamp = None
        errors = validator.validate(ctx)
        assert any("timestamp" in e.lower() for e in errors)

    def test_is_valid_true(self, sample_context: DecisionContext, validator: DecisionContextValidator):
        assert validator.is_valid(sample_context) is True

    def test_is_valid_false(self, validator: DecisionContextValidator, sample_timestamp: datetime):
        ctx = DecisionContext(asset="", decision_timestamp=sample_timestamp, historical_scenario_ids=["hist_001", "hist_001"])
        assert validator.is_valid(ctx) is False

    def test_multiple_errors(self, validator: DecisionContextValidator):
        ctx = DecisionContext(asset="", historical_scenario_ids=["hist_001", "hist_001"])
        ctx.decision_timestamp = None
        errors = validator.validate(ctx)
        assert len(errors) >= 3

    def test_duplicate_detection_multiple_lists(self, validator: DecisionContextValidator, sample_timestamp: datetime):
        ctx = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp, historical_scenario_ids=["hist_001", "hist_001"], experiment_result_ids=["exp_001", "exp_001"])
        errors = validator.validate(ctx)
        dup_errors = [e for e in errors if "Duplicate" in e]
        assert len(dup_errors) == 2

    def test_empty_single_reference_not_flagged(self, validator: DecisionContextValidator, sample_timestamp: datetime):
        """Empty single reference fields are valid optional defaults, not errors."""
        ctx = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp, market_snapshot_id="")
        errors = validator.validate(ctx)
        assert errors == []


# =============================================================================
# Large Context
# =============================================================================


class TestLargeContext:
    """Tests for large contexts with many references."""

    def test_large_number_of_references(self, sample_timestamp: datetime):
        many_ids = [f"id_{i:04d}" for i in range(1000)]
        ctx = DecisionContext(
            asset="XAUUSD",
            decision_timestamp=sample_timestamp,
            historical_scenario_ids=many_ids,
            experiment_result_ids=many_ids,
            validation_ids=many_ids,
            research_ids=many_ids,
            market_memory_report_ids=many_ids,
            simulation_result_ids=many_ids,
        )
        assert len(ctx.historical_scenario_ids) == 1000
        assert len(ctx.experiment_result_ids) == 1000
        assert len(ctx.validation_ids) == 1000

    def test_large_context_serialization(self, sample_timestamp: datetime):
        many_ids = [f"id_{i:04d}" for i in range(500)]
        ctx = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp, historical_scenario_ids=many_ids)
        d = ctx.to_dict()
        restored = DecisionContext.from_dict(d)
        assert restored.historical_scenario_ids == many_ids
        assert restored.id == ctx.id

    def test_large_context_hash_stable(self, sample_timestamp: datetime):
        many_ids = [f"id_{i:04d}" for i in range(500)]
        ctx1 = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp, historical_scenario_ids=many_ids)
        ctx2 = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp, historical_scenario_ids=list(many_ids))
        assert ctx1.compute_hash() == ctx2.compute_hash()


# =============================================================================
# Lifecycle
# =============================================================================


class TestLifecycle:
    """Tests for lifecycle tracking."""

    def test_initial_stage_is_created(self, sample_context: DecisionContext):
        assert sample_context.lifecycle.current_stage.value == "Created"

    def test_lifecycle_has_transition_reason(self, sample_context: DecisionContext):
        """Index 0 is from BaseObject.__init__; index 1 is from DecisionContext.__init__."""
        transitions = sample_context.lifecycle.transitions
        assert len(transitions) >= 2
        reason = transitions[1].reason
        assert reason is not None
        assert "DecisionContext created" in reason

    def test_lifecycle_serialization(self, sample_context: DecisionContext):
        d = sample_context.to_dict()
        restored = DecisionContext.from_dict(d)
        assert restored.lifecycle.current_stage == sample_context.lifecycle.current_stage
        assert len(restored.lifecycle.transitions) == len(sample_context.lifecycle.transitions)


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_context_with_no_optional_references(self, sample_timestamp: datetime):
        ctx = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp)
        assert ctx.reasoning_chain_id == ""
        assert ctx.audit_entry_id == ""

    def test_context_with_only_asset(self, sample_timestamp: datetime):
        ctx = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp)
        assert ctx.asset == "XAUUSD"
        assert ctx.id is not None

    def test_version_fields_defaults(self, sample_timestamp: datetime):
        ctx = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp)
        assert ctx.dataset_version == "DATASET_V1"
        assert ctx.calculation_version == "DECISION_V1"
        assert ctx.context_version == "CONTEXT_V1"

    def test_to_dict_sorted_keys(self, sample_context: DecisionContext):
        d = sample_context.to_dict()
        json_str = json.dumps(d, sort_keys=True, default=str)
        parsed = json.loads(json_str)
        assert parsed["asset"] == "XAUUSD"

    def test_equality_same_hash(self, sample_timestamp: datetime):
        ctx1 = DecisionContext(asset="XAUUSD", timeframe="1h", decision_timestamp=sample_timestamp)
        ctx2 = DecisionContext(asset="XAUUSD", timeframe="1h", decision_timestamp=sample_timestamp)
        assert ctx1 == ctx2

    def test_inequality_different_content(self, sample_timestamp: datetime):
        ctx1 = DecisionContext(asset="XAUUSD", decision_timestamp=sample_timestamp)
        ctx2 = DecisionContext(asset="BTCUSD", decision_timestamp=sample_timestamp)
        assert ctx1 != ctx2
