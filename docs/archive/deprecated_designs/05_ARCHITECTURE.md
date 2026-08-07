# Document Status

Status:
ARCHIVED

Reason:
Historical record only

Superseded by:
See docs/ARCHITECTURE_FREEZE_V2.md (current constitution)

Original purpose:
See docs/DOCUMENTATION_INVENTORY_REPORT.md

---

# ResearchOS — Constitution

## Article V: Architecture

### 5.1 Architectural Philosophy

ResearchOS follows a **three-engine architecture**, each engine serving a distinct purpose. The engines operate independently but share data through a common research record. The architecture is designed for clarity, auditability, and human oversight at every stage.

### 5.2 Engine 1: Market Intelligence Engine

**Purpose:** Produce institutional-grade market research.

**Core Functions:**

| Function | Description |
|---|---|
| Macro Research | Analysis of interest rates, monetary policy, fiscal developments, geopolitical events, and global liquidity |
| Technical Structure | Regime identification, trend analysis, support/resistance, volatility profiling |
| Liquidity Analysis | Order flow, depth-of-market, institutional positioning, liquidity regime changes |
| Cross-Market Analysis | Intermarket relationships, correlation shifts, capital flow tracking |
| Scenario Generation | Construction of probabilistic scenarios with defined validity conditions |

**Outputs:**
- Research reports with clearly stated hypotheses
- Scenario matrices with probability assignments
- Risk factor identification
- Market regime classification
- Cross-market heat maps

### 5.3 Engine 2: Research Validation Engine

**Purpose:** Validate all research against reality.

**Core Functions:**

| Function | Description |
|---|---|
| Reality Comparison | Systematic comparison of past scenarios with actual outcomes |
| Quality Scoring | Quantitative evaluation of accuracy, timeliness, completeness, relevance |
| Failure Analysis | Categorization of errors by failure mode |
| Confidence Calibration | Statistical calibration of probability estimates |

**Outputs:**
- Validation reports with quality scores
- Error analysis by category
- Calibration curves
- Improvement recommendations

### 5.4 Engine 3: Human Cognitive Growth Engine

**Purpose:** Improve the trader's decision-making capability.

**Core Functions:**

| Function | Description |
|---|---|
| Reasoning Evaluation | Assessment of logical structure, completeness, and rigor |
| Knowledge Tracking | Measurement of mental model expansion over time |
| Bias Detection | Identification of systematic cognitive errors |
| Decision Feedback | Structured feedback for continuous improvement |

**Outputs:**
- Reasoning quality reports
- Cognitive bias profiles
- Knowledge growth trajectories
- Targeted improvement exercises

### 5.5 Data Flow

```
Market Data → [Engine 1: Market Intelligence] → Research Outputs
                                                       ↓
                                          [Engine 2: Research Validation]
                                                       ↓
                                          Validation Reports & Scores
                                                       ↓
                                          [Engine 3: Cognitive Growth]
                                                       ↓
                                          Trader Improvement & Learning
```

### 5.6 Audit Trail

Every research output, validation result, and cognitive assessment is recorded in an immutable audit trail. The audit trail enables:

- Complete traceability of any conclusion to its supporting data
- Historical analysis of research quality trends
- Longitudinal tracking of trader cognitive growth
- Forensic analysis of errors and failures

### 5.7 Human Integration Points

1. **Research Question Definition:** The human defines what to research.
2. **Scenario Review:** The human reviews and approves scenarios before they are tracked.
3. **Validation Review:** The human reviews validation results and decides what to change.
4. **Cognitive Feedback Application:** The human applies cognitive feedback to improve decision-making.
5. **Final Decision:** The human makes all trading decisions using research as input.

