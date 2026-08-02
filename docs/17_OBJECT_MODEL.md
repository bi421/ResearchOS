# ResearchOS — Object Model

> **Version:** 1.0.0
> **Status:** Phase 0 — Constitutional Foundation
> **Classification:** Data Specification

---

## 1. Overview

This document defines every object type in ResearchOS. Each object is a structured data entity with well-defined properties, relationships, and lifecycle. All objects are deterministic, version-controlled, and traceable.

Objects are organized by the reasoning layer they belong to:

| Layer | Objects |
|---|---|
| **Observation** | Observation, MarketState, MacroState |
| **Evidence** | Evidence, EvidenceRegistry |
| **Interpretation** | Narrative, Interpretation |
| **Hypothesis** | Hypothesis, HypothesisSet |
| **Scenario** | Scenario, ScenarioSet |
| **Confidence** | Confidence, ConfidenceReport |
| **Contradiction** | Contradiction, ContradictionReport |
| **Decision Support** | Research, ResearchReport, ResearchQuestion |
| **Knowledge** | Knowledge, Pattern, Lesson |
| **Validation** | Validation, FailureAnalysis |
| **Cognitive** | Bias, LearningRecord, CognitiveAssessment |
| **Process** | ResearchCycle, ReasoningChain, AuditEntry |

---

## 2. Observation Layer Objects

### 2.1 Observation

**Purpose:** The atomic unit of market data. A single, objectively verifiable data point.

```
Observation:
  id:              string (deterministic UUID)
  source:          string (source identifier, e.g., "MACRO:CPI_YOY")
  timestamp:       timestamp (UTC)
  value:           any (raw observed value)
  unit:            string (e.g., "percent", "USD", "index")
  frequency:       string (e.g., "daily", "monthly", "real-time")
  geography:       string (e.g., "US", "Global", "EMU")
  asset_class:     string (e.g., "Equity", "Fixed Income", "FX", "Commodity")
  quality_flags:   [string] (e.g., ["STALE", "PRELIMINARY"])
  retrieval_time:  timestamp (when data was retrieved)
  retrieval_method: string (fixed retrieval procedure identifier)
  ontology_tags:   [string] (ontology concept IDs)
  validated:       bool (whether validation passed)
```

**Relationships:** Belongs to ObservationRegistry; Referenced by Evidence; Tagged by OntologyConcept.
**Lifecycle:** Created → Validated → Archived (immutable)

### 2.2 MarketState

**Purpose:** A snapshot of market conditions at a specific point in time.

```
MarketState:
  id:              string (deterministic UUID)
  timestamp:       timestamp (UTC)
  asset:           string (asset identifier)
  regime:          string (e.g., "Expansion", "Stagflation")
  trend:           string (e.g., "Uptrend", "Downtrend", "Range")
  volatility:      float (current volatility level)
  liquidity:       string (e.g., "High", "Normal", "Low")
  sentiment:       float (sentiment score, 0.0-1.0)
  observations:    [Observation.id]
  confidence:      float (0.0-1.0)
```

**Relationships:** Composed of Observations; Referenced by Evidence; Used by Narrative.
**Lifecycle:** Created → Updated → Superseded → Archived

### 2.3 MacroState

**Purpose:** A snapshot of macroeconomic conditions.

```
MacroState:
  id:              string (deterministic UUID)
  timestamp:       timestamp (UTC)
  geography:       string (e.g., "US", "Global")
  regime:          string (e.g., "Expansion", "Stagflation")
  inflation:       float (inflation rate)
  growth:          float (GDP growth rate)
  policy_stance:   string (e.g., "Accommodative", "Restrictive")
  risk_factors:    [string]
  observations:    [Observation.id]
  confidence:      float (0.0-1.0)
```

**Relationships:** Composed of Observations; Referenced by Evidence; Used by Narrative.
**Lifecycle:** Created → Updated → Superseded → Archived

---

## 3. Evidence Layer Objects

### 3.1 Evidence

