# ResearchOS — Constitution

## Article XIII: Knowledge Engine

> **Version:** 1.0.0
> **Status:** Phase 0 — Constitutional Foundation
> **Last Updated:** 2026-07-29
> **Determinism Guarantee:** Every knowledge entry is created by a deterministic rule that maps a specific input (validation result, reasoning trace, or research artifact) to a structured knowledge record. No knowledge is inferred through machine learning or subjective interpretation.
> **Explainability Guarantee:** Every knowledge entry is traceable to its source — the specific research report, validation result, or reasoning trace that produced it. Every relationship between knowledge entries is explicitly documented with its analytical rationale.

---

### 13.1 Overview

The Knowledge Engine is the component of ResearchOS that accumulates, organizes, and manages institutional knowledge over time. It transforms the outputs of the Validation Engine (Article XII) into structured, reusable knowledge that improves future research.

The Knowledge Engine manages five knowledge repositories:

| Repository | Description | Article Reference |
|---|---|---|
| **Research Memory** | Complete archive of all research reports and their validation results | VII, XII |
| **Historical Pattern Library** | Patterns identified from historical data and validated research | VII.6.6, XII |
| **Market Knowledge Base** | Structured knowledge about market behavior, relationships, and regimes | IX, VII.5-7.7 |
| **Reasoning History** | Complete archive of all reasoning traces and their outcomes | X, XII |
| **Lessons Learned** | Actionable lessons extracted from validation failures and successes | XII.5-12.6 |

Each repository is populated deterministically by rules that map specific inputs to structured knowledge records. All knowledge entries are versioned, timestamped, and traceable to their sources.

---

### 13.2 Research Memory

**Ontology Reference:** `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:STATE:REGIME`

#### 13.2.1 Purpose

Research Memory is the complete, immutable archive of all research reports produced by ResearchOS, along with their validation results. It enables historical analysis, pattern identification, and continuous improvement.

#### 13.2.2 Structure

```
ResearchMemoryEntry:
  research_id:          string (deterministic UUID)
  research_timestamp:   timestamp
  research_question:    string
  time_horizon:         string
  asset:                string
  methodology_version:  string
  report_hash:          string
  validation_results:   [ValidationResultSummary]
  quality_score:        float
  lessons_learned:      [string]
  memory_trace:         string
```

#### 13.2.3 Population Procedure

1. **Research Report Archiving:**
   - When a research report is generated (Article VII, Section 7.12), it is automatically archived.
   - The report's hash, metadata, and key conclusions are stored.
   - The report is indexed by asset, time horizon, and research question type.

2. **Validation Result Linking:**
   - When the Validation Engine (Article XII) validates a research report, the validation results are linked to the memory entry.
   - The validation summary includes: overall status, quality score, scenario accuracy, and failure causes.

3. **Lesson Extraction:**
   - From the validation results, actionable lessons are extracted using deterministic rules:
     - If a scenario was invalidated due to data error → Lesson: "Source X has reliability issues"
     - If a scenario was invalidated due to assumption error → Lesson: "Primary driver Y is unreliable"
     - If a scenario was invalidated due to model error → Lesson: "Model Z needs recalibration"
     - If a scenario was invalidated due to cognitive error → Lesson: "Trader exhibited bias W"

4. **Indexing:**
   - Each memory entry is indexed by:
     - **Asset** — The asset class and specific instrument
     - **Time Horizon** — The research time horizon
     - **Regime** — The market regime at the time of research
     - **Outcome** — Whether the research was accurate or inaccurate
     - **Failure Mode** — If inaccurate, the primary failure mode

#### 13.2.4 Retrieval

Research Memory entries are retrieved using deterministic queries:

- **By Asset:** Find all research on a specific asset
- **By Regime:** Find all research conducted during a specific market regime
- **By Accuracy:** Find all accurate/inaccurate research
- **By Time Period:** Find all research within a specific time range
- **By Failure Mode:** Find all research that failed due to a specific cause

---

### 13.3 Historical Pattern Library

**Ontology Reference:** `ONTOLOGY:RELATIONSHIP:LEADS`, `ONTOLOGY:RELATIONSHIP:REGIME_DEPENDENT`

#### 13.3.1 Purpose

The Historical Pattern Library stores patterns identified from historical data and validated research. These patterns are the building blocks for scenario generation, narrative construction, and hypothesis formation.

