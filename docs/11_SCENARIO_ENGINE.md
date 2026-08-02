# ResearchOS — Constitution

## Article XI: Scenario Engine

> **Version:** 1.0.0
> **Status:** Phase 0 — Constitutional Foundation
> **Last Updated:** 2026-07-29
> **Determinism Guarantee:** Every scenario is constructed using fixed, deterministic rules. Given identical inputs (observations, evidence, analysis, narrative), the same scenarios with identical probabilities and validity conditions are guaranteed.
> **Explainability Guarantee:** Every scenario includes a complete construction trace documenting the primary driver, supporting evidence, probability calculation, validity conditions, and outcome specifications.

---

### 11.1 Overview

The Scenario Engine is the component of ResearchOS that constructs probabilistic market scenarios from analysis results, evidence, and narrative. It produces a structured set of scenarios that describe possible future market states, each with:

- A **probability** estimate (calibrated against historical data)
- **Validity conditions** (what would make the scenario valid)
- **Invalidity conditions** (what would make the scenario invalid)
- **Outcome specifications** (expected returns, volatility, regime)
- A **construction trace** (why the scenario was built this way)

The engine produces three primary scenario types:

| Scenario | Type | Description |
|---|---|---|
| **Scenario A** | Base | The most likely outcome given current evidence |
| **Scenario B** | Bull | An optimistic outcome where the primary driver is stronger |
| **Scenario C** | Bear | A pessimistic outcome where the primary driver is weaker or reversed |

Additional **tail scenarios** are generated from narrative invalidation conditions when they exist.

---

### 11.2 Scenario Engine Inputs

The Scenario Engine consumes artifacts from the Reasoning Engine (Article X):

| Input | Source | Article |
|---|---|---|
| `AnalysisReport` | Stage 3: Interpretation & Analysis | X.4 |
| `EvidenceRegistry` | Stage 2: Evidence Formation | X.3 |
| `Narrative` | Stage 3: Interpretation & Analysis | X.4 |
| `ContradictionReport` | Stage 4: Contradiction Detection | X.5 |
| `CalibrationTable` | Confidence Estimation | VII.10.4 |

Each input is versioned and timestamped. The Scenario Engine uses only data available at the research timestamp (look-ahead bias prevention).

---

### 11.3 Scenario Engine Outputs

The Scenario Engine produces a `ScenarioSet` artifact containing:

```
ScenarioSet:
  scenarios: [
    {
      id: string,
      type: [Base | Bull | Bear | Tail],
      label: string,                    # e.g., "Scenario A"
      thesis: string,
      probability: float,
      calibrated_probability: float,
      confidence_interval: {lower: float, upper: float},
      expected_return: float,
      return_range: {p5: float, p95: float},
      volatility: float,
      regime: string,
      valid_if: [Condition],
      invalid_if: [Condition],
      dependencies: [string],
      supporting_evidence: [string],
      contradicting_evidence: [string],
      milestones: [Milestone],
      construction_trace: ConstructionTrace
    }
  ]
  probability_calibration: float
  scenario_diversity: float
  total_probability: float
```

---

### 11.4 Scenario A: Base Case Construction

**Scenario Type:** Base
**Label:** Scenario A
**Ontology Reference:** `ONTOLOGY:STATE:REGIME`, `ONTOLOGY:RELATIONSHIP:CAUSAL`

#### 11.4.1 Purpose

Scenario A represents the most likely future market state given all available evidence. It is the anchor scenario from which all other scenarios diverge.

#### 11.4.2 Construction Procedure

**Step 1: Narrative Extraction**

1. Extract the narrative thesis from the `Narrative` artifact.
2. Extract the primary driver and supporting drivers.
3. Extract the evidence strength, coherence score, and plausibility score.

**Step 2: Probability Calculation**

The base probability is computed using the deterministic formula from Article VII, Section 7.9.2:

```
P_base = (evidence_strength × 0.50) + (coherence_score × 0.30) + (plausibility_score × 0.20)
```

Where:
- `evidence_strength` = The narrative's evidence strength (0.0–1.0)
- `coherence_score` = The narrative's coherence score (0.0–1.0)
- `plausibility_score` = The narrative's plausibility score (0.0–1.0)

**Step 3: Outcome Specification**

The outcome is specified using the following deterministic rules:

1. **Expected Return:**
   - Derived from the primary driver's historical relationship to market returns.
   - Computed as:
     ```
     E[R_base] = μ_driver × β_driver × T
     ```
     Where:
     - `μ_driver` = Historical average return associated with the primary driver
     - `β_driver` = Sensitivity of the asset to the primary driver
     - `T` = Time horizon (in years)

2. **Return Range:**
   - The 5th percentile is computed as:
     ```
     R_p5 = E[R_base] - (σ_driver × 1.645 × √T)
     ```
   - The 95th percentile is computed as:
     ```
     R_p95 = E[R_base] + (σ_driver × 1.645 × √T)
     ```
   - Where `σ_driver` is the historical standard deviation of returns associated with the primary driver.

3. **Volatility:**
   - Computed as the weighted average of the three analytical dimensions' volatility estimates:
     ```
     σ_base = (σ_macro × 0.30) + (σ_technical × 0.40) + (σ_liquidity × 0.30)
     ```

4. **Regime:**
   - The regime is taken directly from the macro regime classification (Article VII, Section 7.5.2).
   - If the macro and technical regimes differ, the macro regime takes precedence.

**Step 4: Validity Condition Definition**

1. **Valid-If Conditions:**
   - Derived from the primary driver's supporting evidence.
   - Each supporting evidence entry contributes one condition.
   - Conditions are combined with AND logic.
   - Example: "10-year yield remains below 4.5% for 30 days"

2. **Invalid-If Conditions:**
   - Derived from the primary driver's contradicting evidence.
   - Each contradicting evidence entry contributes one condition.
   - Conditions are combined with OR logic.
   - Example: "10-year yield exceeds 5.0% OR CPI YoY exceeds 6.0%"

**Step 5: Milestone Definition**

1. **Confirmation Milestones:**
   - Events that would strengthen the scenario if they occur.
   - Derived from the narrative's catalyst list.
   - Each milestone is assigned an impact score (0.0–1.0).

2. **Refutation Milestones:**
   - Events that would weaken the scenario if they occur.
   - Derived from the narrative's invalidation conditions.
   - Each milestone is assigned an impact score (0.0–1.0).

**Step 6: Construction Trace**

The construction trace documents:
- The narrative thesis used
- The probability calculation with all factor values
- The outcome specifications and their derivation
- The validity/invalidity conditions and their source evidence
- The milestones and their impact scores

#### 11.4.3 Example

Given:
- Narrative thesis: "The market is in an Expansion regime, primarily driven by accommodative monetary policy."
- Evidence strength: 0.75
- Coherence score: 0.85
- Plausibility score: 0.80

Construction:
```
P_base = (0.75 × 0.50) + (0.85 × 0.30) + (0.80 × 0.20) = 0.375 + 0.255 + 0.160 = 0.790

E[R_base] = 0.08 × 1.2 × 0.5 = 0.048 (4.8% expected return over 6 months)

R_p5 = 0.048 - (0.15 × 1.645 × √0.5) = 0.048 - 0.174 = -0.126 (-12.6%)
R_p95 = 0.048 + (0.15 × 1.645 × √0.5) = 0.048 + 0.174 = 0.222 (22.2%)

σ_base = (0.12 × 0.30) + (0.18 × 0.40) + (0.10 × 0.30) = 0.036 + 0.072 + 0.030 = 0.138

Valid-If: "Fed funds rate remains at 5.25-5.50%" AND "10-year yield stays below 4.5%"
Invalid-If: "Fed cuts rates by 50+ bps" OR "10-year yield exceeds 5.0%"
```

---

### 11.5 Scenario B: Bull Case Construction

**Scenario Type:** Bull
**Label:** Scenario B
**Ontology Reference:** `ONTOLOGY:STATE:TREND:ACCELERATING`, `ONTOLOGY:RELATIONSHIP:AMPLIFIES`

#### 11.5.1 Purpose

Scenario B represents an optimistic outcome where the primary driver is stronger than the base case. It captures the upside potential of the market narrative.

#### 11.5.2 Construction Procedure

**Step 1: Driver Amplification**

1. Identify the primary driver from the narrative.
2. Determine the amplification factor using the deterministic formula:
   ```
   Amplification = 1.0 + (base_probability × 0.50)
   ```
   This means: if the base probability is 0.80, the amplification factor is 1.40 (40% stronger driver).

3. Adjust the primary driver's expected value:
   ```
   Driver_bull = Driver_base × Amplification
   ```

**Step 2: Probability Calculation**

The bull probability is computed using the formula from Article VII, Section 7.9.2:

```
P_bull = (1.0 − P_base) × 0.40
```

This allocates 40% of the remaining probability (after the base case) to the bull scenario.

**Step 3: Outcome Specification**

1. **Expected Return:**
   ```
   E[R_bull] = E[R_base] × Amplification × 1.20
   ```
   The 1.20 multiplier accounts for the additional optimism in the bull case.

2. **Return Range:**
   - The range is widened to reflect increased uncertainty:
     ```
     R_p5_bull = E[R_bull] - (σ_base × 1.645 × √T × 1.10)
     R_p95_bull = E[R_bull] + (σ_base × 1.645 × √T × 1.10)
     ```
   - The 1.10 multiplier widens the range by 10%.

3. **Volatility:**
   ```
   σ_bull = σ_base × 0.90
   ```
   Volatility is typically lower in bull markets (investors are complacent).

4. **Regime:**
   - The regime is the same as the base case, but with an "accelerating" trend modifier.
   - Example: "Expansion → Expansion (Accelerating)"

**Step 4: Validity Condition Definition**

1. **Valid-If Conditions:**
   - The primary driver exceeds its base case value by the amplification factor.
   - Supporting evidence is stronger than in the base case.
   - Example: "Fed funds rate stays at 5.25-5.50%" AND "10-year yield rises to 4.0-4.5%" AND "CPI YoY falls below 3.0%"

2. **Invalid-If Conditions:**
   - The primary driver fails to materialize.
   - Contradicting evidence becomes dominant.
   - Example: "Fed cuts rates" OR "CPI YoY exceeds 5.0%" OR "10-year yield exceeds 5.0%"

**Step 5: Milestone Definition**

1. **Confirmation Milestones:**
   - Events that would confirm the bull case.
   - Example: "Stronger-than-expected GDP growth", "Lower-than-expected inflation"

2. **Refutation Milestones:**
   - Events that would invalidate the bull case.
   - Example: "Weaker-than-expected economic data", "Inflation surprise to the upside"

**Step 6: Construction Trace**

The construction trace documents:
- The amplification factor and its calculation
- The probability allocation
- The outcome specifications and their derivation
- The validity/invalidity conditions
- The milestones

#### 11.5.3 Example

Given:
- P_base = 0.790
- E[R_base] = 0.048
- σ_base = 0.138

Construction:
```
Amplification = 1.0 + (0.790 × 0.50) = 1.395

P_bull = (1.0 − 0.790) × 0.40 = 0.210 × 0.40 = 0.084

E[R_bull] = 0.048 × 1.395 × 1.20 = 0.0805 (8.05% expected return)

R_p5_bull = 0.0805 - (0.138 × 1.645 × √0.5 × 1.10) = 0.0805 - 0.191 = -0.111 (-11.1%)
R_p95_bull = 0.0805 + 0.191 = 0.272 (27.2%)

σ_bull = 0.138 × 0.90 = 0.124

Valid-If: "Fed funds rate stays at 5.25-5.50%" AND "10-year yield rises to 4.0-4.5%" AND "CPI YoY falls below 3.0%"
Invalid-If: "Fed cuts rates" OR "CPI YoY exceeds 5.0%" OR "10-year yield exceeds 5.0%"
```

---

### 11.6 Scenario C: Bear Case Construction

**Scenario Type:** Bear
**Label:** Scenario C
**Ontology Reference:** `ONTOLOGY:STATE:TREND:REVERSING`, `ONTOLOGY:RELATIONSHIP:CONTRADICTS`

#### 11.6.1 Purpose

Scenario C represents a pessimistic outcome where the primary driver is weaker or reversed. It captures the downside risk of the market narrative.

#### 11.6.2 Construction Procedure

**Step 1: Driver Reversal**

1. Identify the primary driver from the narrative.
2. Determine the reversal factor using the deterministic formula:
   ```
   Reversal = 1.0 - (base_probability × 0.50)
   ```
   This means: if the base probability is 0.80, the reversal factor is 0.60 (the driver is 40% weaker).

3. Adjust the primary driver's expected value:
   ```
   Driver_bear = Driver_base × Reversal × -1.0
   ```
   The -1.0 multiplier reverses the direction of the driver.

**Step 2: Probability Calculation**

The bear probability is computed using the formula from Article VII, Section 7.9.2:

```
P_bear = (1.0 − P_base) × 0.40
```

This allocates 40% of the remaining probability (after the base case) to the bear scenario.

**Step 3: Outcome Specification**