**Purpose:** An observation that has been interpreted and contextualized to support or contradict a hypothesis.

```
Evidence:
  id:              string (deterministic UUID)
  observation_id:  string (link to source Observation)
  hypothesis_id:   string (link to Hypothesis)
  interpretation:  string (how the observation is interpreted)
  direction:       string (e.g., "Supporting", "Contradicting", "Neutral")
  quality:         float (0.0-1.0, computed from 6 factors)
  confidence:      float (0.0-1.0, quality × (1 - uncertainty))
  weight:          float (relative importance, 0.0-1.0)
  tier:            string (e.g., "Primary", "Secondary", "Tertiary")
  age_days:        int (days since observation)
  aging_multiplier: float (weight reduction for age)
  dependencies:    [string] (other evidence IDs)
  conflicts:       [string] (conflicting evidence IDs)
  created_at:      timestamp
  last_updated:    timestamp
  ontology_tags:   [string]
```

**Relationships:** References Observation; References Hypothesis; Referenced by Interpretation, Confidence, Contradiction.
**Lifecycle:** Created → Weighted → Linked → Aged → Retired

### 3.2 EvidenceRegistry

**Purpose:** A collection of all evidence for a research cycle.

```
EvidenceRegistry:
  id:              string (deterministic UUID)
  research_id:     string (link to Research)
  evidence:        [Evidence.id]
  total_weight:    float
  supporting_weight: float
  contradicting_weight: float
  created_at:      timestamp
  last_updated:    timestamp
  registry_hash:   string
```

**Relationships:** Belongs to Research; Contains Evidence.
**Lifecycle:** Created → Updated → Finalized → Archived

---

## 4. Interpretation Layer Objects

### 4.1 Interpretation

**Purpose:** The application of deterministic rules to evidence to produce market understanding.

```
Interpretation:
  id:              string (deterministic UUID)
  evidence_ids:    [string]
  rule_applied:    string
  context:         string (temporal, regime, geopolitical, seasonal)
  conclusion:      string
  confidence:      float (0.0-1.0)
  supporting_evidence: [string]
  contradicting_evidence: [string]
  alternatives:    [string]
  unknowns:        [string]
  created_at:      timestamp
  ontology_tags:   [string]
```

**Relationships:** References Evidence; Referenced by Hypothesis, Narrative.
**Lifecycle:** Created → Reviewed → Refined → Superseded → Archived

### 4.2 Narrative

**Purpose:** A coherent story that explains market conditions based on interpretations.

```
Narrative:
  id:              string (deterministic UUID)
  research_id:     string
  thesis:          string
  primary_driver:  string
  supporting_drivers: [string]
  interpretations: [Interpretation.id]
  evidence_strength: float (0.0-1.0)
  coherence_score:  float (0.0-1.0)
  plausibility_score: float (0.0-1.0)
  invalidation_conditions: [Condition]
  catalysts:       [string]
  confidence:      float (0.0-1.0)
  created_at:      timestamp
  last_updated:    timestamp
  status:          string (e.g., "Active", "Superseded", "Invalidated")
```

**Relationships:** Belongs to Research; Contains Interpretation; Referenced by Hypothesis, Scenario.
**Lifecycle:** Created → Active → Updated → Superseded/Invalidated → Archived

---

## 5. Hypothesis Layer Objects

### 5.1 Hypothesis

**Purpose:** A testable prediction about market behavior.

```
Hypothesis:
  id:              string (deterministic UUID)
  research_id:     string
  type:            string (e.g., "Primary", "Alternative", "Null", "Tail")
  statement:       string
  narrative_id:    string
  evidence_ids:    [string]
  evidence_strength: float (0.0-1.0)
  coherence:       float (0.0-1.0)
  plausibility:    float (0.0-1.0)
  falsifiability:  float (0.0-1.0)
  rank_score:      float
  confidence:      float (0.0-1.0)
  valid_if:        [Condition]
  invalid_if:      [Condition]
  monitoring_conditions: [Condition]
  created_at:      timestamp
  last_updated:    timestamp
  status:          string (e.g., "Active", "Invalidated", "Retired")
```

