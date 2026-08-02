# ResearchOS — Constitution

## Article XIV: Cognitive Growth Engine

> **Version:** 1.0.0
> **Status:** Phase 0 — Constitutional Foundation
> **Last Updated:** 2026-07-29
> **Determinism Guarantee:** Every cognitive measurement is computed using fixed, deterministic rules applied to observable trader behavior.
> **Explainability Guarantee:** Every cognitive assessment includes a complete trace documenting the specific behaviors measured, the rules applied, and the evidence supporting each score.

---

### 14.1 Overview

The Cognitive Growth Engine is the component of ResearchOS that measures, tracks, and improves the Human Trader's cognitive capabilities. It is the third engine in the ResearchOS architecture (Article V, Section 5.4).

The engine measures six cognitive dimensions:

| Dimension | Description |
|---|---|
| **Knowledge** | Depth and accuracy of market understanding |
| **Reasoning** | Quality and rigor of decision process |
| **Bias** | Presence and frequency of cognitive biases |
| **Discipline** | Adherence to systematic research processes |
| **Reflection** | Ability to learn from past decisions |
| **Learning Progress** | Trajectory of cognitive improvement over time |

### 14.2 Knowledge Measurement

**Purpose:** Assesses the trader's depth and accuracy of market understanding across 6 domains (Macro Policy, Technical Structure, Liquidity Dynamics, Cross-Market Relationships, Risk Management, Research Process).

**Procedure:**
1. **Domain Scoring** — For each domain, score based on:
   - Research Question Quality: `(Specificity × 0.40) + (Testability × 0.35) + (Relevance × 0.25)`
   - Evidence Selection: `(Relevant_Selected / Total_Available) × (Correct_Weighting / Total_Weight)`
   - Concept Application: `Correct_Applications / Total_Attempts`
2. **Domain Knowledge Score:** `(Question_Quality × 0.30) + (Evidence_Selection × 0.35) + (Concept_Application × 0.35)`
3. **Overall Knowledge:** Weighted average across domains (Macro 0.25, Technical 0.20, Liquidity 0.15, Cross-Market 0.15, Risk 0.15, Process 0.10)
4. **Growth Tracking:** Moving average with growth rate = `(Current - Previous) / Previous`

### 14.3 Reasoning Measurement

**Purpose:** Assesses the quality and rigor of the trader's decision process, independent of outcome.

**Procedure:**
1. **5 Dimensions scored (0.0–1.0 each):**
   - **Logical Structure:** `(Steps_Identified / Total_Needed) × Completeness_Factor`
   - **Completeness:** `Evidence_Types_Considered / Evidence_Types_Available`
   - **Evidence Integration:** `1.0 - (|Trader_Weight - Optimal_Weight| / Optimal_Weight)`
   - **Multi-Factor Analysis:** `min(1.0, Dimensions_Used / 2.0)`
   - **Conclusion Validity:** `Supporting_Evidence / Total_Evidence`
2. **Composite Score:** `(Structure × 0.20) + (Completeness × 0.20) + (Integration × 0.25) + (MultiFactor × 0.20) + (Validity × 0.15)`
3. **Tracking:** Moving average with linear regression trend analysis

### 14.4 Bias Measurement

**Purpose:** Identifies and quantifies 8 cognitive biases in the trader's decision-making.

**Procedure:**
1. **Bias Types Tracked:** Confirmation, Anchoring, Overconfidence, Recency, Availability, Survivorship, Hindsight, Loss Aversion
2. **Detection Rules (examples):**
   - **Confirmation Bias:** `|Questions_Bullish - Questions_Bearish| / Total_Questions`
   - **Anchoring:** `|Initial_Weight - Final_Weight| / Initial_Weight`
   - **Overconfidence:** `Trader_Confidence - Actual_Accuracy`
   - **Recency Bias:** `Recent_Weight / (Recent_Weight + Older_Weight)`
3. **Frequency Scoring:** `(Bias_Occurrences / Total_Decisions) × 100`
4. **Trend Analysis:** `(Current_Frequency - Previous_Frequency) / Previous_Frequency`
5. **Flagging:** Frequency > 20% triggers attention

### 14.5 Discipline Measurement

**Purpose:** Measures the trader's adherence to systematic research processes.

**Procedure:**
1. **5 Dimensions:**
   - **Process Adherence:** `Lifecycle_Steps_Completed / Total_Steps_Required`
   - **Evidence Requirement:** `min(1.0, Evidence_Collected / Minimum_Required)`
   - **Validation Compliance:** `Validations_Reviewed / Validations_Available`
   - **Contradiction Resolution:** `Contradictions_Addressed / Contradictions_Identified`
   - **Reflection Practice:** `Reflection_Entries / Decisions_Made`