#### 13.3.2 Pattern Types

| Pattern Type | Description | Example |
|---|---|---|
| **Regime Transition** | Patterns of regime changes | "Expansion → Stagflation when inflation > 5% and growth < 2%" |
| **Event Impact** | Patterns of market responses to events | "Fed rate hike → 2% equity decline in 5 days" |
| **Cross-Market** | Patterns of inter-market relationships | "USD strength → commodity decline" |
| **Technical** | Patterns of price action | "Double bottom → 15% rally in 30 days" |
| **Sentiment** | Patterns of sentiment effects | "VIX > 30 → 5% equity decline in 10 days" |
| **Liquidity** | Patterns of liquidity effects | "Repo rate spike → 3% equity decline in 3 days" |

#### 13.3.3 Pattern Structure

```
Pattern:
  pattern_id:        string (deterministic UUID)
  type:              [Regime_Transition | Event_Impact | Cross_Market | Technical | Sentiment | Liquidity]
  description:       string
  trigger_conditions: [Condition]
  outcome:           string
  historical_accuracy: float
  sample_size:       int
  confidence_interval: {lower: float, upper: float}
  supporting_evidence: [EvidenceReference]
  contradicting_evidence: [EvidenceReference]
  first_identified:   timestamp
  last_validated:     timestamp
  pattern_trace:      string
```

#### 13.3.4 Pattern Identification Procedure

1. **Pattern Detection:**
   - The system scans the Research Memory for recurring patterns in research outcomes.
   - Patterns are identified using deterministic rules:
     - **Frequency Threshold** — A pattern must appear at least 3 times in the memory
     - **Consistency Threshold** — The pattern must produce the same outcome at least 70% of the time
     - **Recency Weight** — More recent occurrences are weighted higher

2. **Pattern Validation:**
   - Each identified pattern is validated against out-of-sample data:
     - The pattern is tested on research conducted after the pattern was first identified
     - If the pattern holds in out-of-sample testing, it is added to the library
     - If the pattern fails, it is flagged for review

3. **Pattern Scoring:**
   - Each pattern is assigned a quality score:
     ```
     Pattern_Score = (Accuracy × 0.40) + (Sample_Size × 0.30) + (Recency × 0.20) + (Consistency × 0.10)
     ```
   - Patterns with scores below 0.50 are flagged for review or removal.

4. **Pattern Linking:**
   - Patterns are linked to ontology concepts:
     - **Entity** — The asset or market the pattern applies to
     - **State** — The market state the pattern describes
     - **Relationship** — The relationship the pattern captures
     - **Event** — The event the pattern responds to

#### 13.3.5 Pattern Usage

Patterns are used in:
- **Scenario Generation** (Article XI) — As building blocks for tail scenarios
- **Narrative Construction** (Article VII, Section 7.8) — As evidence for narrative plausibility
- **Hypothesis Formation** (Article VII, Section 7.2) — As templates for new hypotheses
- **Confidence Estimation** (Article VII, Section 7.10) — As historical precedent for confidence scoring

---

### 13.4 Market Knowledge Base

**Ontology Reference:** `ONTOLOGY:ENTITY`, `ONTOLOGY:CLASSIFICATION`, `ONTOLOGY:RELATIONSHIP`

#### 13.4.1 Purpose

The Market Knowledge Base stores structured knowledge about market behavior, relationships, and regimes. It is the semantic foundation for all market understanding in ResearchOS.

#### 13.4.2 Knowledge Categories

| Category | Description | Ontology Reference |
|---|---|---|
| **Entity Properties** | Characteristics of market entities | `ONTOLOGY:ENTITY` |
| **Classification Rules** | Rules for classifying entities | `ONTOLOGY:CLASSIFICATION` |
| **State Transitions** | Rules for state changes | `ONTOLOGY:STATE` |
| **Relationship Strengths** | Quantified relationships between entities | `ONTOLOGY:RELATIONSHIP` |
| **Event Impacts** | Historical impacts of market events | `ONTOLOGY:EVENT` |
| **Regime Characteristics** | Properties of different market regimes | `ONTOLOGY:STATE:REGIME` |

#### 13.4.3 Knowledge Entry Structure