**Relationships:** Belongs to Research; References Narrative; References Evidence; Referenced by Scenario, Confidence.
**Lifecycle:** Created → Active → Invalidated/Retired → Archived

### 5.2 HypothesisSet

**Purpose:** A collection of all hypotheses for a research cycle.

```
HypothesisSet:
  id:              string (deterministic UUID)
  research_id:     string
  hypotheses:      [Hypothesis.id]
  primary_id:      string
  alternatives:    [string]
  null_id:         string
  tail_ids:        [string]
  created_at:      timestamp
  last_updated:    timestamp
  set_hash:        string
```

**Relationships:** Belongs to Research; Contains Hypothesis.
**Lifecycle:** Created → Updated → Finalized → Archived

---

## 6. Scenario Layer Objects

### 6.1 Scenario

**Purpose:** A probabilistic future market state.

```
Scenario:
  id:              string (deterministic UUID)
  hypothesis_id:   string
  type:            string (e.g., "Base", "Bull", "Bear", "Tail")
  label:           string (e.g., "Scenario A")
  thesis:          string
  probability:     float (0.0-1.0)
  calibrated_probability: float
  confidence_interval: {lower: float, upper: float}
  expected_return:  float
  return_range:    {p5: float, p95: float}
  volatility:      float
  regime:          string
  assumptions:     [string]
  dependencies:    [string]
  valid_if:        [Condition]
  invalid_if:      [Condition]
  supporting_evidence: [string]
  contradicting_evidence: [string]
  milestones:      [Milestone]
  construction_trace: string
  created_at:      timestamp
  last_updated:    timestamp
  status:          string (e.g., "Active", "Valid", "Invalidated", "Resolved")
```

**Relationships:** References Hypothesis; References Evidence; Referenced by Confidence, Contradiction.
**Lifecycle:** Created → Active → Valid/Invalidated → Resolved → Retired

### 6.2 ScenarioSet

**Purpose:** A collection of all scenarios for a research cycle.

```
ScenarioSet:
  id:              string (deterministic UUID)
  research_id:     string
  scenarios:       [Scenario.id]
  base_id:         string
  bull_id:         string
  bear_id:         string
  tail_ids:        [string]
  total_probability: float (must sum to 1.0)
  scenario_diversity: float
  created_at:      timestamp
  last_updated:    timestamp
  set_hash:        string
```

**Relationships:** Belongs to Research; Contains Scenario.
**Lifecycle:** Created → Updated → Finalized → Archived

---

## 7. Confidence Layer Objects

### 7.1 Confidence

**Purpose:** A probability estimate with uncertainty bounds.

```
Confidence:
  id:              string (deterministic UUID)
  target_id:       string
  target_type:     string (e.g., "Hypothesis", "Scenario", "Interpretation")
  value:           float (0.0-1.0)
  calibrated_value: float
  lower_bound:     float
  upper_bound:     float
  standard_error:  float
  evidence_strength: float (weight 0.30)
  coherence:       float (weight 0.25)
  historical_precedent: float (weight 0.20)
  model_uncertainty: float (weight 0.15)
  recency:         float (weight 0.10)
  penalties:       [string]
  boosters:        [string]
  calibration_bin: string
  calibration_adjustment: float
  created_at:      timestamp
  last_updated:    timestamp
```

**Relationships:** References target object; Referenced by ConfidenceReport.
**Lifecycle:** Created → Calibrated → Updated → Archived

### 7.2 ConfidenceReport

**Purpose:** A collection of all confidence estimates for a research cycle.

```
ConfidenceReport:
  id:              string (deterministic UUID)
  research_id:     string
  confidences:     [Confidence.id]
  overall_confidence: float
  calibration_accuracy: float
  created_at:      timestamp
  last_updated:    timestamp
  report_hash:     string
```

**Relationships:** Belongs to Research; Contains Confidence.
**Lifecycle:** Created → Updated → Finalized → Archived

