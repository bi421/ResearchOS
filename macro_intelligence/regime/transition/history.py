"""
ResearchOS Macro Intelligence Layer - Transition History Manager

Manages the history of detected regime transitions.
All operations are deterministic and append-only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from macro_intelligence.regime.classification.taxonomy import MacroRegime
from macro_intelligence.regime.transition.models import (
    TransitionHistoryEntry,
    RegimeTransition,
)


class TransitionHistory:
    """
    Immutable history of regime transitions.
    
    Append-only log with deterministic ordering.
    """
    
    def __init__(self):
        self._entries: list[TransitionHistoryEntry] = []
        self._version = "trans-hist/v4.0.0"
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def entries(self) -> list[TransitionHistoryEntry]:
        """Get all history entries (read-only)."""
        return list(self._entries)
    
    @property
    def count(self) -> int:
        """Get the number of recorded transitions."""
        return len(self._entries)
    
    def add_transition(
        self,
        transition: RegimeTransition,
        outcome: str = "pending",
    ) -> TransitionHistoryEntry:
        """
        Add a transition to the history.
        
        Args:
            transition: The detected transition
            outcome: Current outcome status ("pending", "confirmed", "reversed")
            
        Returns:
            The history entry created
        """
        entry = TransitionHistoryEntry(
            transition_id=transition.transition_id,
            detected_at=transition.detected_at,
            previous_regime=transition.previous_regime,
            current_regime=transition.current_regime,
            transition_type=transition.transition_type,
            confidence=transition.confidence,
            signals_count=len(transition.signals),
            outcome=outcome,
        )
        self._entries.append(entry)
        return entry
    
    def update_outcome(
        self,
        transition_id: str,
        outcome: str,
        duration_observed: int | None = None,
    ) -> bool:
        """
        Update the outcome of a recorded transition.
        
        Returns True if found and updated, False otherwise.
        """
        for i, entry in enumerate(self._entries):
            if entry.transition_id == transition_id:
                # Create new entry with updated outcome
                new_entry = TransitionHistoryEntry(
                    transition_id=entry.transition_id,
                    detected_at=entry.detected_at,
                    previous_regime=entry.previous_regime,
                    current_regime=entry.current_regime,
                    transition_type=entry.transition_type,
                    confidence=entry.confidence,
                    signals_count=entry.signals_count,
                    duration_observed=duration_observed,
                    outcome=outcome,
                )
                self._entries[i] = new_entry
                return True
        return False
    
    def get_transitions(
        self,
        from_regime: MacroRegime | None = None,
        to_regime: MacroRegime | None = None,
        transition_type: str | None = None,
        outcome: str | None = None,
    ) -> list[TransitionHistoryEntry]:
        """
        Get transitions with optional filtering.
        
        Args:
            from_regime: Filter by source regime
            to_regime: Filter by target regime
            transition_type: Filter by transition type
            outcome: Filter by outcome
            
        Returns:
            Filtered list of history entries
        """
        results = self._entries
        
        if from_regime is not None:
            results = [e for e in results if e.previous_regime == from_regime]
        if to_regime is not None:
            results = [e for e in results if e.current_regime == to_regime]
        if transition_type is not None:
            results = [e for e in results if e.transition_type == transition_type]
        if outcome is not None:
            results = [e for e in results if e.outcome == outcome]
        
        return list(results)
    
    def get_last_transition(self) -> TransitionHistoryEntry | None:
        """Get the most recent transition."""
        if not self._entries:
            return None
        return self._entries[-1]
    
    def get_transitions_since(
        self,
        since_datetime: datetime,
   ) -> list[TransitionHistoryEntry]:
        """Get transitions detected after a given datetime."""
        return [e for e in self._entries if e.detected_at >= since_datetime]
    
    def get_transition_counts(
        self,
   ) -> dict[str, dict[str, int]]:
        """
        Get transition frequency counts.
        
        Returns:
            Dict mapping (from_regime, to_regime) to count
        """
        counts: dict[str, dict[str, int]] = {}
        for entry in self._entries:
            from_key = entry.previous_regime.value
            to_key = entry.current_regime.value
            if from_key not in counts:
                counts[from_key] = {}
            if to_key not in counts[from_key]:
                counts[from_key][to_key] = 0
            counts[from_key][to_key] += 1
        return counts
    
    def get_regime_appearances(self) -> dict[str, int]:
        """Get how many times each regime has appeared as a target."""
        counts: dict[str, int] = {}
        for entry in self._entries:
            key = entry.current_regime.value
            counts[key] = counts.get(key, 0) + 1
        return counts
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize history."""
        return {
            "version": self._version,
            "entries": [e.to_dict() for e in self._entries],
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransitionHistory:
        """Deserialize history."""
        history = cls()
        for entry_data in data.get("entries", []):
            entry = TransitionHistoryEntry.from_dict(entry_data)
            history._entries.append(entry)
        return history
    
    def compute_hash(self) -> str:
        """Deterministic hash of the entire history."""
        import hashlib
        import json
        hash_data = {
            "version": self._version,
            "entry_count": len(self._entries),
            "entries": [e.compute_hash() for e in self._entries],
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