2. **Composite Score:** `(Process × 0.25) + (Evidence × 0.20) + (Validation × 0.20) + (Contradiction × 0.20) + (Reflection × 0.15)`

### 14.6 Reflection Measurement

**Purpose:** Assesses the trader's ability to learn from past decisions.

**Procedure:**
1. **4 Dimensions:**
   - **Depth:** `Analysis_Points / Maximum_Points`
   - **Accuracy:** `Correct_Causes / Total_Causes_Identified`
   - **Actionability:** `Actionable_Items / Total_Items`
   - **Consistency:** `1.0 - (|Trader_Assessment - Validation_Assessment| / Validation_Assessment)`
2. **Composite Score:** `(Depth × 0.30) + (Accuracy × 0.30) + (Actionability × 0.25) + (Consistency × 0.15)`

### 14.7 Learning Progress Measurement

**Purpose:** Tracks the trader's cognitive improvement over time.

**Procedure:**
1. **6 Dimensions tracked:** Knowledge Growth, Reasoning Improvement, Bias Reduction, Discipline Improvement, Reflection Quality, Overall Performance
2. **Progress Formulas:**
   - Growth: `(Current - Baseline) / Baseline`
   - Bias Reduction: `(Baseline_Bias - Current_Bias) / Baseline_Bias`
   - Performance: `(Current_Accuracy - Baseline_Accuracy) / (1.0 - Baseline_Accuracy)`
3. **Trajectory Analysis:** Linear regression slope of (Score vs. Time)
4. **Classification:** Accelerating, Steady, Decelerating, Plateauing

### 14.8 Cognitive Growth Engine Architecture

```
┌─────────────────────────────────────────────────────┐
│  Cognitive Growth Engine                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Knowledge│ │Reasoning │ │ Bias     │ │Discipline│ │
│  │ Measure  │ │ Measure  │ │ Measure  │ │ Measure  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │ Reflection│ │Learning  │ │ Synthesis & Feedback│ │
│  │ Measure  │ │ Progress │ │ Generation          │ │
│  └──────────┘ └──────────┘ └──────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Module Interfaces:**
| Module | Input | Output |
|---|---|---|
| Knowledge Measurement | Research questions, evidence selection | `KnowledgeScore` |
| Reasoning Measurement | Reasoning traces, evidence weights | `ReasoningScore` |
| Bias Measurement | Decisions, evidence weighting | `BiasProfile` |
| Discipline Measurement | Lifecycle progress, evidence collection | `DisciplineScore` |
| Reflection Measurement | Reflection entries, validation results | `ReflectionScore` |
| Learning Progress | All cognitive scores over time | `LearningProgress` |
| Synthesis | All cognitive scores | `CognitiveAssessment` |

**Measurement Triggers:** Research completed, decision made, validation completed, periodic review (monthly)

### 14.9 Cognitive Growth Engine Guarantees

**Determinism (C1-C4):**
- C1: All inputs are explicitly defined and versioned
- C2: Every measurement rule is a fixed, explicit transformation
- C3: Given same inputs and engine version, same scores are guaranteed
- C4: Every assessment includes a complete trace for reproducibility

**Explainability (C5-C8):**
- C5: Every score is linked to specific trader behaviors
- C6: Every assessment includes plain-language explanations
- C7: Full measurement trace available on request
- C8: All machine-generated assessments are clearly labeled

### 14.11 Integration with Other Engines

| Engine | Integration Point | Data Flow |
|---|---|---|
| Reasoning Engine (X) | Receives reasoning traces | Reasoning → Cognitive |
| Validation Engine (XII) | Receives validation results | Validation → Cognitive |
| Knowledge Engine (XIII) | Receives lessons learned | Knowledge → Cognitive |
| Market Intelligence (planned) | Receives cognitive assessments | Cognitive → Intelligence |
>>>>>>>


---

### 14.10 Cognitive Growth Engine Summary

The Cognitive Growth Engine measures and improves the Human Trader's cognitive capabilities through six dimensions. Each dimension is measured using fixed, deterministic rules applied to observable trader behavior. The engine generates actionable feedback and training recommendations.

The engine guarantees that every cognitive assessment is reproducible, traceable, and explainable.

---

*This concludes Article XIV: Cognitive Growth Engine.*