---

## 8. Contradiction Layer Objects

### 8.1 Contradiction

**Purpose:** A conflict between evidence, interpretations, or analyses.

```
Contradiction:
  id:              string (deterministic UUID)
  research_id:     string
  type:            string (e.g., "Internal", "Cross-Market", "Macro", "Timeframe", "Research")
  description:     string
  sides:           [{evidence: [string], weight: float, position: string}]
  severity:        float (0.0-1.0)
  resolution:      string (e.g., "Resolved", "Unresolved", "Escalated")
  resolution_method: string
  confidence_impact: float
  created_at:      timestamp
  resolved_at:     timestamp
  ontology_tags:   [string]
```

**Relationships:** Belongs to Research; References Evidence; Referenced by ContradictionReport.
**Lifecycle:** Detected → Assessed → Resolved/Escalated → Archived

### 8.2 ContradictionReport

**Purpose:** A collection of all contradictions for a research cycle.

```
ContradictionReport:
  id:              string (deterministic UUID)
  research_id:     string
  contradictions:  [Contradiction.id]
  total_count:     int
  resolved_count:  int
  unresolved_count: int
  average_severity: float
  created_at:      timestamp
  last_updated:    timestamp
  report_hash:     string
```

**Relationships:** Belongs to Research; Contains Contradiction.
**Lifecycle:** Created → Updated → Finalized → Archived

---

## 9. Decision Support Objects

### 9.1 Research

**Purpose:** The top-level research entity encompassing an entire research cycle.

```
Research:
  id:              string (deterministic UUID)
  question:        string
  timestamp:       timestamp
  time_horizon:    string (e.g., "Intraday", "Daily", "Weekly", "Monthly", "Quarterly")
  asset:           string
  methodology_version: string
  status:          string (e.g., "In Progress", "Complete", "Validated", "Archived")
  observation_ids: [string]
  evidence_registry_id: string
  hypothesis_set_id: string
  scenario_set_id: string
  confidence_report_id: string
  contradiction_report_id: string
  report_id:       string
  created_at:      timestamp
  completed_at:    timestamp
  validated_at:    timestamp
  research_hash:   string
```

**Relationships:** Contains all other research objects; Referenced by ResearchReport, Validation, Knowledge.
**Lifecycle:** Initiated → In Progress → Complete → Validated → Archived

### 9.2 ResearchQuestion

**Purpose:** A specific, testable question that the research aims to answer.

```
ResearchQuestion:
  id:              string (deterministic UUID)
  research_id:     string
  question:        string
  sub_questions:   [string]
  ontology_tags:   [string]
  priority:        float
  answerable:      bool
  created_at:      timestamp
```

**Relationships:** Belongs to Research.
**Lifecycle:** Created → Decomposed → Answered → Archived

### 9.3 ResearchReport

**Purpose:** The final output of the research process, presented to the human trader.

```
ResearchReport:
  id:              string (deterministic UUID)
  research_id:     string
  title:           string
  executive_summary: string
  research_question: string
  hypotheses:      string
  evidence_summary: string
  analyses:        string
  narrative:       string
  scenarios:       string
  confidence:      string
  contradictions:  string
  risk_factors:    [string]
  invalidation_conditions: [string]
  known_unknowns:  [string]
  open_questions:  [string]
  methodology_version: string
  report_hash:     string
  created_at:      timestamp
  format:          string (e.g., "Markdown", "PDF", "JSON")
  status:          string (e.g., "Draft", "Final", "Archived")
```

**Relationships:** Belongs to Research; Referenced by Validation.
**Lifecycle:** Draft → Final → Archived

---

## 10. Knowledge Layer Objects

### 10.1 Knowledge

**Purpose:** Structured knowledge about market behavior, accumulated over time.

