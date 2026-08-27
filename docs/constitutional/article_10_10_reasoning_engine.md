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

## Article X: Reasoning Engine

> **Version:** 1.0.0
> **Status:** Phase 0 — Constitutional Foundation
> **Last Updated:** 2026-07-29
> **Determinism Guarantee:** Every reasoning step is a deterministic transformation defined by explicit rules. No inference uses stochastic processes, neural networks, or subjective judgment. Given identical inputs and rules, identical reasoning traces are guaranteed.
> **Explainability Guarantee:** Every conclusion produced by the reasoning engine is accompanied by a complete, human-readable reasoning trace that documents every transformation, every rule applied, and every piece of evidence considered.

---

### 10.1 Overview

The Reasoning Engine is the logical core of ResearchOS. It transforms raw market observations into institutional-grade research through a deterministic, seven-stage pipeline. Each stage is a pure function: it takes inputs, applies explicit rules, and produces outputs with a complete audit trail.

The reasoning pipeline is:

```
┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│  Stage 1:    │     │  Stage 2:    │     │  Stage 3:      │
│  Observation │────▶│  Evidence    │────▶│  Interpretation │
│  Collection  │     │  Formation   │     │  & Analysis     │
└──────────────┘     └──────────────┘     └────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│  Stage 4:    │     │  Stage 5:    │     │  Stage 6:      │
│  Contradiction│     │  Scenario    │     │  Confidence    │
│  Detection   │────▶│  Generation  │────▶│  Estimation    │
└──────────────┘     └──────────────┘     └────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────────────────────────────────────────────────┐
│  Stage 7: Research Report Generation                      │
│  (Assembles all prior stages into final output)          │
└──────────────────────────────────────────────────────────┘
```

Each stage produces a **Reasoning Artifact** that is stored in the audit trail (Article V, Section 5.6) and includes:
- A deterministic UUID
- The inputs consumed
- The rules applied
- The outputs produced
- A human-readable reasoning trace

---

### 10.2 Stage 1: Observation Collection

**Input:** `ResearchQuestion` artifact (Article VII, Section 7.2)
**Output:** `ObservationSet` artifact
**Ontology Reference:** `ONTOLOGY:ENTITY:DATA_PROVIDER`, `ONTOLOGY:EVENT`

#### 10.2.1 Purpose

Observation collection gathers all raw data points relevant to the research question. It is the entry point for all external information into the reasoning engine.

#### 10.2.2 Procedure

1. **Question Decomposition:**
   - The research question is decomposed into sub-questions using a fixed template engine.
   - Each sub-question is tagged with ontology concepts (entity type, geography, time horizon).
   - Sub-questions are ranked by importance using a fixed priority formula:
     ```
     Priority = (entity_importance × 0.40) + (time_horizon_weight × 0.30) + (decision_context_weight × 0.30)
     ```

2. **Source Identification:**
   - For each sub-question, the system consults the `EvidenceSourceMap` (defined in Article VIII, Section 8.1).
   - The map returns a list of data source identifiers that are relevant to the sub-question.
   - Sources are filtered by:
     - **Temporal relevance** — Only sources with data available at the research timestamp.
     - **Geographic relevance** — Only sources covering the relevant geography.
     - **Asset relevance** — Only sources covering the relevant asset class.

3. **Data Retrieval:**
   - For each source, the system retrieves data using the deterministic retrieval protocol from Article VII, Section 7.3.2.
   - Each data point is wrapped in an `Observation` object:
     ```
     Observation:
       id:             Deterministic UUID (source + timestamp + value hash)
       source:         Source identifier (e.g., "MACRO:POLICY_RATE")
       timestamp:      UTC timestamp of the observation
       value:          The raw observed value
       ontology_tags:  List of ontology concept IDs relevant to this observation
       retrieval_time: Timestamp when the data was retrieved
       retrieval_method: Fixed string identifying the retrieval procedure
       quality_flags:  List of quality flags (STALE, REVISED, etc.)
     ```

4. **Observation Validation:**
   - Each observation is validated against three criteria:
     - **Completeness** — No missing values.
     - **Timeliness** — Timestamp is before the research timestamp (look-ahead bias check).
     - **Integrity** — Value matches the expected format and range for the source.

5. **Observation Set Assembly:**
   - All valid observations are assembled into an `ObservationSet` artifact.
   - Observations are indexed by ontology tags for efficient retrieval in subsequent stages.
   - A deterministic hash of the observation set is computed and stored.