1. **Expected Return:**
   ```
   E[R_bear] = E[R_base] × Reversal × -0.80
   ```
   The -0.80 multiplier accounts for the downside and the asymmetry of market declines.

2. **Return Range:**
   - The range is widened to reflect increased uncertainty:
     ```
     R_p5_bear = E[R_bear] - (σ_base × 1.645 × √T × 1.10)
     R_p95_bear = E[R_bear] + (σ_base × 1.645 × √T × 1.10)
     ```

3. **Volatility:**
   ```
   σ_bear = σ_base × 1.20
   ```
   Volatility is typically higher in bear markets (investors are fearful).

4. **Regime:**
   - The regime is adjusted to reflect the bear case.
   - If the base regime is "Expansion", the bear regime is "Deflationary Slump".
   - If the base regime is "Stagflation", the bear regime is "Stagflation (Worsening)".
   - The regime mapping is defined in a fixed `RegimeTransitionTable`.

**Step 4: Validity Condition Definition**

1. **Valid-If Conditions:**
   - The primary driver is reversed or significantly weakened.
   - Contradicting evidence becomes dominant.
   - Example: "Fed hikes rates by 50+ bps" OR "CPI YoY exceeds 6.0%" OR "10-year yield exceeds 5.0%"

2. **Invalid-If Conditions:**
   - The primary driver continues in the base case direction.
   - Supporting evidence remains dominant.
   - Example: "Fed cuts rates" OR "CPI YoY falls below 3.0%" OR "10-year yield falls below 4.0%"

**Step 5: Milestone Definition**

1. **Confirmation Milestones:**
   - Events that would confirm the bear case.
   - Example: "Higher-than-expected inflation", "Stronger-than-expected Fed tightening"

2. **Refutation Milestones:**
   - Events that would invalidate the bear case.
   - Example: "Lower-than-expected inflation", "Dovish Fed communication"

**Step 6: Construction Trace**

The construction trace documents:
- The reversal factor and its calculation
- The probability allocation
- The outcome specifications and their derivation
- The validity/invalidity conditions
- The milestones

#### 11.6.3 Example

Given:
- P_base = 0.790
- E[R_base] = 0.048
- σ_base = 0.138

Construction:
```
Reversal = 1.0 - (0.790 × 0.50) = 0.605

P_bear = (1.0 − 0.790) × 0.40 = 0.210 × 0.40 = 0.084

E[R_bear] = 0.048 × 0.605 × -0.80 = -0.0232 (-2.32% expected return)

R_p5_bear = -0.0232 - (0.138 × 1.645 × √0.5 × 1.10) = -0.0232 - 0.191 = -0.214 (-21.4%)
R_p95_bear = -0.0232 + 0.191 = 0.168 (16.8%)

σ_bear = 0.138 × 1.20 = 0.166

Valid-If: "Fed hikes rates by 50+ bps" OR "CPI YoY exceeds 6.0%" OR "10-year yield exceeds 5.0%"
Invalid-If: "Fed cuts rates" OR "CPI YoY falls below 3.0%" OR "10-year yield falls below 4.0%"
```

---

### 11.7 Tail Scenario Construction

**Scenario Type:** Tail
**Label:** Scenario D, E, F (as needed)
**Ontology Reference:** `ONTOLOGY:EVENT:SYSTEMIC_CRISIS`, `ONTOLOGY:RELATIONSHIP:CONTAGION`

#### 11.7.1 Purpose

Tail scenarios represent low-probability, high-impact events that are not captured by the base, bull, or bear scenarios. They are generated from the narrative's invalidation conditions.

#### 11.7.2 Construction Procedure

**Step 1: Invalidation Condition Extraction**

1. Extract all invalidation conditions from the narrative.
2. For each condition, determine the triggering event.
3. Assign each condition to a tail scenario.

**Step 2: Probability Assignment**

The tail probability is computed using the formula from Article VII, Section 7.9.2:

```
P_tail_i = (1.0 − P_base − P_bull − P_bear) × (historical_frequency_i / Σ historical_frequencies)
```

Where:
- `historical_frequency_i` = The historical frequency of the triggering event
- `Σ historical_frequencies` = The sum of all triggering events' historical frequencies

**Step 3: Outcome Specification**

1. **Expected Return:**
   - Computed from the triggering event's historical impact:
     ```
     E[R_tail] = E[R_base] + Impact_event
     ```
   - Where `Impact_event` is the average market return during similar historical events.