```
Knowledge:
  id:              string (deterministic UUID)
  type:            string (e.g., "Entity_Property", "Classification_Rule", "State_Transition", "Relationship_Strength", "Event_Impact", "Regime_Characteristic")
  subject:         string (ontology concept ID)
  predicate:       string
  object:          string
  confidence:      float (0.0-1.0)
  evidence_count:  int
  first_observed:  timestamp
  last_updated:    timestamp
  source_references: [string]
  knowledge_trace: string
```

**Relationships:** Referenced by Evidence, Interpretation, Narrative.
**Lifecycle:** Discovered → Validated → Updated → Archived

### 10.2 Pattern

**Purpose:** A recurring market behavior identified from historical data.

```
Pattern:
  id:              string (deterministic UUID)
  type:            string (e.g., "Regime_Transition", "Event_Impact", "Cross_Market", "Technical", "Sentiment", "Liquidity")
  description:     string
  trigger_conditions: [Condition]
  outcome:         string
  historical_accuracy: float (0.0-1.0)
  sample_size:     int
  confidence_interval: {lower: float, upper: float}
  supporting_evidence: [string]
  contradicting_evidence: [string]
  first_identified: timestamp
  last_validated:   timestamp
  pattern_trace:    string
```

**Relationships:** Referenced by Evidence, Interpretation, Narrative, Scenario.
**Lifecycle:** Detected → Validated → Used → Retired

### 10.3 Lesson

**Purpose:** An actionable insight extracted from research validation.

```
Lesson:
  id:              string (deterministic UUID)
  type:            string (e.g., "Data", "Model", "Process", "Bias", "Scenario", "Validation")
  description:     string
  recommendation:  string
  severity:        float (0.0-1.0)
  frequency:       int
  first_observed:  timestamp
  last_observed:   timestamp
  affected_articles: [string]
  supporting_evidence: [string]
  lesson_trace:    string
```

**Relationships:** Referenced by Validation, CognitiveAssessment.
**Lifecycle:** Extracted → Prioritized → Applied → Retired

---

## 11. Validation Objects

### 11.1 Validation

**Purpose:** The evaluation of research against actual market outcomes.

```
Validation:
  id:              string (deterministic UUID)
  research_id:     string
  research_report_id: string
  validation_date: timestamp
  time_horizon:    string
  overall_status:  string (e.g., "Accurate", "Partially Accurate", "Inaccurate")
  quality_score:   float (0.0-1.0)
  scenario_results: [ScenarioValidationResult]
  target_results:  [TargetValidationResult]
  failure_analysis_id: string
  statistics_update_id: string
  validation_trace: string
  created_at:      timestamp
```

**Relationships:** Belongs to Research; Referenced by FailureAnalysis, StatisticsUpdate, Lesson.
**Lifecycle:** Initiated → In Progress → Complete → Archived

### 11.2 FailureAnalysis

**Purpose:** Root cause analysis of research failures.

```
FailureAnalysis:
  id:              string (deterministic UUID)
  validation_id:   string
  research_id:     string
  failures:        [FailureDetail]
  root_causes:     [RootCause]
  severity_scores: [SeverityScore]
  improvement_areas: [string]
  failure_trace:   string
  created_at:      timestamp
```

**Relationships:** Belongs to Validation; Referenced by StatisticsUpdate, Lesson.
**Lifecycle:** Initiated → Analyzed → Completed → Archived

---

## 12. Cognitive Objects

### 12.1 Bias

**Purpose:** A detected cognitive bias in the trader's decision-making.

```
Bias:
  id:              string (deterministic UUID)
  type:            string (e.g., "Confirmation", "Anchoring", "Overconfidence", "Recency", "Availability", "Survivorship", "Hindsight", "Loss_Aversion")
  trader_id:       string
  decision_id:     string
  description:     string
  evidence:        [string]
  frequency:       float (0.0-1.0)
  trend:           float
  first_detected:  timestamp
  last_detected:   timestamp
  severity:        float (0.0-1.0)
  bias_trace:      string
```

**Relationships:** Referenced by CognitiveAssessment, LearningRecord.
**Lifecycle:** Detected → Tracked → Mitigated → Retired

### 12.2 LearningRecord