#### 10.2.3 Reasoning Trace

The reasoning trace for this stage includes:
- The decomposed sub-questions and their priorities
- The source identification decisions for each sub-question
- The data retrieval calls made (with parameters)
- The validation results for each observation
- The final observation set summary

---

### 10.3 Stage 2: Evidence Formation

**Input:** `ObservationSet` artifact, `HypothesisSet` artifact (Article VII, Section 7.2)
**Output:** `EvidenceRegistry` artifact
**Ontology Reference:** `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:STATE`, `ONTOLOGY:RELATIONSHIP`

#### 10.3.1 Purpose

Evidence formation transforms raw observations into structured, weighted evidence that can be used for analysis. It applies the evidence collection and weighting protocols from Article VII (Sections 7.3–7.4) through deterministic rules.

#### 10.3.2 Procedure

1. **Evidence Extraction:**
   - Each observation is converted into an `EvidenceEntry` using the schema from Article VII, Section 7.3.2.
   - The conversion applies fixed transformation rules:
     - **Direct observations** → Direct evidence
     - **Calculated values** → Derived evidence (with formula recorded)
     - **Market structure observations** → Structural evidence
     - **Positioning data** → Positional evidence
     - **Event occurrences** → Event evidence

2. **Evidence Linking:**
   - Each evidence entry is linked to hypotheses using the `HypothesisEvidenceLinkMap`.
   - The link map specifies which evidence is relevant to which hypothesis, based on ontology tag overlap.
   - Link strength is computed using the Jaccard similarity formula from Article VII, Section 7.4.3.

3. **Evidence Weighting:**
   - Each evidence entry is assigned a weight using the five-factor formula from Article VII, Section 7.4.6:
     ```
     W = SR × RE × RL × CS × SI × QF
     ```
   - Each factor is computed from fixed tables and deterministic formulas:
     - **SR** (Source Reliability) — From the `SourceReliabilityTable` (Article VIII, Section 8.4)
     - **RE** (Recency) — From the freshness formula in Article VII, Section 7.3.4
     - **RL** (Relevance) — From the Jaccard similarity in Article VII, Section 7.4.3
     - **CS** (Consensus) — From the consensus formula in Article VII, Section 7.4.4
     - **SI** (Structural Importance) — From the `StructuralImportanceTable` (Article VII, Section 7.4.5)
     - **QF** (Quality Factor) — From the quality flag multipliers in Article VII, Section 7.3.3

4. **Evidence Aggregation:**
   - For each hypothesis, evidence is aggregated into an Evidence Score using the formula from Article VII, Section 7.4.7:
     ```
     ES = Σ(W_i × D_i) / Σ(W_i)
     ```
   - The confidence in the Evidence Score is computed as:
     ```
     EC = Σ(W_i) / N
     ```

5. **Evidence Registry Assembly:**
   - All evidence entries are assembled into an `EvidenceRegistry` artifact.
   - Entries are indexed by hypothesis ID and ontology tags.
   - A deterministic hash of the registry is computed and stored.

#### 10.3.3 Reasoning Trace

The reasoning trace for this stage includes:
- The evidence extraction rules applied to each observation
- The hypothesis linking decisions and their rationale
- The weight calculation for each evidence entry (with all factor values)
- The aggregation results for each hypothesis
- The final evidence registry summary

---

### 10.4 Stage 3: Interpretation & Analysis

**Input:** `EvidenceRegistry` artifact
**Output:** `AnalysisReport` artifact (containing MacroAnalysis, TechnicalAnalysis, LiquidityAnalysis)
**Ontology Reference:** `ONTOLOGY:STATE:TREND`, `ONTOLOGY:STATE:VOL`, `ONTOLOGY:STATE:LIQUIDITY`, `ONTOLOGY:STATE:REGIME`

#### 10.4.1 Purpose

Interpretation & Analysis applies the three analytical dimensions (macro, technical, liquidity) to the evidence, producing structured analysis results. Each dimension operates independently but shares evidence through the ontology.

#### 10.4.2 Procedure

The procedure is divided into three parallel sub-stages, one for each analytical dimension. Each sub-stage follows the same general structure:

**Sub-Stage 3A: Macro Analysis** (Article VII, Section 7.5)