2. **Return Range:**
   - The range is significantly widened:
     ```
     R_p5_tail = E[R_tail] - (σ_base × 1.645 × √T × 2.00)
     R_p95_tail = E[R_tail] + (σ_base × 1.645 × √T × 2.00)
     ```
   - The 2.00 multiplier reflects the extreme uncertainty of tail events.

3. **Volatility:**
   ```
   σ_tail = σ_base × 2.00
   ```

4. **Regime:**
   - The regime is set to "Stagflation" or "Deflationary Slump" depending on the nature of the tail event.

**Step 4: Validity Condition Definition**

1. **Valid-If Conditions:**
   - The triggering event occurs.
   - Example: "Geopolitical crisis in the Middle East" OR "Pandemic declaration by WHO"

2. **Invalid-If Conditions:**
   - The triggering event does not occur within the time horizon.
   - Example: "No major geopolitical event within 30 days"

**Step 5: Construction Trace**

The construction trace documents:
- The invalidation condition that triggered the tail scenario
- The historical frequency used for probability assignment
- The outcome specifications
- The validity/invalidity conditions

---

### 11.8 Scenario Probability Normalization

After all scenarios are constructed, probabilities are normalized to sum to 1.0.

#### 11.8.1 Procedure

1. **Sum Calculation:**
   ```
   P_total = P_base + P_bull + P_bear + Σ P_tail_i
   ```

2. **Normalization:**
   If |P_total - 1.0| > 0.01, adjust the base scenario probability:
   ```
   P_base_adjusted = P_base + (1.0 - P_total)
   ```

3. **Validation:**
   - All probabilities must be in [0.0, 1.0].
   - The sum must be 1.0 ± 0.001.
   - If validation fails, the system flags an error.

#### 11.8.2 Example

Given:
- P_base = 0.790
- P_bull = 0.084
- P_bear = 0.084
- P_tail_1 = 0.030
- P_tail_2 = 0.012

```
P_total = 0.790 + 0.084 + 0.084 + 0.030 + 0.012 = 1.000

No adjustment needed. ✓
```

---

### 11.9 Scenario Calibration

Scenario probabilities are calibrated against historical data using the calibration table from Article VII, Section 7.10.4.

#### 11.9.1 Procedure

1. **Bin Assignment:**
   - Each scenario's probability is assigned to a calibration bin of width 0.1.
   - Example: P = 0.790 → Bin 0.7-0.8

2. **Calibration Lookup:**
   - The system looks up the observed frequency for the bin.
   - If the observed frequency differs from the bin midpoint by >0.05, a calibration adjustment is applied.

3. **Adjustment Formula:**
   ```
   P_calibrated = Observed_Frequency + (P_raw - Bin_Midpoint)
   ```

4. **Confidence Interval Update:**
   - The confidence interval is updated to reflect the calibration:
     ```
     CI_calibrated = P_calibrated ± (1.0 - P_calibrated) × z × σ
     ```

#### 11.9.2 Example

Given:
- P_base = 0.790 (Bin 0.7-0.8, midpoint = 0.75)
- Observed frequency for this bin = 0.72

```
Calibration adjustment = 0.72 - 0.75 = -0.03
P_calibrated = 0.790 + (-0.03) = 0.760

CI_calibrated = 0.760 ± (1.0 - 0.760) × 1.96 × sqrt(0.760 × 0.240 / N)
```

---

### 11.10 Scenario Monitoring

Scenarios are monitored after construction to track their validity over time.

#### 11.10.1 Monitoring Procedure

1. **Daily Condition Checking:**
   - Each scenario's validity conditions are checked daily.
   - When a condition is triggered, the scenario's status is updated.

2. **Status Transitions:**
   - **Active** → All conditions pending
   - **Valid** → All valid-if conditions met, no invalid-if conditions met
   - **Invalidated** → Any invalid-if condition met
   - **Resolved** → All conditions resolved (either valid or invalidated)

3. **Notification:**
   - When a scenario's status changes, a notification is sent to the Human Trader.
   - The notification includes the triggered condition and the new status.

4. **Outcome Comparison:**
   - When a scenario is resolved, its actual outcome is compared to the expected outcome.
   - The comparison is recorded for future calibration.

#### 11.10.2 Monitoring Data Structure

