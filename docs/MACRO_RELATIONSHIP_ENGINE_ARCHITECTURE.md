# Macro Intelligence Layer — Historical Relationship Engine Architecture

**Version:** 5.0.0
**Status:** FROZEN (Phase 5 - Relationship Analysis)
**Date:** 2026-08-03

## Overview

The Historical Relationship Engine analyzes deterministic statistical relationships between macroeconomic variables using only frozen MIL contracts.

## Architecture

```
macro_intelligence/relationships/
├── __init__.py          # Package exports
├── models.py            # Frozen dataclass models
├── correlation.py       # Pearson, Spearman, rolling correlation
├── rolling.py           # Rolling correlation utilities
├── lag_analysis.py      # Lead/lag detection
├── regime_relationship.py  # Regime-conditional correlations
├── break_detection.py   # Structural break detection
└── engine.py            # RelationshipEngine orchestrator
```

## Models

| Model | Purpose |
|-------|---------|
| `CorrelationResult` | Pairwise correlation with type/strength classification |
| `RollingCorrelationResult` | Time-series of correlations with stability metric |
| `LagRelationship` | Optimal lag and correlation between series |
| `RegimeRelationship` | Correlation conditioned on macro regime |
| `StructuralBreak` | Detected break point with before/after correlations |
| `RelationshipResult` | Complete analysis combining all methods |

## Capabilities

### 1. Correlation Engine
- **Pearson correlation** — linear relationship
- **Spearman correlation** — monotonic relationship (rank-based)
- **Relationship classification** — type (positive/negative/neutral) + strength (very_strong/strong/moderate/weak/negligible)
- **P-value approximation** — statistical significance

### 2. Rolling Correlation
- Configurable window size
- Stability metric (standard deviation of rolling correlations)
- Trend detection (slope of correlation over time)

### 3. Lag Analysis
- Cross-correlation to find optimal lag
- Leading indicator detection (positive lag = series_a leads)
- Lagging indicator detection (negative lag = series_b leads)
- Reaction delay detection (event-driven)

### 4. Regime-Conditional Relationships
- Correlation computed separately for each macro regime
- Enables analysis like: "Gold/DXY correlation in risk-off vs expansion"
- Sample size validation per regime

### 5. Structural Break Detection
- Scans for correlation changes over time
- Classifies break type (strength_change, direction_change)
- Confidence scoring based on change magnitude
- Deduplication of nearby breaks

## Architecture Invariants

| Invariant | Description |
|-----------|-------------|
| MIL-REL-001 | Same input produces identical relationship output |
| MIL-REL-002 | Relationship objects are immutable |
| MIL-REL-003 | All relationships preserve provenance |
| MIL-REL-004 | Algorithms are versioned |
| MIL-REL-005 | No dependency on ResearchOS V1 |
| MIL-REL-006 | Historical reconstruction is deterministic |

## Algorithm Versions

| Component | Version |
|-----------|---------|
| Models | `rel-eng/v5.0.0` |
| Engine | `rel-eng/v5.0.0` |

## Usage

```python
from macro_intelligence.relationships import RelationshipEngine

engine = RelationshipEngine()

# Simple correlation
corr = engine.analyze_correlation(x, y, "XAU", "DXY")

# Full analysis
result = engine.full_analysis(
    x, y, "XAU", "DXY",
    regime_labels=regimes,
    rolling_window=20,
    max_lag=10,
)
```

## Limitations

1. **Pure statistics only** — No causal inference, no ML
2. **Linear relationships** — Pearson captures linear, Spearman captures monotonic
3. **No missing data handling** — All series must be same length
4. **No stationarity checks** — User responsible for data preprocessing
5. **No multiple testing correction** — P-values are approximate

## Tests

Run all relationship tests:
```bash
pytest tests/unit/test_macro_intelligence/relationships/ -v
```

All 50 tests pass, covering:
- Pearson and Spearman accuracy
- Rolling correlation
- Lag detection
- Regime-conditional relationships
- Structural break detection
- All 6 MIL-REL invariants
- Determinism and immutability
