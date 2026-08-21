"""
DecisionContext — everything known at decision time (references only).

Based on Article XVII: Object Model — Decision Engine Layer.

Represents a single complete market snapshot at one moment in time.
Contains only references (IDs) to existing ResearchOS objects — NO data duplication.
This ensures every DecisionContext is lightweight, auditable, and deterministic.

References:
    - Market Snapshot ID
    - Market Regime ID
    - Macro State ID
    - Historical Scenario IDs
    - Experiment Result IDs
    - Validation IDs
    - Research IDs
    - Market Memory Report IDs
    - Simulation Result IDs
    - Reasoning Chain ID (optional)
    - Audit Entry ID (optional)

Metadata:
    asset, symbol, timeframe, decision_timestamp,
    dataset_version, calculation_version, context_version

Design Principles:
    - References only: No embedded data from other objects.
    - Deterministic: Same inputs → same ID and hash.
    - Auditable: Full lifecycle tracking.
    - Serializable: Full to_dict/from_dict support.
"""

from __future__ import annotations


import pandas as pd
from typing import Dict, Optional
from datetime import datetime


from typing import Any, List


from researchos.core.base_object import BaseObject


from researchos.core.identity import generate_id


from researchos.core.lifecycle import LifecycleStage


from researchos.core.timestamp import parse_timestamp, utc_now