```
KnowledgeEntry:
  entry_id:          string (deterministic UUID)
  category:          string
  subject:           string (ontology concept ID)
  predicate:         string
  object:            string
  confidence:        float
  evidence_count:    int
  last_updated:      timestamp
  source_references: [string]
  knowledge_trace:   string
```

#### 13.4.4 Knowledge Population Procedure

1. **Entity Property Extraction:**
   - From research reports, entity properties are extracted:
     - Asset volatility characteristics
     - Correlation patterns
     - Seasonal tendencies
     - Response to macro factors

2. **Classification Rule Learning:**
   - From regime classifications, rules are extracted:
     - "If inflation > 5% and growth < 2%, then Stagflation"
     - "If VIX > 30 and volume > 2× average, then High Volatility Range"

3. **Relationship Strength Quantification:**
   - From cross-market analysis, relationships are quantified:
     - "USD and commodities: correlation = -0.45"
     - "Gold and real yields: correlation = -0.60"

4. **Event Impact Recording:**
   - From event analysis, impacts are recorded:
     - "Fed rate hike: average 2% equity decline in 5 days"
     - "CPI surprise > 0.5%: average 1.5% equity decline in 1 day"

5. **Regime Characteristic Documentation:**
   - From regime analysis, characteristics are documented:
     - "Expansion: low volatility, rising prices, accommodative policy"
     - "Stagflation: high volatility, rising prices, constrained policy"

#### 13.4.5 Knowledge Retrieval

Knowledge entries are retrieved using:
- **Entity Queries** — Find all knowledge about a specific entity
- **Relationship Queries** — Find all relationships between entities
- **State Queries** — Find all knowledge about a specific state
- **Event Queries** — Find all knowledge about a specific event type

---

### 13.5 Reasoning History

**Ontology Reference:** `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:STATE`

#### 13.5.1 Purpose

Reasoning History is the complete archive of all reasoning traces produced by the Reasoning Engine (Article X). It enables analysis of reasoning quality, identification of systematic errors, and continuous improvement of the reasoning process.

#### 13.5.2 Structure

```
ReasoningHistoryEntry:
  trace_id:          string (deterministic UUID)
  research_id:       string
  stage:             [Observation | Evidence | Interpretation | Contradiction | Scenario | Confidence | Report]
  inputs:            [string]
  rules_applied:     [string]
  outputs:           [string]
  reasoning_time:    float (seconds)
  validation_result: string
  quality_score:     float
  history_trace:     string
```

#### 13.5.3 Population Procedure

1. **Trace Archiving:**
   - Every reasoning trace produced by the Reasoning Engine is automatically archived.
   - The trace includes: inputs, rules applied, outputs, and timing.

2. **Validation Linking:**
   - When the Validation Engine validates a research report, the validation result is linked to the reasoning history entry.

3. **Quality Analysis:**
   - The quality of each reasoning trace is analyzed:
     - **Correctness** — Whether the reasoning led to correct conclusions
     - **Efficiency** — Whether the reasoning was computationally efficient
     - **Completeness** — Whether all relevant evidence was considered
     - **Consistency** — Whether the reasoning was internally consistent

4. **Pattern Extraction:**
   - From reasoning history, patterns are extracted:
     - "Macro analysis tends to overestimate inflation impact"
     - "Technical analysis is more accurate in trending regimes"
     - "Liquidity analysis is more reliable when market depth is high"

#### 13.5.4 Analysis Uses

Reasoning History is used for:
- **Reasoning Quality Assessment** — Measuring the accuracy of each reasoning stage
- **Bias Detection** — Identifying systematic errors in reasoning
- **Process Improvement** — Improving the reasoning pipeline
- **Training** — Providing examples for cognitive growth

---

### 13.6 Lessons Learned

**Ontology Reference:** `ONTOLOGY:RELATIONSHIP:CONTRADICTS`, `ONTOLOGY:STATE:SENTIMENT`

#### 13.6.1 Purpose

Lessons Learned is the repository of actionable insights extracted from validation results and reasoning history. Each lesson is a specific, testable recommendation for improving future research.

#### 13.6.2 Lesson Types

