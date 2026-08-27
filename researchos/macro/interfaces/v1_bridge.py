"""
ResearchOS Macro Intelligence Layer - V1 Bridge Interface
Version: v1b/v1
Status: FROZEN
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from researchos.macro.interfaces.base import BridgeInterface


class V1BridgeInterface(BridgeInterface, ABC):
    """
    Read-only bridge from V1 Core to Macro Intelligence Layer.

    Rules:
    - V1 Core can ONLY READ through this interface
    - MIL cannot write to V1 Core
    - All changes are additive (new methods, not breaking changes)
    - Version is strictly enforced
    """

    BRIDGE_VERSION = "v1b/v1"

    @abstractmethod
    def query(
        self,
        query_type: str,
        params: dict[str, Any],
    ) -> Any:
        """
        Generic query endpoint for V1 Core.

        Args:
            query_type: Type of query (e.g., "series", "event", "reaction")
            params: Query parameters

        Returns:
            Query result (type varies by query_type)
        """
        pass

    @abstractmethod
    def validate_contract(self) -> dict[str, Any]:
        """
        Validate that the current implementation matches the contract.

        Returns:
            ContractValidationResult with pass/fail status
        """
        pass

    @abstractmethod
    def get_contract_version(self) -> str:
        """
        Get the current contract version.

        Returns:
            Version string (e.g., "v1b/v1")
        """
        pass

    # =====================================================================
    # CONVENIENCE METHODS
    # =====================================================================

    def get_macro_context(self, date: str | None = None) -> dict:
        """
        Get macro context for V1 Core.

        Args:
            date: ISO date string (default: today)

        Returns:
            MacroContext as dictionary
        """
        return self.query("macro_context", {"date": date})

    def get_series_context(
        self,
        series_id: str,
        date: str | None = None,
        lookback_days: int = 90,
    ) -> dict:
        """
        Get context for a specific series.

        Returns:
            SeriesContext as dictionary
        """
        return self.query(
            "series_context",
            {
                "series_id": series_id,
                "date": date,
                "lookback_days": lookback_days,
            },
        )

    def get_regime(self, date: str | None = None) -> dict:
        """
        Get current regime classification.

        Returns:
            RegimeClassification as dictionary
        """
        return self.query("regime", {"date": date})

    def get_correlations(
        self,
        series_a: str,
        series_b: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        """
        Get correlation between two series.

        Returns:
            CorrelationResult as dictionary
        """
        return self.query(
            "correlation",
            {
                "series_a": series_a,
                "series_b": series_b,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