class DecisionContext(BaseObject):
    """
    A complete snapshot of everything known about the market at one moment.

    This is the foundational input to the decision pipeline. It collects
    references to all existing ResearchOS objects that contribute to a
    decision. NO data from those objects is duplicated here — only IDs.

    Required References:
        market_snapshot_id: ID of the current MarketSnapshot.
        market_regime_id: ID of the current MarketRegime classification.
        macro_state_id: ID of the current MacroState assessment.
        historical_scenario_ids: IDs of matched HistoricalScenarios.
        experiment_result_ids: IDs of ExperimentResults.
        validation_ids: IDs of ExperimentValidations.
        research_ids: IDs of Research cycles.
        market_memory_report_ids: IDs of MarketMemoryReports.
        simulation_result_ids: IDs of QuantEngine SimulationResults.

    Optional References:
        reasoning_chain_id: ID of the ReasoningChain (from process objects).
        audit_entry_id: ID of the AuditEntry (from process objects).

    Metadata:
        asset: Asset symbol (e.g., "XAUUSD").
        symbol: Alternate symbol identifier.
        timeframe: Bar timeframe (e.g., "1h", "4h", "1d").
        decision_timestamp: UTC timestamp of this decision context.
        dataset_version: Version of the dataset used.
        calculation_version: Version of calculation methodology.
        context_version: Version of this context schema.
    """

    def __init__(
        self,
        asset: str,
        market_snapshot_id: str = "",
        market_regime_id: str = "",
        macro_state_id: str = "",
        historical_scenario_ids: Optional[List[str]] = None,
        experiment_result_ids: Optional[List[str]] = None,
        validation_ids: Optional[List[str]] = None,
        research_ids: Optional[List[str]] = None,
        market_memory_report_ids: Optional[List[str]] = None,
        simulation_result_ids: Optional[List[str]] = None,
        reasoning_chain_id: str = "",
        audit_entry_id: str = "",
        symbol: str = "",
        timeframe: str = "",
        decision_timestamp: Optional[datetime] = None,
        dataset_version: str = "DATASET_V1",
        calculation_version: str = "DECISION_V1",
        context_version: str = "CONTEXT_V1",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        self.macro_data: Optional[pd.DataFrame] = None
        self.macro_correlations: Optional[Dict[str, float]] = None
        if id is None:
            ts = decision_timestamp.isoformat() if decision_timestamp else utc_now().isoformat()
            seed = f"DecisionContext|{asset}|{ts}|{timeframe}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        # Required references
        self.asset = asset
        self.market_snapshot_id = market_snapshot_id
        self.market_regime_id = market_regime_id
        self.macro_state_id = macro_state_id
        self.historical_scenario_ids: List[str] = historical_scenario_ids or []
        self.experiment_result_ids: List[str] = experiment_result_ids or []
        self.validation_ids: List[str] = validation_ids or []
        self.research_ids: List[str] = research_ids or []
        self.market_memory_report_ids: List[str] = market_memory_report_ids or []
        self.simulation_result_ids: List[str] = simulation_result_ids or []

        # Optional references
        self.reasoning_chain_id = reasoning_chain_id
        self.audit_entry_id = audit_entry_id

        # Metadata
        self.symbol = symbol
        self.timeframe = timeframe
        self.decision_timestamp = decision_timestamp or utc_now()
        self.dataset_version = dataset_version
        self.calculation_version = calculation_version
        self.context_version = context_version

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason=f"DecisionContext created for {asset} ({timeframe})",
        )

    # ------------------------------------------------------------------
    # Reference management helpers
    # ------------------------------------------------------------------

    def add_historical_scenario(self, scenario_id: str) -> None:
        """Add a historical scenario reference."""
        if scenario_id and scenario_id not in self.historical_scenario_ids:
            self.historical_scenario_ids.append(scenario_id)

    def add_experiment_result(self, result_id: str) -> None:
        """Add an experiment result reference."""
        if result_id and result_id not in self.experiment_result_ids:
            self.experiment_result_ids.append(result_id)

    def add_validation(self, validation_id: str) -> None:
        """Add a validation reference."""
        if validation_id and validation_id not in self.validation_ids:
            self.validation_ids.append(validation_id)

    def add_research(self, research_id: str) -> None:
        """Add a research reference."""
        if research_id and research_id not in self.research_ids:
            self.research_ids.append(research_id)

    def add_market_memory_report(self, report_id: str) -> None:
        """Add a market memory report reference."""
        if report_id and report_id not in self.market_memory_report_ids:
            self.market_memory_report_ids.append(report_id)

    def add_simulation_result(self, result_id: str) -> None:
        """Add a simulation result reference."""
        if result_id and result_id not in self.simulation_result_ids:
            self.simulation_result_ids.append(result_id)

    # ------------------------------------------------------------------
    # Deterministic identity & serialization
    # ------------------------------------------------------------------

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "market_snapshot_id": self.market_snapshot_id,
            "market_regime_id": self.market_regime_id,
            "macro_state_id": self.macro_state_id,
            "historical_scenario_ids": sorted(self.historical_scenario_ids),
            "experiment_result_ids": sorted(self.experiment_result_ids),
            "validation_ids": sorted(self.validation_ids),
            "research_ids": sorted(self.research_ids),
            "market_memory_report_ids": sorted(self.market_memory_report_ids),
            "simulation_result_ids": sorted(self.simulation_result_ids),
            "reasoning_chain_id": self.reasoning_chain_id,
            "audit_entry_id": self.audit_entry_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "decision_timestamp": self.decision_timestamp.isoformat(),
            "dataset_version": self.dataset_version,
            "calculation_version": self.calculation_version,
            "context_version": self.context_version,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "asset": self.asset,
                "market_snapshot_id": self.market_snapshot_id,
                "market_regime_id": self.market_regime_id,
                "macro_state_id": self.macro_state_id,
                "historical_scenario_ids": self.historical_scenario_ids,
                "experiment_result_ids": self.experiment_result_ids,
                "validation_ids": self.validation_ids,
                "research_ids": self.research_ids,
                "market_memory_report_ids": self.market_memory_report_ids,
                "simulation_result_ids": self.simulation_result_ids,
                "reasoning_chain_id": self.reasoning_chain_id,
                "audit_entry_id": self.audit_entry_id,
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "decision_timestamp": self.decision_timestamp.isoformat(),
                "dataset_version": self.dataset_version,
                "calculation_version": self.calculation_version,
                "context_version": self.context_version,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionContext":
        obj = super().from_dict(data)
        obj.asset = data["asset"]
        obj.market_snapshot_id = data.get("market_snapshot_id", "")
        obj.market_regime_id = data.get("market_regime_id", "")
        obj.macro_state_id = data.get("macro_state_id", "")
        obj.historical_scenario_ids = list(data.get("historical_scenario_ids", []))
        obj.experiment_result_ids = list(data.get("experiment_result_ids", []))
        obj.validation_ids = list(data.get("validation_ids", []))
        obj.research_ids = list(data.get("research_ids", []))
        obj.market_memory_report_ids = list(data.get("market_memory_report_ids", []))
        obj.simulation_result_ids = list(data.get("simulation_result_ids", []))
        obj.reasoning_chain_id = data.get("reasoning_chain_id", "")
        obj.audit_entry_id = data.get("audit_entry_id", "")
        obj.symbol = data.get("symbol", "")
        obj.timeframe = data.get("timeframe", "")
        obj.decision_timestamp = (
            parse_timestamp(data["decision_timestamp"])
            if data.get("decision_timestamp")
            else utc_now()
        )
        obj.dataset_version = data.get("dataset_version", "DATASET_V1")
        obj.calculation_version = data.get("calculation_version", "DECISION_V1")
        obj.context_version = data.get("context_version", "CONTEXT_V1")
        return obj