| Lesson Type | Description | Example |
|---|---|---|
| **Data Lesson** | Improvements to data collection or quality | "Source X has reliability issues during crisis periods" |
| **Model Lesson** | Improvements to analytical models | "Inflation model underestimates core CPI by 0.3%" |
| **Process Lesson** | Improvements to research process | "Need to check cross-market relationships before finalizing narrative" |
| **Bias Lesson** | Identification of cognitive biases | "Trader tends to overweight recent evidence (recency bias)" |
| **Scenario Lesson** | Improvements to scenario construction | "Tail scenarios need wider return ranges" |
| **Validation Lesson** | Improvements to validation process | "Need to validate scenarios daily, not weekly" |

#### 13.6.3 Lesson Structure

```
Lesson:
  lesson_id:          string (deterministic UUID)
  type:              [Data | Model | Process | Bias | Scenario | Validation]
  description:       string
  recommendation:    string
  severity:          float (0.0-1.0)
  frequency:         int
  first_observed:    timestamp
  last_observed:     timestamp
  affected_articles: [string]
  supporting_evidence: [EvidenceReference]
  lesson_trace:      string
```

#### 13.6.4 Lesson Extraction Procedure

1. **Failure Analysis Review:**
   - The system reviews all failure analyses from the Validation Engine (Article XII, Section 12.5).
   - For each failure, the system extracts lessons using deterministic rules:

   **Data Error → Data Lesson:**
   - If failure mode is Data Error and source reliability < 0.85 → Lesson: "Source X reliability needs review"
   - If failure mode is Data Error and quality flag is STALE → Lesson: "Need real-time data for X"

   **Assumption Error → Model Lesson:**
   - If failure mode is Assumption Error and primary driver was wrong → Lesson: "Primary driver Y is unreliable"
   - If failure mode is Assumption Error and regime was wrong → Lesson: "Regime classification needs improvement"

   **Model Error → Model Lesson:**
   - If failure mode is Model Error and volatility was wrong → Lesson: "Volatility model needs recalibration"
   - If failure mode is Model Error and correlation was wrong → Lesson: "Correlation model needs updating"

   **Cognitive Error → Bias Lesson:**
   - If failure mode is Cognitive Error and trader ignored contradicting evidence → Lesson: "Trader exhibits confirmation bias"
   - If failure mode is Cognitive Error and trader overweighted recent evidence → Lesson: "Trader exhibits recency bias"

2. **Success Analysis Review:**
   - The system reviews all successful validations.
   - For each success, the system extracts positive lessons:
     - "Model X performed well in regime Y"
     - "Data source Z is reliable for asset class W"

3. **Lesson Scoring:**
   - Each lesson is assigned a severity score:
     ```
     Severity = (Failure_Rate × 0.40) + (Impact × 0.30) + (Frequency × 0.30)
     ```
   - Where:
     - **Failure_Rate** = Fraction of times this issue caused a failure
     - **Impact** = Average impact of failures caused by this issue
     - **Frequency** = How often this issue occurs

4. **Lesson Prioritization:**
   - Lessons are prioritized by severity score.
   - High-severity lessons (>0.70) are flagged for immediate attention.
   - Medium-severity lessons (0.40-0.70) are scheduled for review.
   - Low-severity lessons (<0.40) are archived for reference.

#### 13.6.5 Lesson Application

Lessons are applied through:
- **Automatic Updates** — High-confidence lessons trigger automatic parameter updates
- **Human Review** — Medium-confidence lessons are presented to the Human Trader
- **Training Exercises** — Bias lessons trigger targeted cognitive training
- **Process Changes** — Process lessons trigger workflow modifications

---

### 13.7 Knowledge Engine Architecture

The Knowledge Engine is designed as a modular system with five repositories and three processing modules.

