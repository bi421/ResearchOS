# Macro Intelligence Layer — Regime Transition Architecture

**Version:** 4.0.0
**Status:** FROZEN (Phase 4 - Transition Analysis)
**Date:** 2026-08-03

## Overview

The Regime Transition Analysis Engine detects transitions between macro regimes, estimates transition probabilities, tracks historical patterns, and generates early warning signals.

## Architecture

```
macro_intelligence/regime/transition/
├── __init__.py          # Package exports
├── models.py            # Data models (all frozen dataclasses)
├── transitions.py       # Transition classification rules
├── probability.py       # Transition probability engine
├── detector.py          # RegimeTransitionDetector orchestrator
└── history.py           # TransitionHistory manager
```

## Data Models

### TransitionSignal
Per-detector signal about an impending regime transition:
- `detector_name`, `signal_id`, `signal_type`, `strength`, `direction`
- `contributing_factors`, `evidence_refs`, `algorithm_version`

### RegimeTransition
A detected transition between two macro regimes:
- `transition_id`, `previous_regime`, `current_regime`, `transition_type`
- `confidence`, `detected_at`, `signals`, `explanation`
- `early_warning`, `early_warning_horizon`

### EarlyWarningSignal
Warning that a transition may be imminent:
- `warning_id`, `current_regime`, `predicted_regime`
- `confidence`, `horizon_periods`, `contributing_signals`

### TransitionAnalysisResult
Complete analysis combining detection, probability, and history:
- `current_regime`, `previous_regime`, `transition_detected`
- `transition`, `early_warnings`, `persistence`, `probability_matrix`

### TransitionHistoryEntry
Logged transition record:
- `transition_id`, `detected_at`, `previous_regime`, `current_regime`
- `transition_type`, `confidence`, `signals_count`, `outcome`

### RegimePersistence
Measures how long a regime has persisted:
- `regime`, `persistence_periods`, `avg_persistence`
- `continuation_probability`, `days_since_last_transition`

### TransitionProbabilityMatrix
Empirical transition probabilities between regimes:
- `transition_probs[from][to]`, `observation_count`, `transition_counts`

## Transition Types

| Type | Description |
|------|-------------|
| `STABLE` | No significant transition pressure |
| `GRADUAL_SHIFT` | Moderate confidence, moderate signal strength |
| `ACCELERATED_SHIFT` | High confidence, moderate-high signal strength |
| `REVERSAL` | Very high confidence, high strength, short persistence |
| `VOLATILE` | High variance in detector signals |
| `UNKNOWN` | Insufficient data |

## Classification Rules

### Transition Type Classification
Based on:
- Average signal strength
- Signal agreement (fraction of detectors agreeing)
- Overall confidence
- Regime persistence periods

### Early Warning Generation
Triggered when:
- Confidence >= 0.50
- Horizon >= 2 periods
- Average signal strength >= 0.3

### Continuation Probability
Calculated from:
- Persistence ratio (current vs historical average)
- Signal strength adjustment

### Probability Matrix Update
Uses exponential moving average with smoothing factor alpha (default 0.1).

## Architecture Invariants

| Invariant | Description | Status |
|-----------|-------------|--------|
| MIL-TRANS-001 | Same input produces identical transition output | ✅ |
| MIL-TRANS-002 | Transition objects are immutable | ✅ |
| MIL-TRANS-003 | All transitions preserve provenance | ✅ |
| MIL-TRANS-004 | Algorithms are versioned | ✅ |
| MIL-TRANS-005 | No dependency on ResearchOS V1 | ✅ |

## Algorithm Versions

| Component | Version |
|-----------|---------|
| Models | `trans-det/v4.0.0` |
| Rules | `trans-rules/v4.0.0` |
| Detector | `trans-det/v4.0.0` |
| History | `trans-hist/v4.0.0` |

## Usage

```python
from macro_intelligence.regime.transition import RegimeTransitionDetector
from macro_intelligence.regime.detection.models import RegimeAssessment

detector = RegimeTransitionDetector()

# Full analysis
result = detector.analyze_transitions(current_assessment, previous_assessment)

# Just detect transition
transition = detector.detect_transition(current_assessment, previous_regime)

# Access history
history = detector.history
entries = history.get_transitions(from_regime=MacroRegime.GOLDILOCKS)
```

## Tests

Run all transition tests:
```bash
pytest tests/unit/test_macro_intelligence/regime/transition/ -v
```

All 58 tests pass, covering:
- Model serialization/deserialization
- Transition signal creation and hashing
- Transition type classification
- Probability engine operations
- History management
- Full detection pipeline
- All 5 MIL-TRANS invariants
- Edge cases and determinism
