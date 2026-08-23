"""
Phase 7.1 — DecisionContext Module.

Purpose:
    DecisionContext is the foundational input to the decision pipeline.
    It represents everything known about the market at one moment in time,
    using ONLY references (IDs) to existing ResearchOS objects — no data duplication.

Exports:
    DecisionContext — A BaseObject subclass representing a complete market snapshot.
    DecisionContextValidator — Validates DecisionContext structural integrity.

Future Phases (not yet implemented):
    Phase 7.2 — EvidenceAggregator (evidence.py — placeholder)
    Phase 7.3 — EvidenceScore (score.py — placeholder)
    Phase 7.4 — ProbabilityAssessment (probability.py — placeholder)
    Phase 7.5 — DecisionReasoner (reasoner.py — placeholder)
    Phase 7.6 — DecisionReport (report.py — placeholder)
"""

from researchos.decision_engine.context import DecisionContext, DecisionContextValidator

__all__ = [
    "DecisionContext",
    "DecisionContextValidator",
]