# =============================================================================
# DecisionContextValidator
# =============================================================================


class DecisionContextValidator:
    """
    Validates a DecisionContext for structural integrity.

    Rules:
        1. required references — asset must be non-empty
        2. valid timestamp — decision_timestamp must be set
        3. duplicate references rejected — no duplicate IDs in any reference list
        4. empty IDs rejected — no empty strings in reference lists

    The validator does NOT check that referenced objects actually exist
    in the repository (that is a repository-level concern).

    Usage:
        validator = DecisionContextValidator()
        errors = validator.validate(ctx)
        if errors:
            for error in errors:
                print(f"Validation error: {error}")
    """

    REQUIRED_FIELDS = [
        "asset",
    ]

    REFERENCE_LISTS = [
        "historical_scenario_ids",
        "experiment_result_ids",
        "validation_ids",
        "research_ids",
        "market_memory_report_ids",
        "simulation_result_ids",
    ]

    SINGLE_REFERENCES = [
        "market_snapshot_id",
        "market_regime_id",
        "macro_state_id",
        "reasoning_chain_id",
        "audit_entry_id",
    ]

    def validate(self, context: DecisionContext) -> List[str]:
        """
        Validate a DecisionContext.

        Args:
            context: The DecisionContext to validate.

        Returns:
            List of error messages. Empty list means validation passed.
        """
        errors: List[str] = []

        # Rule 1: Required fields
        errors.extend(self._check_required(context))

        # Rule 2: Valid timestamp
        errors.extend(self._check_timestamp(context))

        # Rule 3: Duplicate references
        errors.extend(self._check_duplicates(context))

        # Rule 4: Empty IDs
        errors.extend(self._check_empty_ids(context))

        return errors

    def _check_required(self, context: DecisionContext) -> List[str]:
        """Check that required fields are non-empty."""
        errors = []
        if not context.asset:
            errors.append("Required field 'asset' is empty")
        return errors

    def _check_timestamp(self, context: DecisionContext) -> List[str]:
        """Check that decision_timestamp is valid."""
        errors = []
        if context.decision_timestamp is None:
            errors.append("decision_timestamp is not set")
        return errors

    def _check_duplicates(self, context: DecisionContext) -> List[str]:
        """Check that no reference list contains duplicates."""
        errors = []
        for list_name in self.REFERENCE_LISTS:
            ids = getattr(context, list_name, [])
            seen = set()
            duplicates = set()
            for ref_id in ids:
                if ref_id in seen:
                    duplicates.add(ref_id)
                seen.add(ref_id)
            if duplicates:
                dup_str = ", ".join(sorted(duplicates))
                errors.append(f"Duplicate references found in '{list_name}': {dup_str}")
        return errors

    def _check_empty_ids(self, context: DecisionContext) -> List[str]:
        """Check that no reference list contains empty strings."""
        errors = []
        for list_name in self.REFERENCE_LISTS:
            ids = getattr(context, list_name, [])
            empty_ids = [ref_id for ref_id in ids if not ref_id]
            if empty_ids:
                errors.append(f"Empty ID found in '{list_name}' ({len(empty_ids)} occurrence(s))")
        return errors

    def is_valid(self, context: DecisionContext) -> bool:
        """Quick check if a DecisionContext is valid."""
        return len(self.validate(context)) == 0