**Purpose:** A record of the trader's cognitive learning progress.

```
LearningRecord:
  id:              string (deterministic UUID)
  trader_id:       string
  dimension:       string (e.g., "Knowledge", "Reasoning", "Bias", "Discipline", "Reflection", "Learning_Progress")
  score:           float (0.0-1.0)
  baseline_score:  float
  progress:        float
  trend:           float
  trajectory:      string (e.g., "Accelerating", "Steady", "Decelerating", "Plateauing")
  recommendations: [string]
  recorded_at:     timestamp
  learning_trace:  string
```

**Relationships:** Referenced by CognitiveAssessment.
**Lifecycle:** Recorded → Tracked → Updated → Archived

### 12.3 CognitiveAssessment

**Purpose:** A comprehensive assessment of the trader's cognitive capabilities.

```
CognitiveAssessment:
  id:              string (deterministic UUID)
  trader_id:       string
  research_id:     string
  knowledge_score: float (0.0-1.0)
  reasoning_score: float (0.0-1.0)
  bias_profile:    [Bias.id]
  discipline_score: float (0.0-1.0)
  reflection_score: float (0.0-1.0)
  learning_progress: float (0.0-1.0)
  overall_score:   float (0.0-1.0)
  feedback:        [string]
  recommendations: [string]
  assessment_trace: string
  created_at:      timestamp
  assessment_hash: string
```

**Relationships:** Contains Bias; Contains LearningRecord; Referenced by Lesson.
**Lifecycle:** Initiated → Assessed → Completed → Archived

---

## 13. Process Objects

### 13.1 ResearchCycle

**Purpose:** The complete cycle of research, from question to validation.

```
ResearchCycle:
  id:              string (deterministic UUID)
  research_id:     string
  start_time:      timestamp
  end_time:        timestamp
  stages:          [Stage]
  duration:        float (seconds)
  inputs:          [string]
  outputs:         [string]
  quality_metrics: [QualityMetric]
  cycle_hash:      string
  created_at:      timestamp
```

**Relationships:** Belongs to Research; Contains ReasoningChain.
**Lifecycle:** Started → In Progress → Completed → Archived

### 13.2 ReasoningChain

**Purpose:** A complete chain of reasoning from observation to conclusion.

```
ReasoningChain:
  id:              string (deterministic UUID)
  research_id:     string
  steps:           [ReasoningStep]
  inputs:          [string]
  outputs:         [string]
  rules_applied:   [string]
  evidence_used:   [string]
  confidence:      float (0.0-1.0)
  chain_hash:      string
  created_at:      timestamp
  trace:           string
```

**Relationships:** Belongs to Research; Referenced by AuditEntry.
**Lifecycle:** Created → Verified → Archived

### 13.3 AuditEntry

**Purpose:** An immutable record of a single action or decision in the system.

```
AuditEntry:
  id:              string (deterministic UUID)
  timestamp:       timestamp
  actor:           string
  action:          string
  object_id:       string
  object_type:     string
  before_state:    string
  after_state:     string
  reasoning_chain_id: string
  entry_hash:      string
  previous_entry:  string
```

**Relationships:** References ReasoningChain.
**Lifecycle:** Created → Immutable → Archived

---

## 14. Object Count Summary

| Layer | Object Types | Total Objects (est.) |
|---|---|---|
| **Observation** | 3 | ~116,000/day |
| **Evidence** | 2 | ~50,000/research |
| **Interpretation** | 2 | ~50/research |
| **Hypothesis** | 2 | ~5/research |
| **Scenario** | 2 | ~5/research |
| **Confidence** | 2 | ~10/research |
| **Contradiction** | 2 | ~5/research |
| **Decision Support** | 3 | ~1/research |
| **Knowledge** | 3 | ~10,000/lifetime |
| **Validation** | 2 | ~1/research |
| **Cognitive** | 3 | ~5/trader/year |
| **Process** | 3 | ~5/research |

---

*This concludes the ResearchOS Object Model specification.*