```
ScenarioMonitoring:
  scenario_id: string
  status: [Active | Valid | Invalidated | Resolved]
  valid_if_status: [
    {
      condition: Condition,
      met: bool,
      date_met: timestamp (if met)
    }
  ]
  invalid_if_status: [
    {
      condition: Condition,
      met: bool,
      date_met: timestamp (if met)
    }
  ]
  actual_outcome: float (filled when resolved)
  resolution_date: timestamp (filled when resolved)
```

---

### 11.11 Scenario Engine Architecture

The Scenario Engine is designed as a modular component with four sub-engines:

```
┌─────────────────────────────────────────────────────────────┐
│  Scenario Engine                                            │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Base        │  │ Bull/Bear   │  │ Tail        │         │
│  │ Scenario    │  │ Scenario    │  │ Scenario    │         │
│  │ Constructor │  │ Constructor │  │ Constructor │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│        │               │               │                    │
│        ▼               ▼               ▼                    │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Probability Normalizer & Calibrator                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Scenario Monitor                                      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### 11.11.1 Module Interfaces

| Module | Input | Output |
|---|---|---|
| Base Scenario Constructor | `Narrative`, `EvidenceRegistry` | `Scenario` (Base) |
| Bull/Bear Scenario Constructor | `Scenario` (Base), `AnalysisReport` | `Scenario` (Bull), `Scenario` (Bear) |
| Tail Scenario Constructor | `Narrative`, `CalibrationTable` | `Scenario` (Tail) [] |
| Probability Normalizer | All scenarios | `ScenarioSet` |
| Scenario Monitor | `ScenarioSet`, `ObservationSet` | `ScenarioMonitoring` [] |

#### 11.11.2 Error Handling

- **Missing Narrative** — If no narrative exists, the base scenario is constructed from analysis results directly.
- **Insufficient Evidence** — If evidence is insufficient, probabilities are reduced and confidence intervals widened.
- **Probability Overflow** — If probabilities exceed 1.0, they are normalized.
- **Invalid Conditions** — If validity conditions are impossible to satisfy, the scenario is flagged.

---

### 11.12 Scenario Engine Guarantees

#### 11.12.1 Determinism Guarantees

**S1: Input Determinism**
- All inputs are explicitly defined and versioned.
- Data sources are identified by fixed URIs (Article VIII).
- Parameters are stored in version-controlled configuration files.

**S2: Rule Determinism**
- Every scenario construction rule is a fixed, explicit transformation.
- No rule involves randomness, subjective judgment, or machine learning inference.
- All formulas use fixed coefficients and thresholds.

**S3: Output Determinism**
- Given the same inputs and the same version of the Scenario Engine, the same scenarios are guaranteed.
- A deterministic hash of each scenario is computed and stored for verification.

**S4: Reproducibility**
- Every scenario includes a complete construction trace.
- Any researcher can reproduce the scenario by following the trace.
- The audit trail contains all intermediate calculations.

#### 11.12.2 Explainability Guarantees

**S5: Traceability**
- Every scenario is linked to its supporting evidence through the construction trace.
- Every probability is linked to its contributing factors.
- Every validity condition is linked to its source evidence.

**S6: Plain-Language Explanations**
- Every scenario includes a plain-language description of the thesis.
- Every probability calculation is explained in plain language.
- Every validity condition is expressed in clear, testable terms.

**S7: Right to Explanation**
- The Human Trader can request the construction trace for any scenario at any time.
- The trace includes all formulas, factor values, and evidence references.
- The trace is presented in a step-by-step, human-readable format.

**S8: Transparency of AI Contribution**
- All machine-generated scenarios are clearly labeled.
- The system distinguishes between human-authored narratives and machine-generated scenarios.
- All scenarios are produced by deterministic rules, not stochastic models.

---

### 11.13 Scenario Engine Summary

The Scenario Engine constructs three primary scenarios (A: Base, B: Bull, C: Bear) plus tail scenarios from narrative invalidation conditions. Each scenario is built using deterministic rules that:

1. **Extract** the primary driver and evidence from the narrative
2. **Compute** the probability using fixed formulas
3. **Specify** the outcome (expected return, range, volatility, regime)
4. **Define** validity and invalidity conditions
5. **Identify** confirmation and refutation milestones
6. **Document** the complete construction trace

After construction, probabilities are normalized and calibrated against historical data. Scenarios are then monitored daily for condition triggers, with status updates and outcome comparisons recorded for future calibration.

The engine guarantees that every scenario is reproducible, traceable, and explainable.

---

*This concludes Article XI: Scenario Engine. The next article (Article XII) will define the Research Validation methodology.*