1. **Dimension Filtering:**
   - Evidence entries tagged with macro-related ontology concepts are selected.
   - Tags include: `ONTOLOGY:ENTITY:PARTICIPANT:CENTRAL_BANK`, `ONTOLOGY:EVENT:ECONOMIC_RELEASE`, `ONTOLOGY:STATE:REGIME`

2. **Indicator Computation:**
   - For each macro indicator (inflation, growth, policy stance), the system computes:
     - The current value (from the most recent evidence)
     - The trend (from the directional signals of multiple evidence entries)
     - The percentile (from historical context, if available)

3. **Regime Classification:**
   - The macro regime is classified using the deterministic decision tree from Article VII, Section 7.5.2.
   - The classification produces:
     - The regime type (Stagflation, Reflation, Expansion, Deflationary Slump)
     - A confidence score for the classification
     - The evidence supporting and contradicting the classification

4. **Risk Factor Identification:**
   - Macro risk factors are identified using the procedure from Article VII, Section 7.5.4.
   - Each risk factor is assigned a severity score.

**Sub-Stage 3B: Technical Analysis** (Article VII, Section 7.6)

1. **Dimension Filtering:**
   - Evidence entries tagged with technical-related ontology concepts are selected.
   - Tags include: `ONTOLOGY:STATE:TREND`, `ONTOLOGY:STATE:VOL`, `ONTOLOGY:ENTITY:INSTRUMENT`

2. **Trend Computation:**
   - The trend score is computed using the three-component formula from Article VII, Section 7.6.1:
     ```
     TS = (MA_trend × 0.40) + (structure_score × 0.35) + (momentum_strength × 0.25)
     ```

3. **Regime Classification:**
   - The technical regime is classified using the 2×3 matrix from Article VII, Section 7.6.2.
   - Support/resistance levels are mapped using the procedure from Article VII, Section 7.6.3.
   - Volatility is profiled using the procedure from Article VII, Section 7.6.4.
   - Volume dynamics are analyzed using the procedure from Article VII, Section 7.6.5.
   - Patterns are recognized using the deterministic rules from Article VII, Section 7.6.6.

**Sub-Stage 3C: Liquidity Analysis** (Article VII, Section 7.7)

1. **Dimension Filtering:**
   - Evidence entries tagged with liquidity-related ontology concepts are selected.
   - Tags include: `ONTOLOGY:STATE:LIQUIDITY`, `ONTOLOGY:ENTITY:PARTICIPANT`

2. **Order Flow Analysis:**
   - Order flow imbalance is computed using the formula from Article VII, Section 7.7.1.
   - Trade size distribution and timing are analyzed.

3. **Depth Assessment:**
   - Market depth is assessed using the procedures from Article VII, Section 7.7.2.
   - Liquidity concentration is measured using the Herfindahl-Hirschman Index.

4. **Positioning Analysis:**
   - Institutional positioning is analyzed using the COT data procedures from Article VII, Section 7.7.3.
   - Positioning extremes and divergences are identified.

5. **Regime Classification:**
   - The liquidity regime is classified using the procedure from Article VII, Section 7.7.4.
   - Transaction costs are analyzed using the procedure from Article VII, Section 7.7.5.

#### 10.4.3 Reasoning Trace

The reasoning trace for this stage includes:
- The evidence filtering decisions for each dimension
- The indicator computations with all input values
- The regime classification decisions and their rationale
- The risk factor identifications
- The analysis results for each dimension

---

### 10.5 Stage 4: Contradiction Detection

**Input:** `AnalysisReport` artifact, `EvidenceRegistry` artifact
**Output:** `ContradictionReport` artifact
**Ontology Reference:** `ONTOLOGY:RELATIONSHIP:CONTRADICTS`, `ONTOLOGY:RELATIONSHIP:REGIME_DEPENDENT`

#### 10.5.1 Purpose

Contradiction detection identifies conflicts between evidence, analyses, and scenarios. It ensures that the reasoning engine does not produce conclusions that are internally inconsistent.

#### 10.5.2 Procedure

1. **Cross-Dimensional Contradiction Check:**
   - The directional signals from Macro, Technical, and Liquidity analyses are compared.
   - A contradiction is flagged when analyses disagree (per Article VII, Section 7.11.2).
   - Severity is computed as:
     ```
     Severity = (n_disagree / n_total) × average_weight_of_disagreeing_evidence
     ```

