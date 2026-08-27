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

## Article XII: Validation Engine

> **Version:** 1.0.0
> **Status:** Phase 0 — Constitutional Foundation
> **Last Updated:** 2026-07-29
> **Determinism Guarantee:** Every validation step is a deterministic comparison between predicted and actual values using fixed rules. No validation decision involves subjective judgment or stochastic processes.
> **Explainability Guarantee:** Every validation result includes a complete trace documenting the research artifact validated, the reality data compared, the validation criteria applied, and the failure cause identified.

---

### 12.1 Overview

The Validation Engine is the component of ResearchOS that validates research outputs against actual market outcomes. It closes the scientific method loop by comparing predictions with reality, identifying why research was wrong, and updating system statistics for continuous improvement.

The validation pipeline is:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Research       │     │  Reality        │     │  Validation     │
│  Input          │────▶│  Comparison     │────▶│  Assessment     │
│  (Research #438)│     │  (Actual Data)  │     │  (Pass/Fail)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Failure        │     │  Statistics     │     │  Improvement    │
│  Cause          │────▶│  Update         │────▶│  Recommendations│
│  Analysis       │     │  (Calibration)  │     │  (Feedback)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

The pipeline consists of five stages:

1. **Research Input** — Load the research artifact to be validated
2. **Reality Comparison** — Retrieve and compare actual market outcomes
3. **Validation Assessment** — Determine if the research passed or failed
4. **Failure Cause Analysis** — Identify why research was wrong
5. **Statistics Update** — Update calibration tables and quality metrics

---

### 12.2 Stage 1: Research Input

**Input:** Research report identifier (e.g., "Research #438")
**Output:** `ValidationTarget` artifact
**Ontology Reference:** `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:STATE`

#### 12.2.1 Purpose

Load the research artifact to be validated and extract the validation targets — the specific predictions and scenarios that need to be checked against reality.

#### 12.2.2 Procedure

1. **Research Report Retrieval:**
   - The research report is retrieved from the audit trail using its identifier.
   - The report's metadata is extracted: research timestamp, time horizon, asset, methodology version.

2. **Validation Target Extraction:**
   - From the `ScenarioSet` artifact, the following targets are extracted:
     - **Scenario probabilities** — Each scenario's predicted probability
     - **Expected returns** — Each scenario's expected return
     - **Return ranges** — Each scenario's 5th and 95th percentile bounds
     - **Volatility estimates** — Each scenario's volatility
     - **Regime predictions** — Each scenario's predicted regime
     - **Validity conditions** — Each scenario's valid-if and invalid-if conditions
     - **Milestone predictions** — Each scenario's confirmation/refutation milestones

3. **Target Structuring:**
   - Each validation target is structured as:
     ```
     ValidationTarget:
       research_id:      string
       scenario_id:      string
       target_type:      [Probability | Expected_Return | Return_Range | Volatility | Regime | Condition | Milestone]
       predicted_value:  float (or string for regime/condition)
       tolerance:        float
       timeframe:        string
       horizon:          string
       status:           [Pending | Validated | Invalidated | Partial]
     ```

4. **Timeline Construction:**
   - The validation timeline is constructed based on the research time horizon:
     - **Intraday** — Validated at end of trading day
     - **Daily** — Validated at end of each trading day
     - **Weekly** — Validated at end of each week
     - **Monthly** — Validated at end of each month
     - **Quarterly** — Validated at end of each quarter

#### 12.2.3 Reasoning Trace

The reasoning trace for this stage includes:
- The research report metadata
- The validation targets extracted
- The validation timeline
- The target structuring decisions

---

### 12.3 Stage 2: Reality Comparison

**Input:** `ValidationTarget` artifact
**Output:** `RealityComparison` artifact
**Ontology Reference:** `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:STATE:REGIME`

#### 12.3.1 Purpose

Retrieve actual market outcomes and compare them against the research predictions. This is the empirical test of the scientific method.

#### 12.3.2 Procedure

1. **Reality Data Retrieval:**
   - For each validation target, the system retrieves the actual outcome from the data sources defined in Article VIII.
   - The retrieval uses the same deterministic protocol as Stage 1 of the Reasoning Engine (Article X, Section 10.2).
   - Look-ahead bias prevention: only data available at the validation timestamp is used.

2. **Comparison Execution:**
   - For each target, the predicted value is compared to the actual value:

   **Probability Targets:**
   ```
   Error = |Predicted_Probability - Actual_Outcome|
   Where Actual_Outcome = 1.0 if scenario was correct, 0.0 if incorrect
   ```

   **Expected Return Targets:**
   ```
   Error = |Predicted_Return - Actual_Return|
   Where Actual_Return is the realized return over the time horizon
   ```

   **Return Range Targets:**
   ```
   Coverage = 1.0 if Actual_Return is within [p5, p95], 0.0 otherwise
   ```

   **Volatility Targets:**
   ```
   Error = |Predicted_Volatility - Actual_Volatility|
   Where Actual_Volatility is the realized volatility over the time horizon
   ```

   **Regime Targets:**
   ```
   Match = 1.0 if Predicted_Regime == Actual_Regime, 0.0 otherwise
   ```

   **Condition Targets:**
   ```
   Trigger = 1.0 if condition was met within the time horizon, 0.0 otherwise
   ```

   **Milestone Targets:**
   ```
   Occurrence = 1.0 if milestone event occurred, 0.0 otherwise
   ```

3. **Comparison Results:**
   - Each comparison produces a `RealityComparison` artifact:
     ```
     RealityComparison:
       target_id:        string
       predicted_value:  float
       actual_value:     float
       error:            float
       within_tolerance: bool
       comparison_time:  timestamp
       data_sources:     [string]
     ```

#### 12.3.3 Reasoning Trace

The reasoning trace for this stage includes:
- The data sources retrieved
- The actual values obtained
- The comparison calculations
- The within-tolerance determinations

---

### 12.4 Stage 3: Validation Assessment

**Input:** `RealityComparison` artifact, `ValidationTarget` artifact
**Output:** `ValidationResult` artifact
**Ontology Reference:** `ONTOLOGY:STATE:REGIME`, `ONTOLOGY:RELATIONSHIP:CONFIRMS`

#### 12.4.1 Purpose

Determine whether each research prediction passed or failed validation, and assess the overall quality of the research.

#### 12.4.2 Procedure

1. **Individual Target Validation:**
   - For each validation target, the result is classified:

   **Pass Criteria:**
   - **Probability** — |Error| ≤ tolerance (default: 0.10)
   - **Expected Return** — |Error| ≤ tolerance (default: 0.05)
   - **Return Range** — Coverage = 1.0 (actual within range)
   - **Volatility** — |Error| ≤ tolerance (default: 0.03)
   - **Regime** — Match = 1.0
   - **Condition** — Trigger matches prediction
   - **Milestone** — Occurrence matches prediction

   **Fail Criteria:**
   - Any target that does not meet its pass criteria

   **Partial Criteria:**
   - Targets that partially meet criteria (e.g., return range coverage is 80% instead of 90%)

2. **Scenario-Level Validation:**
   - A scenario is classified as:
     - **Validated** — All targets pass
     - **Invalidated** — Any target fails
     - **Partial** — Some targets pass, some fail

3. **Research-Level Validation:**
   - The overall research is classified as:
     - **Accurate** — ≥70% of scenarios validated
     - **Partially Accurate** — 40-70% of scenarios validated
     - **Inaccurate** — <40% of scenarios validated

4. **Quality Scoring:**
   - The research quality score is computed using the formula from Article VII, Section 7.12:
     ```
     Quality_Score = (Accuracy × 0.40) + (Calibration × 0.30) + (Timeliness × 0.20) + (Completeness × 0.10)
     ```
   - Where:
     - **Accuracy** = Fraction of correct scenario predictions
     - **Calibration** = How well probabilities matched outcomes (1.0 - |P - Actual|)
     - **Timeliness** = How early key signals were detected (1.0 - days_late / 30)
     - **Completeness** = Fraction of evidence collected vs. available

5. **Validation Result Assembly:**
   - The `ValidationResult` artifact is assembled:
     ```
     ValidationResult:
       research_id:         string
       validation_date:     timestamp
       overall_status:      [Accurate | Partially Accurate | Inaccurate]
       quality_score:       float
       scenario_results:    [ScenarioValidationResult]
       target_results:      [TargetValidationResult]
       validation_trace:    string
     ```

#### 12.4.3 Reasoning Trace

The reasoning trace for this stage includes:
- The pass/fail determination for each target
- The scenario-level validation results
- The quality score calculation
- The overall research assessment

---

### 12.5 Stage 4: Failure Cause Analysis

**Input:** `ValidationResult` artifact, `RealityComparison` artifact
**Output:** `FailureAnalysis` artifact
**Ontology Reference:** `ONTOLOGY:RELATIONSHIP:CONTRADICTS`

#### 12.5.1 Purpose

Identify why research predictions were wrong. This is the root cause analysis that enables continuous improvement.

#### 12.5.2 Procedure

1. **Failure Identification:**
   - All failed targets are identified from the `ValidationResult`.
   - Each failure is categorized by the type of prediction that failed.

2. **Failure Mode Classification:**
   - Each failure is classified into one of four failure modes (Article IV, Section 4.2):

   **Data Error:**
   - The prediction was wrong because the input data was incorrect.
   - Indicators: Data was stale, revised, preliminary, or anomalous.
   - Detection: Check evidence quality flags and source reliability scores.

   **Assumption Error:**
   - The prediction was wrong because a key assumption was incorrect.
   - Indicators: The narrative thesis was wrong, or a dependency was violated.
   - Detection: Check if the primary driver behaved as expected.

   **Model Error:**
   - The prediction was wrong because the analytical model was inadequate.
   - Indicators: The model failed to capture a key relationship or regime shift.
   - Detection: Check if the model's assumptions were violated.

   **Cognitive Error:**
   - The prediction was wrong because of human bias or oversight.
   - Indicators: The trader ignored contradicting evidence or overweighted confirming evidence.
   - Detection: Check if the trader's decision deviated from the research recommendation.

3. **Root Cause Analysis:**
   - For each failure, the system traces back through the reasoning chain:
     - **Observation** → Was the data correct?
     - **Evidence** → Was the evidence properly weighted?
     - **Analysis** → Were the analytical dimensions correctly applied?
     - **Narrative** → Was the narrative thesis sound?
     - **Scenario** → Were the scenarios properly constructed?
     - **Confidence** → Was the confidence appropriately calibrated?

4. **Failure Severity Scoring:**
   - Each failure is assigned a severity score:
     ```
     Severity = (Probability_Error × 0.40) + (Return_Error × 0.30) + (Impact × 0.30)
     ```
   - Where:
     - **Probability_Error** = |Predicted_Probability - Actual_Outcome|
     - **Return_Error** = |Predicted_Return - Actual_Return| / |Actual_Return|
     - **Impact** = The financial impact of the error (if applicable)

5. **Failure Analysis Assembly:**
   - The `FailureAnalysis` artifact is assembled:
     ```
     FailureAnalysis:
       research_id:         string
       failures:            [FailureDetail]
       root_causes:         [RootCause]
       severity_scores:     [SeverityScore]
       improvement_areas:   [string]
       failure_trace:       string
     ```

#### 12.5.3 Reasoning Trace

The reasoning trace for this stage includes:
- The failure mode classification for each failure
- The root cause analysis for each failure
- The severity scores
- The improvement areas identified

---

### 12.6 Stage 5: Statistics Update

**Input:** `ValidationResult` artifact, `FailureAnalysis` artifact
**Output:** Updated `CalibrationTable`, `QualityMetrics`, `BiasProfile`
**Ontology Reference:** `ONTOLOGY:STATE:VOL`, `ONTOLOGY:RELATIONSHIP:REGIME_DEPENDENT`

#### 12.6.1 Purpose

Update the system's statistical models based on validation results. This ensures that the system continuously improves its calibration, quality scoring, and bias detection.

#### 12.6.2 Procedure

1. **Calibration Table Update:**
   - For each scenario type (Base, Bull, Bear, Tail), the calibration table is updated:
     - The scenario's predicted probability is assigned to a bin of width 0.1.
     - The bin's observed frequency is updated with the actual outcome.
     - The bin's count is incremented.
     - The calibration error is recomputed:
       ```
       Calibration_Error = |Bin_Midpoint - Observed_Frequency|
       ```

2. **Quality Metrics Update:**
   - The system-wide quality metrics are updated:
     - **Research Accuracy** — Updated as a moving average:
       ```
       Accuracy_MA = (Previous_Accuracy × (N-1) + New_Accuracy) / N
       ```
     - **Calibration Error** — Updated as a moving average across all bins.
     - **Timeliness** — Updated based on how early signals were detected.
     - **Completeness** — Updated based on evidence coverage.

3. **Bias Profile Update:**
   - The trader's cognitive bias profile is updated:
     - For each bias type (confirmation, anchoring, overconfidence, etc.), the frequency is tracked.
     - The bias profile is updated with any new bias instances identified in the failure analysis.
     - The bias trend is computed:
       ```
       Bias_Trend = (Current_Frequency - Previous_Frequency) / Previous_Frequency
       ```

4. **Model Performance Update:**
   - Each analytical model's performance is updated:
     - **Macro Model** — Accuracy in regime prediction
     - **Technical Model** — Accuracy in trend prediction
     - **Liquidity Model** — Accuracy in liquidity regime prediction
     - **Narrative Model** — Accuracy in primary driver identification
     - **Scenario Model** — Accuracy in scenario construction

5. **Improvement Recommendations:**
   - Based on the failure analysis, improvement recommendations are generated:
     - **Data Improvements** — Add new data sources, improve data quality
     - **Model Improvements** — Adjust model parameters, add new factors
     - **Process Improvements** — Change evidence weighting, add new checks
     - **Training Improvements** — Target specific cognitive biases for improvement

6. **Statistics Update Assembly:**
   - The updated statistics are assembled:
     ```
     StatisticsUpdate:
       research_id:         string
       calibration_updates: [CalibrationUpdate]
       quality_updates:     [QualityUpdate]
       bias_updates:        [BiasUpdate]
       model_updates:       [ModelUpdate]
       recommendations:     [Recommendation]
       update_trace:        string
     ```

#### 12.6.3 Reasoning Trace

The reasoning trace for this stage includes:
- The calibration table updates
- The quality metrics updates
- The bias profile updates
- The model performance updates
- The improvement recommendations

---

### 12.7 Validation Engine Architecture

The Validation Engine is designed as a modular pipeline where each stage is a separate, independently testable module.

```
┌─────────────────────────────────────────────────────────────┐
│  Validation Engine                                          │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Research    │  │ Reality     │  │ Validation  │         │
│  │ Input       │→ │ Comparison  │→ │ Assessment  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│        │               │               │                    │
│        ▼               ▼               ▼                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Failure     │  │ Statistics  │  │ Improvement │         │
│  │ Cause       │→ │ Update      │→ │ Feedback    │         │
│  │ Analysis    │  │             │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

#### 12.7.1 Module Interfaces

| Module | Input | Output |
|---|---|---|
| Research Input | Research report ID | `ValidationTarget` |
| Reality Comparison | `ValidationTarget` | `RealityComparison` |
| Validation Assessment | `RealityComparison`, `ValidationTarget` | `ValidationResult` |
| Failure Cause Analysis | `ValidationResult`, `RealityComparison` | `FailureAnalysis` |
| Statistics Update | `ValidationResult`, `FailureAnalysis` | Updated `CalibrationTable`, `QualityMetrics`, `BiasProfile` |

#### 12.7.2 Validation Triggers

Validation is triggered automatically when:

1. **Time Horizon Elapsed** — The research time horizon has passed.
2. **Scenario Resolved** — A scenario's validity conditions have been met or invalidated.
3. **Manual Trigger** — The Human Trader requests validation.
4. **Periodic Review** — Monthly or quarterly review of all active research.

#### 12.7.3 Error Handling

- **Missing Reality Data** — If reality data is unavailable, validation is deferred.
- **Data Discrepancies** — If multiple reality sources disagree, the most reliable source is used.
- **Incomplete Validation** — If not all targets can be validated, partial results are recorded.
- **System Errors** — All errors are logged and reported to the Human Trader.

---

### 12.8 Validation Engine Guarantees

#### 12.8.1 Determinism Guarantees

**V1: Input Determinism**
- All inputs to the validation engine are explicitly defined and versioned.
- Research reports are identified by deterministic UUIDs.
- Reality data is retrieved from fixed, version-controlled sources.

**V2: Rule Determinism**
- Every validation rule is a fixed, explicit comparison.
- No validation decision involves randomness, subjective judgment, or machine learning inference.
- All thresholds and tolerances are fixed and documented.

**V3: Output Determinism**
- Given the same research report and the same reality data, the same validation results are guaranteed.
- A deterministic hash of each validation result is computed and stored.

**V4: Reproducibility**
- Every validation result includes a complete trace of all comparisons and decisions.
- Any researcher can reproduce the validation by following the trace.
- The audit trail contains all intermediate calculations.

#### 12.8.2 Explainability Guarantees

**V5: Traceability**
- Every validation result is linked to the research artifact it validates.
- Every comparison is linked to its supporting reality data.
- Every failure cause is linked to its root cause analysis.

**V6: Plain-Language Explanations**
- Every validation result includes a plain-language summary.
- Every failure cause is explained in clear, non-technical terms.
- Every improvement recommendation is actionable and specific.

**V7: Right to Explanation**
- The Human Trader can request the full validation trace for any research report at any time.
- The trace includes all data sources, comparison calculations, and decision logic.
- The trace is presented in a step-by-step, human-readable format.

**V8: Transparency of AI Contribution**
- All machine-generated validation results are clearly labeled.
- The system distinguishes between automated validation and human review.
- All validation is performed by deterministic rules, not stochastic models.

---

### 12.9 Validation Engine Summary

The Validation Engine closes the scientific method loop in ResearchOS. It validates research outputs against actual market outcomes through a five-stage pipeline:

1. **Research Input** — Loads the research artifact and extracts validation targets
2. **Reality Comparison** — Retrieves actual outcomes and compares them to predictions
3. **Validation Assessment** — Determines pass/fail status and computes quality scores
4. **Failure Cause Analysis** — Identifies root causes of failures (data, assumption, model, cognitive errors)
5. **Statistics Update** — Updates calibration tables, quality metrics, bias profiles, and model performance

The engine guarantees that every validation is reproducible, traceable, and explainable. It feeds continuous improvement back into the system through updated statistics and improvement recommendations.

---

### 12.10 Validation Integration with Other Engines

The Validation Engine integrates with the other ResearchOS engines:

| Engine | Integration Point | Data Flow |
|---|---|---|
| **Reasoning Engine** (X) | Receives research reports for validation | Research → Validation |
| **Scenario Engine** (XI) | Validates scenario probabilities and outcomes | Scenarios → Validation |
| **Cognitive Growth Engine** (planned) | Feeds bias profiles and improvement recommendations | Validation → Cognitive Growth |
| **Market Intelligence Engine** (planned) | Receives updated calibration for future research | Validation → Intelligence |

---

*This concludes Article XII: Validation Engine. The next article (Article XIII) will define the Cognitive Growth Engine methodology.*