```
┌─────────────────────────────────────────────────────────────┐
│  Knowledge Engine                                           │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Research    │  │ Historical  │  │ Market      │         │
│  │ Memory      │  │ Pattern     │  │ Knowledge   │         │
│  │             │  │ Library     │  │ Base        │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│        │               │               │                    │
│        ▼               ▼               ▼                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Reasoning   │  │ Lessons     │  │ Knowledge   │         │
│  │ History     │  │ Learned     │  │ Query       │         │
│  │             │  │             │  │ Interface   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│        │               │               │                    │
│        ▼               ▼               ▼                    │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Knowledge Synthesis & Distribution                  │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### 13.7.1 Module Interfaces

| Module | Input | Output |
|---|---|---|
| Research Memory | `ResearchReport`, `ValidationResult` | `ResearchMemoryEntry` |
| Historical Pattern Library | `ResearchMemoryEntry`, `ReasoningHistoryEntry` | `Pattern` |
| Market Knowledge Base | `AnalysisReport`, `Pattern`, `ValidationResult` | `KnowledgeEntry` |
| Reasoning History | `ReasoningTrace`, `ValidationResult` | `ReasoningHistoryEntry` |
| Lessons Learned | `FailureAnalysis`, `ValidationResult` | `Lesson` |
| Knowledge Synthesis | All knowledge entries | `KnowledgeSynthesis` |
| Knowledge Query | User query | `KnowledgeResponse` |

#### 13.7.2 Knowledge Population Triggers

Knowledge is populated automatically when:

1. **Research Report Generated** — New research report is archived in Research Memory
2. **Validation Completed** — Validation results are linked to memory entries
3. **Pattern Detected** — New patterns are identified and added to the library
4. **Knowledge Updated** — Market knowledge base entries are updated
5. **Lesson Extracted** — New lessons are extracted from failure analysis

#### 13.7.3 Knowledge Retrieval

Knowledge is retrieved through:
- **Direct Queries** — User-specified queries against any repository
- **Pattern Matching** — System identifies relevant patterns for current research
- **Context-Aware Recommendations** — System recommends relevant knowledge based on current context
- **Historical Analog Search** — System finds similar historical research for reference

---

### 13.8 Knowledge Engine Guarantees

#### 13.8.1 Determinism Guarantees

**K1: Input Determinism**
- All inputs to the Knowledge Engine are explicitly defined and versioned.
- Research reports, validation results, and reasoning traces are identified by deterministic UUIDs.
- Knowledge population rules are stored in version-controlled configuration files.

**K2: Rule Determinism**
- Every knowledge population rule is a fixed, explicit transformation.
- No rule involves randomness, subjective judgment, or machine learning inference.
- All pattern detection thresholds and lesson extraction criteria are fixed and documented.

**K3: Output Determinism**
- Given the same inputs and the same version of the Knowledge Engine, the same knowledge entries are guaranteed.
- A deterministic hash of each knowledge entry is computed and stored for verification.

**K4: Reproducibility**
- Every knowledge entry includes a complete trace of its source and creation rules.
- Any researcher can reproduce the knowledge entry by following the trace.
- The audit trail contains all intermediate calculations and decisions.

#### 13.8.2 Explainability Guarantees

**K5: Traceability**
- Every knowledge entry is linked to its source (research report, validation result, reasoning trace).
- Every pattern is linked to its supporting evidence entries.
- Every lesson is linked to its failure analysis.

**K6: Plain-Language Explanations**
- Every knowledge entry includes a plain-language description.
- Every pattern includes a human-readable description of the trigger and outcome.
- Every lesson includes a clear, actionable recommendation.

**K7: Right to Explanation**
- The Human Trader can request the full creation trace for any knowledge entry at any time.
- The trace includes all source references, rules applied, and decision logic.
- The trace is presented in a step-by-step, human-readable format.

**K8: Transparency of AI Contribution**
- All machine-generated knowledge entries are clearly labeled.
- The system distinguishes between human-authored knowledge and machine-extracted knowledge.
- All knowledge is produced by deterministic rules, not stochastic models.

---

### 13.9 Knowledge Engine Summary

The Knowledge Engine accumulates and manages institutional knowledge through five repositories:

1. **Research Memory** — Complete archive of research reports and validation results
2. **Historical Pattern Library** — Patterns identified from historical data and validated research
3. **Market Knowledge Base** — Structured knowledge about market behavior, relationships, and regimes
4. **Reasoning History** — Complete archive of reasoning traces and their outcomes
5. **Lessons Learned** — Actionable lessons extracted from validation failures and successes

Each repository is populated deterministically by rules that map specific inputs to structured knowledge records. The engine guarantees that every knowledge entry is reproducible, traceable, and explainable.

The Knowledge Engine feeds continuous improvement back into the system by providing:
- **Patterns** for scenario generation and narrative construction
- **Knowledge** for hypothesis formation and analysis
- **Lessons** for bias detection and process improvement
- **History** for quality assessment and training

---

*This concludes Article XIII: Knowledge Engine.*