2. **Temporal Contradiction Check:**
   - Evidence from the most recent 10% of the look-back period is compared with earlier evidence.
   - Contradictions are flagged when directional signals differ.

3. **Source Contradiction Check:**
   - Evidence entries from different sources with the same semantic meaning are compared.
   - Contradictions are flagged when values differ beyond predefined thresholds.

4. **Narrative Contradiction Check:**
   - Evidence in the narrative's evidence base is checked against the narrative thesis.
   - Contradictions are flagged when evidence contradicts the thesis.

5. **Scenario Contradiction Check:**
   - Scenario validity conditions are checked for overlaps.
   - Contradictions are flagged when mutually exclusive scenarios can both be valid.

6. **Historical Contradiction Check:**
   - Scenarios are compared against historical precedent.
   - Contradictions are flagged when historical outcomes consistently disagree.

7. **Resolution:**
   - Automatic resolution is attempted when one side has ≥2× the evidence weight of the other.
   - Unresolved contradictions are flagged for human review.
   - All contradictions reduce the confidence of affected conclusions.

#### 10.5.3 Reasoning Trace

The reasoning trace for this stage includes:
- Each contradiction check performed and its result
- The evidence on each side of each contradiction
- The resolution decisions and their rationale
- The confidence impact of each contradiction

---

### 10.6 Stage 5: Scenario Generation

**Input:** `AnalysisReport` artifact, `EvidenceRegistry` artifact, `ContradictionReport` artifact
**Output:** `ScenarioSet` artifact
**Ontology Reference:** `ONTOLOGY:STATE`, `ONTOLOGY:EVENT`, `ONTOLOGY:RELATIONSHIP`

#### 10.6.1 Purpose

Scenario generation produces a set of probabilistic future market states, each with defined validity and invalidity conditions. Scenarios are generated deterministically from the analysis results, evidence, and narrative.

#### 10.6.2 Procedure

1. **Base Scenario Construction:**
   - The base scenario is constructed from the narrative thesis (Article VII, Section 7.8).
   - The probability is computed using the formula from Article VII, Section 7.9.2:
     ```
     P_base = (evidence_strength × 0.50) + (coherence_score × 0.30) + (plausibility_score × 0.20)
     ```

2. **Bull/Bear Scenario Construction:**
   - The bull scenario assumes the primary driver is stronger than the base case.
   - The bear scenario assumes the primary driver is weaker or reversed.
   - Probabilities are computed using the formulas from Article VII, Section 7.9.2.

3. **Tail Scenario Generation:**
   - Tail scenarios are generated from the narrative's invalidation conditions.
   - Each invalidation condition becomes a tail scenario.
   - Probabilities are assigned based on historical frequency.

4. **Outcome Specification:**
   - Each scenario specifies:
     - Expected return (point estimate)
     - Return range (5th–95th percentile)
     - Volatility (expected standard deviation)
     - Key milestones (events that confirm/refute)
     - Market regime (from ontology)

5. **Validity Condition Definition:**
   - Valid-if conditions are derived from supporting evidence.
   - Invalid-if conditions are derived from contradicting evidence.
   - Conditions are formatted using the schema from Article VII, Section 7.9.3.

6. **Probability Normalization:**
   - All scenario probabilities are normalized to sum to 1.0.
   - Adjustments are made to the base scenario probability if needed.

#### 10.6.3 Reasoning Trace

The reasoning trace for this stage includes:
- The narrative thesis used as the base scenario
- The probability calculations for each scenario
- The validity/invalidity conditions and their derivation
- The outcome specifications and their rationale
- The normalization adjustments

---

### 10.7 Stage 6: Confidence Estimation

**Input:** `ScenarioSet` artifact, `EvidenceRegistry` artifact, `ContradictionReport` artifact
**Output:** `ConfidenceReport` artifact
**Ontology Reference:** `ONTOLOGY:STATE:VOL`, `ONTOLOGY:RELATIONSHIP:REGIME_DEPENDENT`

#### 10.7.1 Purpose

Confidence estimation assigns probability estimates to scenarios and conclusions, along with explicit uncertainty ranges. All estimates are calibrated against historical data.

#### 10.7.2 Procedure

