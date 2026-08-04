"""
ResearchOS Macro Intelligence Layer - Storage Base
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from macro_intelligence.contracts.series import NormalizedSeries
from macro_intelligence.contracts.evidence import EvidenceObject
from macro_intelligence.contracts.event import MacroEvent


class BaseStore(ABC):
    """
    Abstract base class for all storage backends.
    
    All storage implementations must:
    - Be append-only (no updates to existing records)
    - Support deterministic serialization
    - Maintain audit trails
    """
    
    @abstractmethod
    def write_series(self, series: NormalizedSeries) -> Path:
        """
        Write a series observation to storage.
        
        Returns:
            Path to written file
        """
        pass
    
    @abstractmethod
    def read_series(
        self,
        series_id: str,
        start: Any,
        end: Any,
        include_revisions: bool = False,
    ) -> list[NormalizedSeries]:
        """
        Read series observations within date range.
        
        Returns:
            List of NormalizedSeries
        """
        pass
    
    @abstractmethod
    def write_evidence(self, evidence: EvidenceObject) -> Path:
        """
        Write evidence to storage.
        
        Returns:
            Path to written file
        """
        pass
    
    @abstractmethod
    def read_evidence(self, evidence_id: str) -> EvidenceObject | None:
        """
        Read evidence by ID.
        
        Returns:
            EvidenceObject or None
        """
        pass
    
    @abstractmethod
    def write_event(self, event: MacroEvent) -> Path:
        """
        Write event to storage.
        
        Returns:
            Path to written file
        """
        pass
    
    @abstractmethod
    def read_event(self, event_id: str) -> MacroEvent | None:
        """
        Read event by ID.
        
        Returns:
            MacroEvent or None
        """
        pass
    
    @abstractmethod
    def get_health(self) -> dict[str, Any]:
        """
        Get storage health status.
        
        Returns:
            Dict with storage metrics
        """
        pass
    
    @abstractmethod
    def verify_integrity(self) -> bool:
        """
        Verify storage integrity.
        
        Returns:
            True if storage is intact
        """
        pass
