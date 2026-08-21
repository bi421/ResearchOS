"""
ResearchOS Macro Intelligence Layer - Macro Query Interface
Version: mqi/v1
Status: FROZEN
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from researchos.macro.contracts.event import MacroEvent
from researchos.macro.contracts.evidence import EvidenceObject
from researchos.macro.contracts.series import NormalizedSeries
from researchos.macro.interfaces.base import QueryInterface


class MacroQueryInterface(QueryInterface, ABC):
    """
    Read-only interface for V1 Core to query Macro Intelligence Layer.

    Version: mqi/v1
    Immutable: Interface contract is frozen
    """

    QUERY_VERSION = "mqi/v1"

    # =====================================================================
    # SERIES QUERIES
    # =====================================================================

    @abstractmethod
    def get_series(
        self,
        series_id: str,
        start: date,
        end: date,
        include_revisions: bool = False,
    ) -> list[NormalizedSeries]:
        """
        Retrieve a time series within a date range.

        Args:
            series_id: Series identifier
            start: Start date (inclusive)
            end: End date (inclusive)
            include_revisions: If True, include all revisions

        Returns:
            List of NormalizedSeries ordered by observation_period ascending
        """
        pass

    @abstractmethod
    def get_latest(self, series_id: str) -> NormalizedSeries | None:
        """
        Retrieve the latest observation for a series.

        Returns:
            Latest NormalizedSeries or None if not found
        """
        pass

    @abstractmethod
    def get_surprise(self, series_id: str, date: date) -> float | None:
        """
        Get the consensus surprise for a data release.

        Returns:
            surprise = actual - forecast (null if no forecast available)
        """
        pass

    @abstractmethod
    def get_yield_curve(self, date: date) -> dict[str, float]:
        """
        Get the full Treasury yield curve for a date.

        Returns:
            {tenor: yield_in_percent} for 2Y, 5Y, 10Y, 30Y
        """
        pass

    @abstractmethod
    def get_spread(
        self,
        tenor_a: str,
        tenor_b: str,
        date: date,
    ) -> float:
        """
        Get the spread between two tenors in basis points.

        Returns:
            Spread in basis points (tenor_a - tenor_b)
        """
        pass

    @abstractmethod
    def get_market_context(
        self,
        series_id: str,
        date: date,
        lookback_days: int = 30,
    ) -> dict:
        """
        Get market context for a series around a date.

        Returns:
            Dict with statistics and nearby events
        """
        pass

    # =====================================================================
    # EVENT QUERIES
    # =====================================================================

    @abstractmethod
    def get_event(self, event_id: str) -> MacroEvent | None:
        """
        Retrieve an event by ID.

        Returns:
            MacroEvent or None if not found
        """
        pass

    @abstractmethod
    def search_events(
        self,
        event_type: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        related_series: list[str] | None = None,
        importance: str | None = None,
        limit: int = 50,
    ) -> list[MacroEvent]:
        """
        Search events with filters.

        Returns:
            List of MacroEvents matching criteria
        """
        pass

    # =====================================================================
    # EVIDENCE QUERIES
    # =====================================================================

    @abstractmethod
    def get_evidence(self, evidence_id: str) -> EvidenceObject | None:
        """
        Retrieve evidence by ID.

        Returns:
            EvidenceObject or None if not found
        """
        pass

    @abstractmethod
    def get_evidence_for_series(
        self,
        series_id: str,
        date: date,
    ) -> list[EvidenceObject]:
        """
        Get all evidence for a series on a date.

        Returns:
            List of EvidenceObjects (may include revisions)
        """
        pass

    # =====================================================================
    # HEALTH & STATUS
    # =====================================================================

    @abstractmethod
    def get_health(self) -> dict[str, Any]:
        """
        Get MIL health status.

        Returns:
            Dict with ingestion status, last update times, etc.
        """
        pass

    @abstractmethod
    def get_series_metadata(self, series_id: str) -> dict | None:
        """
        Get metadata for a series.

        Returns:
            SeriesMetadata dict or None if not found
        """
        pass

    # =====================================================================
    # INTERFACE METHODS
    # =====================================================================

    def validate_contract(self) -> dict[str, Any]:
        """Validate interface contract compliance."""
        return {
            "is_valid": True,
            "version": self.QUERY_VERSION,
            "interface": "MacroQueryInterface",
            "methods_count": len([m for m in dir(self) if not m.startswith("_")]),
        }

    def get_contract_version(self) -> str:
        """Get interface contract version."""
        return self.QUERY_VERSION