1. **Confidence Factor Computation:**
   - For each scenario, five confidence factors are computed (Article VII, Section 7.10.2):
     - **Evidence Strength (ES)** — Total weighted evidence supporting the scenario
     - **Coherence (CO)** — Agreement across analytical dimensions
     - **Historical Precedent (HP)** — How often similar scenarios were correct
     - **Model Uncertainty (MU)** — Confidence in the analytical models used
     - **Recency (RE)** — How recent the supporting evidence is

2. **Composite Confidence Calculation:**
   - The composite confidence is computed using the formula from Article VII, Section 7.10.2:
     ```
     C = (ES × 0.30) + (CO × 0.25) + (HP × 0.20) + (MU × 0.15) + (RE × 0.10)
     ```

3. **Confidence Interval Computation:**
   - The confidence interval is computed using the formula from Article VII, Section 7.10.3:
     ```
     CI = C ± (1.0 − C) × z × σ
     ```
   - Where z = 1.96 (for 95% confidence) and σ = sqrt(C × (1 − C) / N)

4. **Calibration Adjustment:**
   - The calibration table is consulted (Article VII, Section 7.10.4).
   - If the scenario's probability falls in a bin with observed frequency differing by >0.05, a calibration adjustment is applied.

5. **Contradiction Impact:**
   - Unresolved contradictions reduce the confidence score of affected scenarios.
   - The reduction is proportional to the contradiction severity.

#### 10.7.3 Reasoning Trace

The reasoning trace for this stage includes:
- The confidence factor values for each scenario
- The composite confidence calculation
- The confidence interval computation
- The calibration adjustments applied
- The contradiction impact on confidence

---

### 10.8 Stage 7: Research Report Generation

**Input:** All preceding artifacts (`ObservationSet`, `EvidenceRegistry`, `AnalysisReport`, `ContradictionReport`, `ScenarioSet`, `ConfidenceReport`)
**Output:** `ResearchReport` artifact
**Ontology Reference:** All ontology concepts

#### 10.8.1 Purpose

Research report generation assembles all prior reasoning artifacts into a structured, auditable report. The report is the final output of the reasoning engine and is designed for human review and decision-making.

#### 10.8.2 Procedure

1. **Template Selection:**
   - A report template is selected based on the research question type.
   - Templates are fixed, version-controlled documents (Article VII, Section 7.12.3).

2. **Section Population:**
   - Each section is populated deterministically from the corresponding artifact:
     - **Metadata** — From the research question and system state
     - **Executive Summary** — Computed from scenario probabilities and confidence
     - **Research Question** — Verbatim from the input
     - **Hypotheses** — From the `HypothesisSet`
     - **Evidence Summary** — From the `EvidenceRegistry`
     - **Analyses** — From the `AnalysisReport`
     - **Narrative** — From the narrative construction
     - **Scenarios** — From the `ScenarioSet`
     - **Confidence** — From the `ConfidenceReport`
     - **Contradictions** — From the `ContradictionReport`
     - **Validation Plan** — From the validation integration (Article VII, Section 7.13)

3. **Cross-Reference Validation:**
   - All cross-references (evidence IDs, scenario IDs, etc.) are validated for consistency.
   - Any inconsistency is flagged as an error.

4. **Quality Check:**
   - The system checks that:
     - All hypotheses have supporting evidence
     - All scenarios have validity conditions
     - All confidence estimates have intervals
     - All contradictions are documented

5. **Reasoning Trace Assembly:**
   - The reasoning traces from all prior stages are assembled into a complete audit trail.
   - The trace is included as an appendix to the report.

6. **Final Assembly:**
   - The report is assembled in the specified format (Markdown, PDF, or JSON).
   - A deterministic hash of the report content is computed and stored.
   - The report is stored in the audit trail.

#### 10.8.3 Reasoning Trace

The reasoning trace for this stage includes:
- The template selection decision
- The section population decisions
- The cross-reference validation results
- The quality check results
- The final report hash

---

### 10.9 Reasoning Engine Architecture

The reasoning engine is designed as a modular pipeline where each stage is a separate, independently testable module.

