"""
ResearchOS Macro Intelligence Layer - Regime Interfaces
Version: regime/interfaces/v1
Status: FROZEN
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from macro_intelligence.regime.contracts import (
    MacroRegime,
    RegimeAssessment,
    RegimeConfidence,
    RegimeEvidence,
    RegimeSnapshot,
)


class RegimeDetectorInterface(ABC):
    """
    Interface for regime detection.

    MIL-REG-003: Same evidence produces identical regime object.
    """

    DETECTOR_VERSION = "regime/detector/v1"

    @abstractmethod
    def detect(
        self,
        evidence: List[RegimeEvidence],
        timestamp: datetime,
    ) -> Optional[MacroRegime]:
        """
        Detect regime from evidence.

        Args:
            evidence: List of regime evidence
            timestamp: Detection timestamp

        Returns:
            Detected regime or None if undetectable
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Get detector version."""
        pass

    @abstractmethod
    def validate_evidence(
        self,
        evidence: List[RegimeEvidence],
    ) -> tuple[bool, List[str]]:
        """
        Validate evidence for detection.

        Returns:
            (is_valid, list_of_errors)
        """
        pass


class RegimeClassifierInterface(ABC):
    """
    Interface for regime classification.
    """

    CLASSIFIER_VERSION = "regime/classifier/v1"

    @abstractmethod
    def classify(
        self,
        assessment: RegimeAssessment,
    ) -> MacroRegime:
        """
        Classify regime from assessment.

        Args:
            assessment: Regime assessment

        Returns:
            Classified regime
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Get classifier version."""
        pass

    @abstractmethod
    def get_state_mapping(
        self,
        state_name: str,
    ) -> Dict[str, Any]:
        """
        Get state mapping for classification.

        Args:
            state_name: Name of the state

        Returns:
            Mapping dictionary
        """
        pass


class RegimeScoringInterface(ABC):
    """
    Interface for regime scoring.
    """

    SCORER_VERSION = "regime/scorer/v1"

    @abstractmethod
    def score(
        self,
        assessment: RegimeAssessment,
    ) -> RegimeConfidence:
        """
        Score regime assessment.

        Args:
            assessment: Regime assessment

        Returns:
            Confidence score
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Get scorer version."""
        pass

    @abstractmethod
    def calculate_severity(
        self,
        assessment: RegimeAssessment,
    ) -> str:
        """
        Calculate regime severity.

        Args:
            assessment: Regime assessment

        Returns:
            Severity string
        """
        pass


class RegimeSnapshotInterface(ABC):
    """
    Interface for regime snapshot management.
    """

    SNAPSHOT_VERSION = "regime/snapshot/v1"

    @abstractmethod
    def create_snapshot(
        self,
        assessment: RegimeAssessment,
        timestamp: datetime,
        provenance: Optional[Any] = None,
    ) -> RegimeSnapshot:
        """
        Create regime snapshot.

        Args:
            assessment: Regime assessment
            timestamp: Snapshot timestamp
            provenance: Optional provenance chain

        Returns:
            Regime snapshot
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Get snapshot version."""
        pass

    @abstractmethod
    def compare_snapshots(
        self,
        snapshot1: RegimeSnapshot,
        snapshot2: RegimeSnapshot,
    ) -> Dict[str, Any]:
        """
        Compare two snapshots.

        Args:
            snapshot1: First snapshot
            snapshot2: Second snapshot

        Returns:
            Comparison results
        """
        pass