```
┌─────────────────────────────────────────────────────────────┐
│  Reasoning Engine                                           │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ Observation │  │ Evidence    │  │ Interpretation  │   │
│  │ Collector   │→ │ Formulator  │→ │ & Analysis        │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
│        │               │                 │                │
│        ▼               ▼                 ▼                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ Contradiction│  │ Scenario    │  │ Confidence      │   │
│  │ Detector   │→ │ Generator   │→ │ Estimator       │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
│        │               │                 │                │
│        ▼               ▼                 ▼                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Research Report Generator                            │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### 10.9.1 Module Interfaces

Each module communicates through well-defined interfaces:

| Module | Input Interface | Output Interface |
|---|---|---|
| Observation Collector | `ResearchQuestion` | `ObservationSet` |
| Evidence Formulator | `ObservationSet`, `HypothesisSet` | `EvidenceRegistry` |
| Interpretation & Analysis | `EvidenceRegistry` | `AnalysisReport` |
| Contradiction Detector | `AnalysisReport`, `EvidenceRegistry` | `ContradictionReport` |
| Scenario Generator | `AnalysisReport`, `EvidenceRegistry`, `ContradictionReport` | `ScenarioSet` |
| Confidence Estimator | `ScenarioSet`, `EvidenceRegistry`, `ContradictionReport` | `ConfidenceReport` |
| Report Generator | All artifacts | `ResearchReport` |

#### 10.9.2 Error Handling

Each module handles errors deterministically:

- **Data Errors** — Invalid observations are flagged and excluded from analysis.
- **Logic Errors** — Impossible states are flagged and reported.
- **Missing Data** — Missing evidence is noted and confidence is reduced.
- **Contradiction Errors** — Contradictions are detected and flagged.

All errors are recorded in the reasoning trace and included in the final report.

---

### 10.10 Reasoning Engine Guarantees

#### 10.10.1 Determinism Guarantees

**R1: Input Determinism**
- All inputs to the reasoning engine are explicitly defined and versioned.
- Data sources are identified by fixed URIs (Article VIII).
- Parameters are stored in version-controlled configuration files.

**R2: Rule Determinism**
- Every rule in the reasoning engine is defined as a fixed, explicit transformation.
- No rule involves randomness, subjective judgment, or machine learning inference.
- All formulas use fixed coefficients and thresholds.

**R3: Output Determinism**
- Given the same inputs and the same version of the reasoning engine, the same outputs are guaranteed.
- A deterministic hash of each output is computed and stored for verification.
- Any change to inputs or rules produces a different hash, indicating a change in output.

**R4: Reproducibility**
- Every research report includes a complete list of inputs, rules, and engine version.
- Any researcher can reproduce the report by following the same reasoning trace.
- The audit trail contains all intermediate artifacts and reasoning traces.

#### 10.10.2 Explainability Guarantees

**R5: Traceability**
- Every conclusion in the research report is linked to its supporting evidence through the reasoning trace.
- Every evidence entry is linked to its source and collection method.
- Every weight is linked to its calculation factors.
- Every probability is linked to its contributing factors.

**R6: Plain-Language Explanations**
- Every technical term is defined in the glossary (Article IV).
- Every calculation is explained in plain language alongside the formula.
- Every conclusion includes a "Why this conclusion?" section that explains the reasoning.

**R7: Right to Explanation**
- The Human Trader can request an explanation of any conclusion at any time.
- The system provides a step-by-step trace from the conclusion to its supporting evidence.
- The explanation includes the weights, factors, and formulas used.

**R8: Transparency of AI Contribution**
- All machine-generated reasoning is clearly labeled.
- The system distinguishes between human-authored and machine-generated content.
- All machine-generated content is produced by deterministic rules, not stochastic models.

---

### 10.11 Reasoning Engine Summary

The Reasoning Engine is the logical core of ResearchOS. It transforms raw market observations into institutional-grade research through a deterministic, seven-stage pipeline:

1. **Observation Collection** — Gathers all relevant data from identified sources.
2. **Evidence Formation** — Converts observations into weighted, structured evidence.
3. **Interpretation & Analysis** — Applies macro, technical, and liquidity analysis.
4. **Contradiction Detection** — Identifies and resolves conflicts between evidence and analyses.
5. **Scenario Generation** — Produces probabilistic scenarios with validity conditions.
6. **Confidence Estimation** — Assigns calibrated probability estimates with uncertainty ranges.
7. **Research Report Generation** — Assembles all outputs into a structured, auditable report.

Each stage is a deterministic transformation that produces a complete reasoning trace. The engine guarantees that every output is reproducible, traceable, and explainable.

---

*This concludes Article X: Reasoning Engine. The next article (Article XI) will define the Research Validation methodology.*
