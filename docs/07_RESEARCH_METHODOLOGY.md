# ResearchOS — Constitution

## Article VII: Research Methodology

> **Version:** 1.0.0
> **Status:** Phase 0 — Constitutional Foundation
> **Last Updated:** 2026-07-29
> **Determinism Guarantee:** Every procedure in this document is fully deterministic. Given identical inputs and methodology, identical outputs are guaranteed. No stochastic processes are used without an explicitly seeded random number generator.
> **Explainability Guarantee:** Every output produced by any procedure in this document is traceable to its supporting inputs through an explicit, auditable chain of reasoning.

---

### 7.1 Overview

This article defines the complete research methodology for ResearchOS. It specifies the deterministic, explainable procedures that transform raw market data into institutional-grade market intelligence.

The methodology is organized as a **pipeline of deterministic stages**, each producing artifacts that are consumed by subsequent stages. Every stage enforces three invariants:

1. **Falsifiability** — Every hypothesis and scenario specifies conditions under which it would be proven wrong.
2. **Multi-Factor Integration** — No single analytical dimension determines a conclusion. At minimum two independent dimensions must concur.
3. **Temporal Integrity** — No analysis uses data unavailable at the time of the research question. Look-ahead bias is structurally impossible.

The methodology is divided into the following sections:

| Section | Topic |
|---|---|
| 7.2 | Research Lifecycle |
| 7.3 | Evidence Collection |
| 7.4 | Evidence Weighting |
| 7.5 | Macro Analysis |
| 7.6 | Technical Analysis |
| 7.7 | Liquidity Analysis |
| 7.8 | Market Narrative |
| 7.9 | Scenario Generation |
| 7.10 | Confidence Estimation |
| 7.11 | Contradiction Detection |
| 7.12 | Research Report Generation |
| 7.13 | Validation Integration |
| 7.14 | Determinism and Explainability Guarantees |

---

### 7.2 Research Lifecycle

The research lifecycle is a seven-stage pipeline that every research cycle must traverse. Each stage produces a **Research Artifact** that is stored in the immutable audit trail (see Article V, Section 5.6).

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Stage 1:       │     │  Stage 2:        │     │  Stage 3:        │
│  Question       │────▶│  Hypothesis     │────▶│  Evidence        │
│  Formulation    │     │  Formation       │     │  Collection      │
└─────────────────┘     └──────────────────┘     └──────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Stage 4:       │     │  Stage 5:        │     │  Stage 6:        │
│  Analysis       │────▶│  Narrative       │────▶│  Scenario        │
│  (Macro, Tech,  │     │  Synthesis       │     │  Generation      │
│  Liquidity)     │     │                  │     │                  │
└─────────────────┘     └──────────────────┘     └──────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Stage 7:       │     │  Stage 8:        │     │  Stage 9:        │
│  Confidence     │────▶│  Contradiction   │────▶│  Report          │
│  Estimation     │     │  Detection       │     │  Generation      │
└─────────────────┘     └──────────────────┘     └──────────────────┘
```

#### Stage 1: Question Formulation

**Input:** Human Trader's research question (free-text, human-authored).
**Output:** `ResearchQuestion` artifact.

**Procedure:**

1. The Human Trader submits a research question in free text.
2. The system parses the question and extracts:
   - **Subject** — The market, asset, or phenomenon under investigation.
   - **Time Horizon** — The expected timeframe for the answer (intraday, daily, weekly, monthly, quarterly).
   - **Decision Context** — The type of decision the research will inform (position sizing, timing, risk assessment).
3. The system validates that the question is:
   - **Specific** — Not vague or overly broad.
   - **Testable** — Can be answered with empirical evidence.
   - **Actionable** — The answer would change the trader's decision.
4. If the question fails validation, the system returns it with specific feedback. The Human Trader must revise.
5. The validated question is stored as a `ResearchQuestion` artifact with a unique identifier, timestamp, and author.

**Determinism Note:** The parsing rules are defined as a fixed set of regex patterns and keyword mappings. No machine learning is used for parsing.

#### Stage 2: Hypothesis Formation

**Input:** `ResearchQuestion` artifact.
**Output:** `HypothesisSet` artifact.

**Procedure:**

1. The system generates a set of candidate hypotheses using a fixed rule-based template engine. Each template is parameterized by the research question's subject and time horizon.
2. For each candidate hypothesis, the system checks:
   - **Falsifiability** — The hypothesis must specify at least one observable condition that would prove it false.
   - **Mutual Exclusivity** — Hypotheses within the set must not overlap in their predictions.
   - **Collective Exhaustiveness** — The set must cover all plausible outcomes.
3. The system assigns each hypothesis a unique identifier and stores the set as a `HypothesisSet` artifact.
4. The Human Trader reviews the hypotheses and may:
   - Accept all (proceed to Stage 3).
   - Reject specific hypotheses (they are removed, and the set is re-validated).
   - Add new hypotheses (they are validated against the same criteria).

**Hypothesis Template Structure:**

```
Hypothesis H-i:
  Statement:    [falsifiable statement about market behavior]
  Time Horizon: [matching the research question]
  Valid If:     [observable conditions that support this hypothesis]
  Invalid If:   [observable conditions that refute this hypothesis]
  Dependencies: [list of assumptions this hypothesis relies on]
```

#### Stage 3: Evidence Collection

**Input:** `HypothesisSet` artifact.
**Output:** `EvidenceRegistry` artifact.
**See Section 7.3 for full procedure.**

#### Stage 4: Analysis

**Input:** `EvidenceRegistry` artifact.
**Output:** `AnalysisReport` artifact.
**See Sections 7.5, 7.6, 7.7 for the three analytical dimensions.**

#### Stage 5: Narrative Synthesis

**Input:** `AnalysisReport` artifact.
**Output:** `Narrative` artifact.
**See Section 7.8 for full procedure.**

#### Stage 6: Scenario Generation

**Input:** `Narrative` artifact, `EvidenceRegistry` artifact.
**Output:** `ScenarioSet` artifact.
**See Section 7.9 for full procedure.**

#### Stage 7: Confidence Estimation

**Input:** `ScenarioSet` artifact, `EvidenceRegistry` artifact.
**Output:** `ConfidenceReport` artifact.
**See Section 7.10 for full procedure.**

#### Stage 8: Contradiction Detection

**Input:** `AnalysisReport` artifact, `Narrative` artifact, `ScenarioSet` artifact.
**Output:** `ContradictionReport` artifact.
**See Section 7.11 for full procedure.**

#### Stage 9: Report Generation

**Input:** All preceding artifacts.
**Output:** `ResearchReport` artifact.
**See Section 7.12 for full procedure.**

---

### 7.3 Evidence Collection

Evidence collection is a systematic, deterministic process that gathers all relevant data points for a given research question. Every piece of evidence is recorded in an `EvidenceRegistry` with full metadata.

#### 7.3.1 Evidence Types

| Type | Description | Example |
|---|---|---|
| **Direct** | Observable fact that requires no interpretation | CPI release of 3.2% YoY |
| **Structural** | Observable market structure characteristic | 10-year yield above 200-day MA |
| **Derived** | Calculated from other evidence using a fixed formula | Real yield = nominal yield − inflation expectations |
| **Positional** | Observable positioning data from market participants | COT report showing net long 65% of speculators |
| **Event** | Observable occurrence of a scheduled or unscheduled event | Fed rate decision, geopolitical incident |

#### 7.3.2 Evidence Collection Protocol

**Procedure:**

1. **Source Identification:** For each hypothesis in the `HypothesisSet`, the system consults a fixed `EvidenceSourceMap` — a lookup table that maps hypothesis types to relevant data sources. This map is curated by human researchers and version-controlled.

2. **Temporal Window Definition:** For each source, the system defines:
   - **Observation Window** — The time range of data to collect (from the research timestamp backward to the earliest relevant date).
   - **Granularity** — The frequency of data points (daily, hourly, tick-level, etc.).
   - **Look-Back Period** — How far back to collect, determined by the hypothesis time horizon:
     - Intraday: 5 days
     - Daily: 250 trading days
     - Weekly: 500 trading days
     - Monthly: 1,000 trading days
     - Quarterly: 2,000 trading days

3. **Data Retrieval:** The system retrieves data from each source using a deterministic API call sequence. Each call includes:
   - Source identifier
   - Time range
   - Granularity
   - A fixed request ID (for reproducibility)

4. **Data Validation:** Each retrieved data point is validated against three criteria:
   - **Completeness** — No missing values in the requested range.
   - **Timeliness** — The data timestamp is before the research timestamp (look-ahead bias check).
   - **Integrity** — The data matches the expected format and value ranges defined in the source schema.

5. **Evidence Registration:** Each valid data point is registered in the `EvidenceRegistry` with the following fields:

```
EvidenceEntry:
  id:               UUID (deterministic, derived from source + timestamp + value)
  type:             [Direct | Structural | Derived | Positional | Event]
  source:           Source identifier (e.g., "FRED:CPIAUCSL")
  timestamp:        UTC timestamp of the observation
  value:            The observed value (or set of values)
  reliability:       Source reliability score (0.0–1.0, see Section 7.4.1)
  collection_time:  Timestamp when the data was retrieved
  collection_method:  Fixed string identifying the retrieval procedure
  derived_from:     List of evidence IDs this entry was derived from (empty for non-derived)
  formula:          The deterministic formula used (for derived evidence only)
  tags:            List of categorical tags (e.g., ["inflation", "monetary-policy"])
```

6. **Evidence Linking:** Each evidence entry is linked to one or more hypotheses in the `HypothesisSet` using a fixed `HypothesisEvidenceLinkMap`. This map specifies which evidence is relevant to which hypothesis, based on the hypothesis's stated dependencies.

**Determinism Note:** All data retrieval uses fixed API endpoints, fixed request parameters, and fixed validation rules. The only variable is the research timestamp, which is part of the input.

#### 7.3.3 Evidence Quality Flags

Each evidence entry may carry zero or more quality flags:

| Flag | Meaning | Impact on Weight |
|---|---|---|
| `STALE` | Data is older than the look-back period | Weight × 0.5 |
| `REVISED` | Data has been revised since initial publication | Weight × 0.9 |
| `PRELIMINARY` | Data is preliminary and subject to revision | Weight × 0.8 |
| `ESTIMATED` | Data is an estimate, not directly observed | Weight × 0.7 |
| `DISCONTINUED` | Data series has been discontinued | Weight × 0.3 |
| `ANOMALY` | Data point is flagged as anomalous by statistical tests | Weight × 0.1 |

#### 7.3.4 Evidence Freshness

Each evidence entry's **freshness** is computed as:

```
freshness = 1.0 / (1.0 + days_since_observation / 365.0)
```

This produces a value between 0 and 1, where 1.0 means the evidence was observed on the research date and 0.5 means it was observed one year ago.

---

### 7.4 Evidence Weighting

Evidence weighting assigns a numerical weight to each evidence entry, reflecting its contribution to the hypotheses it supports. The weighting is fully deterministic and based on five factors.

#### 7.4.1 Weighting Factors

| Factor | Symbol | Range | Description |
|---|---|---|---|
| Source Reliability | SR | 0.0–1.0 | How trustworthy the data source is |
| Recency | RE | 0.0–1.0 | How recent the evidence is (see Section 7.3.4) |
| Relevance | RL | 0.0–1.0 | How directly the evidence relates to the hypothesis |
| Consensus | CS | 0.0–1.0 | How many independent sources confirm the same finding |
| Structural Importance | SI | 0.0–1.0 | How fundamental the evidence is to market behavior |

#### 7.4.2 Source Reliability (SR)

Source reliability is a fixed value assigned to each data source, maintained in a version-controlled `SourceReliabilityTable`.

| Source Category | SR Value | Examples |
|---|---|---|
| Primary Official | 1.0 | Central bank releases, government statistics |
| Primary Market | 0.95 | Exchange-traded data, real-time feeds |
| Secondary Verified | 0.85 | Bloomberg, Refinitiv, FactSet |
| Secondary Consensus | 0.75 | Survey-based data, consensus estimates |
| Tertiary Derived | 0.60 | Third-party calculations, model outputs |
| Anecdotal | 0.30 | News headlines, social media, unverified reports |

#### 7.4.3 Relevance (RL)

Relevance is computed based on the semantic distance between the evidence's tags and the hypothesis's dependencies.

**Procedure:**

1. Each evidence entry has a set of tags (e.g., `["inflation", "cpi", "us"]`).
2. Each hypothesis has a set of dependency tags (e.g., `["inflation", "monetary-policy", "us"]`).
3. Relevance is computed as the Jaccard similarity:

```
RL = |tags ∩ dependencies| / |tags ∪ dependencies|
```

4. If the intersection is empty, RL = 0.0 (the evidence is not relevant to the hypothesis).
5. If all tags match, RL = 1.0 (maximum relevance).

#### 7.4.4 Consensus (CS)

Consensus measures how many independent sources confirm the same finding.

**Procedure:**

1. For each evidence entry, the system searches the `EvidenceRegistry` for other entries with:
   - The same semantic meaning (determined by tag overlap ≥ 0.8).
   - The same direction of signal (both positive or both negative).
   - A different source.
2. Consensus is computed as:

```
CS = min(1.0, count_of_confirming_sources / 3.0)
```

This means: 1 confirming source → CS = 0.33, 2 → CS = 0.67, 3+ → CS = 1.0.

#### 7.4.5 Structural Importance (SI)

Structural importance measures how fundamental the evidence is to market behavior. This is a fixed value assigned per evidence tag, maintained in a version-controlled `StructuralImportanceTable`.

| Tag Category | SI Value | Rationale |
|---|---|---|
| Central bank policy | 1.0 | Directly drives asset prices |
| Economic growth | 0.95 | Fundamental driver of all markets |
| Inflation | 0.95 | Primary driver of fixed income and currency markets |
| Geopolitical risk | 0.85 | Can cause abrupt market dislocations |
| Technical structure | 0.70 | Reflects collective market psychology |
| Sentiment | 0.60 | Often a lagging indicator |
| Positioning | 0.55 | Can amplify trends but is not causal |
| Flow data | 0.50 | Short-term signal, often noisy |

#### 7.4.6 Final Weight Calculation

The final weight of an evidence entry, relative to a specific hypothesis, is:

```
W = SR × RE × RL × CS × SI × QF
```

Where:
- `SR` = Source Reliability
- `RE` = Recency
- `RL` = Relevance
- `CS` = Consensus
- `SI` = Structural Importance
- `QF` = Quality Factor (product of all quality flag multipliers, or 1.0 if no flags)

**Weight Range:** 0.0 to 1.0. A weight of 0.0 means the evidence has no bearing on the hypothesis. A weight of 1.0 means the evidence is maximally reliable, relevant, recent, confirmed, and structurally important.

**Determinism Note:** Every factor is computed from fixed tables, deterministic formulas, or deterministic lookups. No subjective judgment is involved.

#### 7.4.7 Evidence Aggregation

For each hypothesis, evidence is aggregated into a single **Evidence Score**:

```
ES = Σ(W_i × D_i) / Σ(W_i)
```

Where:
- `W_i` = Weight of evidence entry i
- `D_i` = Directional signal of evidence entry i (+1 for supporting, −1 for contradicting, 0 for neutral)

The Evidence Score ranges from −1.0 (all evidence contradicts) to +1.0 (all evidence supports). A score of 0.0 means evidence is balanced.

**Confidence in Evidence Score:**

```
EC = Σ(W_i) / N
```

Where N is the number of evidence entries. This measures the total weight of evidence, which serves as a proxy for confidence in the Evidence Score.

---

### 7.5 Macro Analysis

Macro analysis evaluates the fundamental economic and policy environment that drives market behavior. It is structured as a deterministic evaluation across five macroeconomic dimensions.

#### 7.5.1 Analytical Dimensions

| Dimension | Description | Key Indicators |
|---|---|---|
| **Monetary Policy** | Central bank actions and forward guidance | Policy rates, balance sheet size, QE/QT, forward guidance |
| **Fiscal Policy** | Government spending and taxation | Deficit/surplus, debt-to-GDP, spending bills, tax changes |
| **Economic Activity** | Real economic growth and sector performance | GDP, PMI, employment, industrial production |
| **Geopolitical** | Political and conflict events | Elections, trade policy, sanctions, military conflicts |
| **Global Liquidity** | Cross-border capital flows and money supply | M2/GDP, cross-border flows, FX reserves, credit conditions |

#### 7.5.2 Macro Regime Classification

The current macro regime is classified using a deterministic decision tree based on two primary axes:

1. **Inflation Regime:** High (>5%) or Low (≤5%)
2. **Growth Regime:** Strong (GDP growth > trend) or Weak (GDP growth ≤ trend)

This produces four base regimes:

| Regime | Inflation | Growth | Typical Characteristics |
|---|---|---|---|
| **Stagflation** | High | Weak | Rising prices, slowing growth, central bank constrained |
| **Reflation** | Low→High | Strong→Weak | Recovery phase, inflation rising from lows |
| **Expansion** | Low | Strong | Healthy growth, stable prices, accommodative policy |
| **Deflationary Slump** | Low | Weak | Falling prices, weak growth, deflationary spiral risk |

**Classification Procedure:**

1. Compute the **Inflation Score** as a weighted average of inflation indicators:
   - CPI YoY (weight: 0.40)
   - Core CPI YoY (weight: 0.30)
   - PCE YoY (weight: 0.20)
   - Inflation expectations 1Y (weight: 0.10)
2. Classify as High if the score exceeds the 60th percentile of its historical range, Low otherwise.
3. Compute the **Growth Score** as a weighted average of growth indicators:
   - Real GDP QoQ (weight: 0.35)
   - Industrial Production MoM (weight: 0.25)
   - Employment Change (weight: 0.25)
   - PMI (weight: 0.15)
4. Classify as Strong if the score exceeds the 50th percentile of its historical range, Weak otherwise.
5. Combine to determine the base regime.

#### 7.5.3 Policy Stance Assessment

For each central bank of interest, the system evaluates the policy stance using a deterministic framework:

1. **Current Policy Rate vs Neutral Rate:**
   - Accommodative if rate < neutral rate
   - Restrictive if rate > neutral rate
   - Neutral if rate ≈ neutral rate (within ±0.25%)

2. **Forward Guidance Assessment:**
   - Dovish if guidance indicates future cuts or slower tightening
   - Hawkish if guidance indicates future hikes or faster tightening
   - Neutral if guidance is ambiguous

3. **Balance Sheet Trajectory:**
   - Accommodative if expanding (QE)
   - Restrictive if contracting (QT)
   - Neutral if stable

4. **Policy Stance Score** = Average of the three assessments (each scored −1.0 to +1.0).

#### 7.5.4 Macro Risk Factor Identification

The system identifies macro risk factors by scanning for:

1. **Policy Uncertainty:** Measured as the standard deviation of policy surprise over the past 250 trading days.
2. **Regime Transition Risk:** Measured as the distance of current indicators from regime boundaries.
3. **Cross-Country Divergence:** Measured as the variance of policy stances across major economies.
4. **External Shock Vulnerability:** Measured as the ratio of external debt to reserves for each country.

Each risk factor is assigned a severity score from 0.0 to 1.0.

#### 7.5.5 Macro Analysis Output

The macro analysis produces a `MacroAnalysis` artifact containing:

```
MacroAnalysis:
  regime:              [Stagflation | Reflation | Expansion | Deflationary Slump]
  policy_stance:       {currency: {bank: {rate: float, stance: float, guidance: string}}}
  risk_factors:        [{factor: string, severity: float, description: string}]
  key_indicators:      {indicator_name: {value: float, trend: string, percentile: float}}
  regime_transition_risk: float
  supporting_evidence: [list of evidence IDs]
  contradicting_evidence: [list of evidence IDs]
```

---

### 7.6 Technical Analysis

Technical analysis evaluates market structure, price action, and quantitative signals derived from market data. All technical analysis in ResearchOS uses rule-based, deterministic methods. No subjective pattern recognition is permitted.

#### 7.6.1 Trend Identification

**Procedure:**

1. **Moving Average Trend:**
   - Compute 20-day, 50-day, and 200-day simple moving averages (SMA).
   - Classify trend as:
     - **Bullish** if price > SMA20 > SMA50 > SMA200
     - **Bearish** if price < SMA20 < SMA50 < SMA200
     - **Mixed** otherwise
   - Assign trend strength as the absolute percentage difference between price and SMA200, normalized to 0.0–1.0.

2. **Price Structure Trend:**
   - Identify higher highs and higher lows (bullish) or lower highs and lower lows (bearish) over the past 25 trading days.
   - Count the number of successful tests of each trend line.
   - Assign a structure score: number of successful tests / 5 (capped at 1.0).

3. **Momentum Trend:**
   - Compute 14-day RSI.
   - Classify as:
     - **Overbought** if RSI > 70
     - **Oversold** if RSI < 30
     - **Neutral** otherwise
   - Momentum strength = |RSI − 50| / 50.

4. **Composite Trend Score:**
   ```
   TS = (MA_trend × 0.40) + (structure_score × 0.35) + (momentum_strength × 0.25)
   ```
   Where MA_trend is +1.0 for bullish, −1.0 for bearish, 0.0 for mixed.

#### 7.6.2 Regime Identification

Market regime is classified using a deterministic framework based on volatility and trend characteristics.

**Procedure:**

1. Compute the **Volatility Regime** using 20-day realized volatility:
   - **High Volatility** if vol > 75th percentile of historical range
   - **Low Volatility** if vol < 25th percentile
   - **Normal Volatility** otherwise

2. Compute the **Trend Regime** using the Composite Trend Score:
   - **Trending** if |TS| > 0.6
   - **Ranging** if |TS| ≤ 0.6

3. Combine to classify the regime:

| Volatility | Trend | Regime |
|---|---|---|
| High | Trending | **Volatile Trend** |
| High | Ranging | **High Volatility Range** |
| Normal | Trending | **Normal Trend** |
| Normal | Ranging | **Normal Range** |
| Low | Trending | **Low Volatility Trend** |
| Low | Ranging | **Low Volatility Range** |

#### 7.6.3 Support and Resistance Mapping

**Procedure:**

1. **Historical Price Levels:**
   - Identify all local maxima and minima over the past 250 trading days.
   - Cluster price levels using a fixed tolerance of 0.5% of the current price.
   - Rank clusters by the number of touches and the volume associated with each touch.

2. **Volume-Weighted Levels:**
   - For each cluster, compute the volume-weighted average price (VWAP) of all trades within the cluster.
   - Assign a strength score: total_volume_at_level / average_daily_volume × 100.

3. **Fibonacci Retracements:**
   - Identify the most recent significant swing high and swing low.
   - Compute retracement levels at 23.6%, 38.2%, 50.0%, 61.8%, and 78.6%.
   - Assign a confluence score based on how many other technical signals align at each level.

4. **Support/Resistance Ranking:**
   - Each level is assigned a composite score:
     ```
     Level_Score = (touch_count × 0.30) + (volume_strength × 0.40) + (confluence × 0.30)
     ```
   - Levels are ranked by score. The top 5 levels above the current price are classified as resistance; the top 5 below are support.

#### 7.6.4 Volatility Profiling

**Procedure:**

1. Compute 10-day, 20-day, and 50-day realized volatility (standard deviation of daily returns).
2. Compute 30-day and 90-day implied volatility (if available).
3. Classify the volatility regime:
   - **Expanding** if 10-day vol > 20-day vol > 50-day vol
   - **Contracting** if 10-day vol < 20-day vol < 50-day vol
   - **Stable** otherwise
4. Compute the **Volatility Risk Premium**:
   ```
   VRP = Implied_Vol - Realized_Vol
   ```
   Positive VRP suggests options are overpriced relative to realized volatility.
5. Assign a volatility regime score:
   - **High** if current vol > 75th percentile
   - **Low** if current vol < 25th percentile
   - **Normal** otherwise

#### 7.6.5 Volume Dynamics

**Procedure:**

1. Compute the **Volume Trend** over 20 trading days:
   - **Increasing** if volume is trending up (linear regression slope > 0)
   - **Decreasing** if volume is trending down
   - **Flat** otherwise

2. Compute the **Volume-Price Relationship:**
   - **Positive Divergence** if price is rising while volume is declining
   - **Negative Divergence** if price is falling while volume is rising
   - **Convergent** if price and volume are moving in the same direction

3. Compute the **Volume Concentration Ratio:**
   ```
   VCR = Volume_in_top_5_trades / Total_volume
   ```
   High VCR (>0.30) suggests institutional participation.

#### 7.6.6 Technical Pattern Recognition

All pattern recognition uses deterministic, rule-based definitions. No machine learning or subjective interpretation.

**Candlestick Patterns (deterministic rules):**

| Pattern | Definition |
|---|---|
| **Hammer** | Body ≤ 25% of range, lower shadow ≥ 2× body, upper shadow ≤ body |
| **Shooting Star** | Body ≤ 25% of range, upper shadow ≥ 2× body, lower shadow ≤ body |
| **Engulfing Bullish** | Day 1 red, Day 2 green, Day 2 body > Day 1 body, Day 2 opens below Day 1 close |
| **Engulfing Bearish** | Day 1 green, Day 2 red, Day 2 body > Day 1 body, Day 2 opens above Day 1 close |

**Chart Patterns (deterministic rules):**

| Pattern | Definition |
|---|---|
| **Double Bottom** | Two equal lows within 3% price range, separated by a peak, neckline defined by the peak |
| **Double Top** | Two equal highs within 3% price range, separated by a valley, neckline defined by the valley |
| **Head and Shoulders** | Left shoulder, head, right shoulder with declining peaks, neckline connecting the two valleys |
| **Ascending Triangle** | Flat resistance line, rising support line, at least 2 touches of each |
| **Descending Triangle** | Flat support line, declining resistance line, at least 2 touches of each |

Each pattern is assigned a **confirmation score** based on:
- Volume confirmation (weight: 0.30)
- Timeframe alignment (weight: 0.25)
- Confluence with other technical signals (weight: 0.25)
- Historical pattern success rate (weight: 0.20)

#### 7.6.7 Technical Analysis Output

The technical analysis produces a `TechnicalAnalysis` artifact:

```
TechnicalAnalysis:
  regime:              [Volatile Trend | High Volatility Range | Normal Trend | Normal Range | Low Volatility Trend | Low Volatility Range]
  trend_score:         float (-1.0 to +1.0)
  trend_strength:      float (0.0 to 1.0)
  support_levels:      [{price: float, strength: float, touches: int}]
  resistance_levels:   [{price: float, strength: float, touches: int}]
  volatility_profile:  {realized: float, implied: float, regime: string, vrp: float}
  volume_analysis:     {trend: string, price_relationship: string, vcr: float}
  patterns:            [{name: string, confidence: float, bullish: bool}]
  supporting_evidence: [list of evidence IDs]
  contradicting_evidence: [list of evidence IDs]
```

---

### 7.7 Liquidity Analysis

Liquidity analysis evaluates the market's ability to absorb trading volume without significant price impact. It covers order flow, depth-of-market, institutional positioning, and liquidity regime changes.

#### 7.7.1 Order Flow Analysis

**Procedure:**

1. **Bid-Ask Pressure:**
   - Compute the **Order Flow Imbalance**:
     ```
     OFI = (Buy_Volume − Sell_Volume) / (Buy_Volume + Sell_Volume)
     ```
   - Classify as:
     - **Buying Pressure** if OFI > 0.1
     - **Selling Pressure** if OFI < −0.1
     - **Balanced** otherwise

2. **Trade Size Distribution:**
   - Compute the average trade size over 20 trading days.
   - Compare to the historical median:
     - **Large Trades** if average > 1.5× historical median
     - **Small Trades** if average < 0.5× historical median
     - **Normal** otherwise

3. **Trade Timing:**
   - Compute the concentration of trades in the first and last 30 minutes of each trading session.
   - Classify as:
     - **Opening Rush** if >40% of volume in first 30 min
     - **Closing Rush** if >40% of volume in last 30 min
     - **Evenly Distributed** otherwise

#### 7.7.2 Depth-of-Market Assessment

**Procedure:**

1. **Market Depth at Best Bid/Ask:**
   - Compute the total quantity available at the best bid and best ask.
   - Compute the **Depth Ratio**:
     ```
     DR = (Bid_Depth + Ask_Depth) / Average_Trade_Size
     ```
   - Classify as:
     - **Deep** if DR > 50
     - **Shallow** if DR < 10
     - **Moderate** otherwise

2. **Depth Decay:**
   - Compute the rate at which depth decreases as you move away from the best bid/ask (first 5 price levels).
   - Classify as:
     - **Rapid Decay** if depth drops >50% by level 3
     - **Gradual Decay** if depth drops <20% by level 3
     - **Moderate Decay** otherwise

3. **Liquidity Concentration:**
   - Compute the **Herfindahl-Hirschman Index** of liquidity across price levels:
     ```
     HHI = Σ(share_i²)
     ```
     Where share_i is the share of total liquidity at price level i.
   - Classify as:
     - **Concentrated** if HHI > 0.25
     - **Diversified** if HHI < 0.10
     - **Moderate** otherwise

#### 7.7.3 Institutional Positioning

**Procedure:**

1. **Commitment of Traders (COT) Data:**
   - Compute the net position of each trader category (commercials, large speculators, small speculators).
   - Compute the **Net Positioning Ratio**:
     ```
     NPR = Net_Position / Open_Interest
     ```
   - Classify positioning as:
     - **Extended Long** if NPR > 0.7
     - **Extended Short** if NPR < −0.7
     - **Neutral** otherwise

2. **Positioning Extremes:**
   - Compare current NPR to its 52-week range.
   - Classify as:
     - **Extreme** if in top/bottom 5% of historical range
     - **Elevated** if in top/bottom 25%
     - **Normal** otherwise

3. **Positioning Divergence:**
   - Compare the positioning of different trader categories.
   - Compute the **Divergence Score**:
     ```
     DS = |NPR_commercials − NPR_large_specs|
     ```
   - High divergence suggests conflicting market views.

#### 7.7.4 Liquidity Regime Changes

**Procedure:**

1. **Liquidity Stress Indicators:**
   - Bid-ask spread widening (vs 20-day average)
   - Market depth contraction (vs 20-day average)
   - Trading volume decline (vs 20-day average)
   - Price impact increase (vs 20-day average)

2. **Liquidity Regime Classification:**
   - **Abundant** if all four indicators are improving
   - **Stressed** if all four indicators are deteriorating
   - **Normal** otherwise

3. **Regime Transition Detection:**
   - Compute the **Liquidity Regime Score** as the average of the four normalized indicators.
   - Detect regime transitions when the score crosses predefined thresholds:
     - Transition to Stressed: score < −0.5
     - Transition to Abundant: score > +0.5

#### 7.7.5 Transaction Cost Analysis

**Procedure:**

1. **Effective Spread:**
   ```
   Effective_Spread = (Sale_Price − Buy_Price) / Mid_Price
   ```
   Computed for each trade and averaged over 20 trading days.

2. **Market Impact:**
   ```
   Impact = (Execution_Price − Decision_Price) / Decision_Price
   ```
   Computed for each trade and averaged.

3. **Slippage:**
   ```
   Slippage = (Execution_Price − VWAP) / VWAP
   ```
   Computed for each trade and averaged.

4. **Transaction Cost Score:**
   ```
   TCS = (Effective_Spread × 0.40) + (|Impact| × 0.35) + (|Slippage| × 0.25)
   ```

#### 7.7.6 Liquidity Analysis Output

The liquidity analysis produces a `LiquidityAnalysis` artifact:

```
LiquidityAnalysis:
  order_flow:        {ofi: float, pressure: string, trade_size_regime: string, timing: string}
  depth:             {depth_ratio: float, decay: string, hhi: float, concentration: string}
  positioning:       {npr: float, extremeness: string, divergence: float}
  regime:            [Abundant | Stressed | Normal]
  regime_score:      float (-1.0 to +1.0)
  transaction_costs: {effective_spread: float, impact: float, slippage: float, tcs: float}
  regime_transitions: [{date: timestamp, from: string, to: string, score: float}]
  supporting_evidence: [list of evidence IDs]
  contradicting_evidence: [list of evidence IDs]
```

---

### 7.8 Market Narrative

The market narrative is a structured, deterministic synthesis of the macro, technical, and liquidity analyses. It tells the story of why the market is behaving as it is, supported by evidence.

#### 7.8.1 Narrative Structure

Every narrative has the following deterministic structure:

```
Narrative:
  thesis:            [The central claim of the narrative]
  timeframe:        [Intraday | Daily | Weekly | Monthly | Quarterly]
  primary_driver:   [The dominant force driving market behavior]
  supporting_drivers: [Secondary forces]
  evidence_base:    [list of evidence IDs that support the narrative]
  evidence_strength: float (0.0 to 1.0)
  coherence_score:  float (0.0 to 1.0)
  plausibility_score: float (0.0 to 1.0)
  historical_precedent: {period: string, similarity: float, outcome: string}
  catalysts:        [{event: string, date: timestamp, impact: float}]
  invalidation_conditions: [list of conditions that would invalidate the narrative]
```

#### 7.8.2 Narrative Construction Procedure

**Procedure:**

1. **Driver Identification:**
   - The system examines the `MacroAnalysis`, `TechnicalAnalysis`, and `LiquidityAnalysis` artifacts.
   - For each analysis, the system identifies the top 3 drivers (by evidence weight) from each dimension.
   - The system ranks all drivers across dimensions by their composite evidence score.

2. **Primary Driver Selection:**
   - The driver with the highest composite evidence score becomes the primary driver.
   - The primary driver must be supported by evidence from at least 2 of the 3 analytical dimensions.
   - If no driver meets this criterion, the narrative is classified as "Multi-Factor Uncertain."

3. **Narrative Thesis Formation:**
   - The thesis is constructed using a fixed template:
     ```
     "The market is currently in a [regime] regime, primarily driven by [primary_driver].
     This is evidenced by [key evidence from macro], [key evidence from technical],
     and [key evidence from liquidity]. The dominant force is [primary_driver]
     because [explanation based on evidence weights]."
     ```
   - The template is filled deterministically using the analysis results.

4. **Coherence Assessment:**
   - The system checks that all three analyses point in the same direction:
     - **High Coherence** (score 1.0) if all three agree.
     - **Medium Coherence** (score 0.67) if two of three agree.
     - **Low Coherence** (score 0.33) if only one analysis supports the narrative.
     - **No Coherence** (score 0.0) if analyses conflict.

5. **Plausibility Assessment:**
   - The system searches the historical database for similar narrative conditions.
   - Plausibility = average historical outcome similarity × time proximity weight.
   - Historical outcomes are scored on a 0.0–1.0 scale based on how closely they match the current narrative.

6. **Catalyst Identification:**
   - The system scans the upcoming event calendar (within the narrative's timeframe).
   - Each event is scored for potential impact:
     - **High Impact** (0.8–1.0) if the event has historically caused >2% market moves.
     - **Medium Impact** (0.5–0.8) if 1–2% moves.
     - **Low Impact** (0.0–0.5) if <1% moves.

7. **Invalidation Conditions:**
   - For each supporting evidence entry, the system derives the condition that would contradict it.
   - These conditions are aggregated into a list of narrative invalidation conditions.
   - Each condition is assigned a probability of occurrence (based on historical frequency).

#### 7.8.3 Narrative Evolution Tracking

The system tracks how narratives evolve over time:

1. **Narrative Persistence:** If the same thesis appears in consecutive research cycles, the persistence score increases.
2. **Narrative Shifts:** When the primary driver changes, a narrative shift is recorded.
3. **Narrative Maturation:** As evidence accumulates, the narrative's confidence increases.

#### 7.8.4 Narrative Output

The narrative is stored as a `Narrative` artifact and included in the `ResearchReport`.

---

### 7.9 Scenario Generation

Scenario generation produces a set of probabilistic future market states, each with defined validity and invalidity conditions. Scenarios are generated deterministically from the narrative, evidence, and historical data.

#### 7.9.1 Scenario Types

| Type | Description | Typical Count |
|---|---|---|
| **Base Scenario** | Most likely outcome given current evidence | 1 |
| **Bull Scenario** | Optimistic outcome, above-median returns | 1 |
| **Bear Scenario** | Pessimistic outcome, below-median returns | 1 |
| **Tail Scenarios** | Low-probability, high-impact events | 2–4 |

#### 7.9.2 Scenario Generation Procedure

**Procedure:**

1. **Base Scenario Construction:**
   - The base scenario is constructed directly from the narrative.
   - The scenario's outcome is the narrative's thesis, projected forward.
   - The probability is computed from the narrative's evidence strength and coherence:
     ```
     P_base = (evidence_strength × 0.50) + (coherence_score × 0.30) + (plausibility_score × 0.20)
     ```

2. **Bull/Bear Scenario Construction:**
   - The bull scenario assumes the primary driver is stronger than the base case.
   - The bear scenario assumes the primary driver is weaker or reversed.
   - Probabilities are computed as:
     ```
     P_bull = (1.0 − P_base) × 0.40
     P_bear = (1.0 − P_base) × 0.40
     ```
   - The remaining 20% is distributed among tail scenarios.

3. **Tail Scenario Generation:**
   - Tail scenarios are generated from the narrative's invalidation conditions.
   - Each invalidation condition becomes a tail scenario with the condition as its trigger.
   - Probability is assigned based on historical frequency:
     ```
     P_tail_i = (1.0 − P_base − P_bull − P_bear) × (historical_frequency_i / Σ historical_frequencies)
     ```

4. **Scenario Outcome Specification:**
   - Each scenario specifies:
     - **Expected Return** (point estimate)
     - **Return Range** (5th–95th percentile)
     - **Volatility** (expected standard deviation)
     - **Key Milestones** (events that would confirm or refute the scenario)
     - **Market Regime** (which regime the scenario implies)

5. **Probability Normalization:**
   - All scenario probabilities are normalized to sum to 1.0.
   - If the sum deviates from 1.0 by more than 0.01, the system adjusts the base scenario probability.

#### 7.9.3 Scenario Validity Conditions

Every scenario must specify explicit conditions under which it would be considered **valid** and **invalid**.

**Procedure:**

1. **Valid If Conditions:**
   - Derived from the scenario's supporting evidence.
   - Each supporting evidence entry contributes one valid-if condition.
   - Conditions are combined with AND logic (all must be true for the scenario to be valid).

2. **Invalid If Conditions:**
   - Derived from contradicting evidence and narrative invalidation conditions.
   - Each contradicting evidence entry contributes one invalid-if condition.
   - Conditions are combined with OR logic (any one being true invalidates the scenario).

3. **Condition Format:**
   ```
   Condition:
     metric:     [e.g., "10-year yield", "S&P 500 price", "VIX"]
     operator:   [">", "<", ">=", "<=", "==", "!="]
     threshold:  float
     timeframe:  [Intraday | Daily | Weekly | Monthly | Quarterly]
     horizon:    [number of periods]
   ```

4. **Condition Monitoring:**
   - The system monitors all conditions daily (or at the appropriate frequency).
   - When a condition is triggered, the scenario's validity status is updated.
   - All status changes are recorded in the audit trail.

#### 7.9.4 Scenario Dependencies

Scenarios may depend on each other:

- **Mutually Exclusive:** Only one can be valid at a time (base, bull, bear).
- **Independent:** Can be valid simultaneously (different tail scenarios).
- **Conditional:** One scenario's validity depends on another's invalidity.

#### 7.9.5 Scenario Output

The scenario set is stored as a `ScenarioSet` artifact:

```
ScenarioSet:
  scenarios: [
    {
      id: string,
      type: [Base | Bull | Bear | Tail],
      thesis: string,
      probability: float,
      expected_return: float,
      return_range: {p5: float, p95: float},
      volatility: float,
      regime: string,
      valid_if: [list of conditions],
      invalid_if: [list of conditions],
      dependencies: [list of scenario IDs],
      supporting_evidence: [list of evidence IDs],
      contradicting_evidence: [list of evidence IDs],
      milestones: [{event: string, date: timestamp, impact: float}]
    }
  ]
  probability_calibration: float
  scenario_diversity: float
```

---

### 7.10 Confidence Estimation

Confidence estimation assigns probability estimates to scenarios and conclusions, along with explicit uncertainty ranges. All estimates are calibrated against historical data.

#### 7.10.1 Confidence Factors

Each scenario's confidence is computed from five factors:

| Factor | Symbol | Range | Description |
|---|---|---|---|
| Evidence Strength | ES | 0.0–1.0 | Total weighted evidence supporting the scenario |
| Coherence | CO | 0.0–1.0 | Agreement across analytical dimensions |
| Historical Precedent | HP | 0.0–1.0 | How often similar scenarios were correct |
| Model Uncertainty | MU | 0.0–1.0 | Confidence in the analytical models used |
| Recency | RE | 0.0–1.0 | How recent the supporting evidence is |

#### 7.10.2 Confidence Calculation

**Procedure:**

1. **Evidence Strength (ES):**
   ```
   ES = Σ(W_i) / max(Σ(W_i))
   ```
   Where W_i are the weights of all evidence supporting the scenario, and max(Σ(W_i)) is the maximum possible evidence strength (computed from the full evidence registry).

2. **Coherence (CO):**
   ```
   CO = (n_agree / n_total)
   ```
   Where n_agree is the number of analytical dimensions that agree with the scenario, and n_total is the total number of dimensions (always 3).

3. **Historical Precedent (HP):**
   - Search the historical database for scenarios with similar evidence patterns.
   - HP = fraction of those scenarios that were correct.
   - If no historical precedent exists, HP = 0.5 (neutral).

4. **Model Uncertainty (MU):**
   - Each analytical model has a fixed uncertainty score (maintained in a version-controlled table).
   - MU = average of the uncertainty scores of all models used in the scenario.
   - Lower MU means higher confidence in the models.

5. **Recency (RE):**
   - RE = average recency of all supporting evidence entries.

6. **Composite Confidence:**
   ```
   C = (ES × 0.30) + (CO × 0.25) + (HP × 0.20) + (MU × 0.15) + (RE × 0.10)
   ```

#### 7.10.3 Confidence Intervals

Every probability estimate includes an explicit confidence interval:

```
CI = C ± (1.0 − C) × z × σ
```

Where:
- `C` = composite confidence
- `z` = z-score for the desired confidence level (1.96 for 95%)
- `σ` = standard error of the confidence estimate

The standard error is computed as:
```
σ = sqrt(C × (1 − C) / N)
```

Where N is the number of independent evidence entries supporting the scenario.

#### 7.10.4 Confidence Calibration

The system maintains a **Calibration Table** that tracks how well past probability estimates matched actual outcomes.

**Procedure:**

1. **Calibration Bin Creation:**
   - Past probability estimates are grouped into bins of width 0.1 (0.0–0.1, 0.1–0.2, etc.).
   - For each bin, the system computes the observed frequency of correct outcomes.

2. **Calibration Adjustment:**
   - If a bin's observed frequency differs from the bin's midpoint by more than 0.05, the system applies a calibration adjustment.
   - The adjustment is:
     ```
     Adjusted_Probability = Observed_Frequency + (Raw_Probability − Bin_Midpoint)
     ```

3. **Calibration Quality:**
   - The system computes the **Calibration Error** as the mean absolute difference between bin midpoints and observed frequencies.
   - A calibration error below 0.05 is considered well-calibrated.

#### 7.10.5 Confidence Reporting

The confidence report includes:

```
ConfidenceReport:
  scenario_confidences: [
    {
      scenario_id: string,
      raw_probability: float,
      calibrated_probability: float,
      confidence_interval: {lower: float, upper: float},
      confidence_score: float,
      calibration_error: float,
      contributing_factors: {
        evidence_strength: float,
        coherence: float,
        historical_precedent: float,
        model_uncertainty: float,
        recency: float
      }
    }
  ]
  overall_confidence: float
  calibration_status: [Well-Calibrated | Needs Adjustment | Poorly Calibrated]
```

---

### 7.11 Contradiction Detection

Contradiction detection identifies conflicts between evidence, analyses, narratives, and scenarios. All contradictions are flagged and must be resolved or explicitly acknowledged.

#### 7.11.1 Contradiction Types

| Type | Description | Example |
|---|---|---|
| **Cross-Dimensional** | Macro, technical, and liquidity analyses disagree | Macro says bullish, technical says bearish |
| **Temporal** | Recent evidence contradicts older evidence | Recent data reverses a long-standing trend |
| **Source** | Different data sources report conflicting values | Two CPI sources report different numbers |
| **Narrative** | Evidence doesn't support the narrative thesis | Narrative says inflation-driven, but evidence is technical |
| **Scenario** | Scenarios have overlapping validity conditions | Two scenarios can both be valid simultaneously |
| **Historical** | Current conditions contradict historical precedent | Pattern suggests bullish, but history says bearish |

#### 7.11.2 Contradiction Detection Procedure

**Procedure:**

1. **Cross-Dimensional Contradiction Check:**
   - Compare the directional signals from Macro, Technical, and Liquidity analyses.
   - A contradiction exists if:
     - Two analyses agree and the third disagrees (partial contradiction).
     - All three analyses disagree (full contradiction).
   - Severity is computed as:
     ```
     Severity = (n_disagree / n_total) × average_weight_of_disagreeing_evidence
     ```

2. **Temporal Contradiction Check:**
   - Compare evidence from the most recent 10% of the look-back period with evidence from the earlier 90%.
   - A contradiction exists if the directional signals differ.
   - Severity is computed based on the weight of the contradicting evidence.

3. **Source Contradiction Check:**
   - For each evidence entry, search for other entries from different sources with the same semantic meaning.
   - A contradiction exists if the values differ by more than a predefined threshold (2% for prices, 0.5% for rates).
   - Severity is computed based on the reliability of the conflicting sources.

4. **Narrative Contradiction Check:**
   - For each piece of evidence in the narrative's evidence base, check if it actually supports the narrative thesis.
   - A contradiction exists if any evidence entry contradicts the thesis.
   - Severity is computed based on the weight of the contradicting evidence.

5. **Scenario Contradiction Check:**
   - For each pair of scenarios, check if their validity conditions overlap.
   - A contradiction exists if two scenarios can both be valid simultaneously when they should be mutually exclusive.
   - Severity is computed based on the probability mass of the overlapping scenarios.

6. **Historical Contradiction Check:**
   - For each scenario, search the historical database for similar conditions.
   - A contradiction exists if the historical outcomes consistently disagree with the scenario.
   - Severity is computed based on the strength of the historical evidence.

#### 7.11.3 Contradiction Resolution

**Procedure:**

1. **Automatic Resolution:**
   - If a contradiction can be resolved by evidence weighting (one side has significantly higher weight), the system automatically resolves it.
   - Resolution threshold: the higher-weight side must have at least 2× the weight of the lower-weight side.

2. **Flagged Resolution:**
   - If automatic resolution is not possible, the contradiction is flagged for human review.
   - The system provides:
     - The nature of the contradiction.
     - The evidence on each side.
     - The weights and sources of each piece of evidence.
     - A recommendation based on evidence weights.

3. **Unresolved Contradictions:**
   - If the Human Trader does not resolve a contradiction, it is carried forward in the report.
   - The contradiction reduces the confidence score of the affected conclusions.
   - The contradiction is tracked in the audit trail for future analysis.

#### 7.11.4 Contradiction Report

```
ContradictionReport:
  contradictions: [
    {
      id: string,
      type: [Cross-Dimensional | Temporal | Source | Narrative | Scenario | Historical],
      severity: float (0.0–1.0),
      description: string,
      sides: [
        {
          label: string,
          evidence: [list of evidence IDs],
          total_weight: float,
          directional_signal: float
        }
      ],
      resolution: [Auto-Resolved | Flagged | Unresolved],
      resolution_details: string
    }
  ]
  overall_contradiction_score: float
  confidence_impact: float
```

---

### 7.12 Research Report Generation

The research report is the final output of the research lifecycle. It is a structured, deterministic document that presents all findings in a clear, auditable format.

#### 7.12.1 Report Structure

```
ResearchReport:
  metadata:          ReportMetadata
  executive_summary: ExecutiveSummary
  research_question: ResearchQuestion
  hypotheses:        HypothesisSet
  evidence:          EvidenceRegistry (summary)
  analyses:          {macro: MacroAnalysis, technical: TechnicalAnalysis, liquidity: LiquidityAnalysis}
  narrative:         Narrative
  scenarios:         ScenarioSet
  confidence:        ConfidenceReport
  contradictions:    ContradictionReport
  validation_plan:   ValidationPlan
  appendices:        Appendices
```

#### 7.12.2 Report Sections

**1. Metadata:**
- Report ID (deterministic UUID)
- Research timestamp
- Author (Human Trader)
- Methodology version
- Data sources used
- Look-back period

**2. Executive Summary:**
- Key conclusion (one sentence)
- Primary scenario probability
- Confidence level
- Major contradictions
- Key risks

**3. Research Question:**
- The original question (verbatim)
- Time horizon
- Decision context

**4. Hypotheses:**
- All hypotheses with their validity/invalidity conditions
- Evidence supporting or contradicting each hypothesis

**5. Evidence Summary:**
- Total evidence count
- Evidence by type
- Evidence by dimension
- Top 10 evidence entries by weight

**6. Analyses:**
- Full Macro, Technical, and Liquidity analysis results
- Supporting and contradicting evidence for each
- Regime classifications

**7. Narrative:**
- The market narrative thesis
- Supporting evidence
- Coherence and plausibility scores
- Catalysts and invalidation conditions

**8. Scenarios:**
- All scenarios with probabilities
- Validity/invalidity conditions
- Return expectations and volatility
- Milestones

**9. Confidence:**
- Confidence scores for each scenario
- Confidence intervals
- Calibration status
- Contributing factors

**10. Contradictions:**
- All detected contradictions
- Severity scores
- Resolution status
- Impact on confidence

**11. Validation Plan:**
- How the research will be validated (see Section 7.13)
- Key metrics to track
- Timeline for validation

**12. Appendices:**
- Full evidence registry
- Raw data sources
- Calculation details
- Historical precedent data

#### 7.12.3 Report Generation Procedure

**Procedure:**

1. **Template Selection:**
   - The system selects a report template based on the research question type.
   - Templates are fixed, version-controlled documents.

2. **Data Population:**
   - Each section is populated deterministically from the corresponding artifact.
   - All values are formatted using fixed formatting rules.

3. **Cross-Reference Validation:**
   - The system validates that all cross-references (evidence IDs, scenario IDs, etc.) are consistent.
   - Any inconsistency is flagged as an error.

4. **Quality Check:**
   - The system checks that:
     - All hypotheses have supporting evidence.
     - All scenarios have validity conditions.
     - All confidence estimates have intervals.
     - All contradictions are documented.
   - Any missing element is flagged.

5. **Final Assembly:**
   - The report is assembled in the specified format (Markdown, PDF, or JSON).
   - A deterministic hash of the report content is computed and stored.
   - The report is stored in the audit trail.

#### 7.12.4 Report Formats

Reports can be generated in three formats:

| Format | Use Case |
|---|---|
| **Markdown** | Human-readable, version-controlled |
| **PDF** | Formal presentation, printing |
| **JSON** | Machine-readable, API integration |

All formats contain identical content, just different serialization.

---

### 7.13 Validation Integration

Every research report includes a validation plan that specifies how the research will be tested against reality. This is the bridge between the Market Intelligence Engine and the Research Validation Engine (see Article V).

#### 7.13.1 Validation Plan Structure

```
ValidationPlan:
  report_id: string
  validation_targets: [
    {
      target: string,
      metric: string,
      expected_value: float,
      actual_value: float (to be filled later),
      tolerance: float,
      timeframe: string,
      status: [Pending | Validated | Invalidated | Partial]
    }
  ]
  scenario_tracking: [
    {
      scenario_id: string,
      monitoring_frequency: string,
      key_conditions: [list of conditions to monitor],
      tracking_status: [Active | Resolved | Expired]
    }
  ]
  quality_metrics: [
    {
      metric: string,
      target: float,
      current: float
    }
  ]
```

#### 7.13.2 Validation Target Generation

**Procedure:**

1. For each scenario in the `ScenarioSet`, the system generates validation targets for:
   - The expected return (with tolerance)
   - The return range boundaries
   - The volatility estimate
   - Each milestone event

2. For each hypothesis in the `HypothesisSet`, the system generates validation targets for:
   - The hypothesis's valid-if conditions
   - The hypothesis's invalid-if conditions

3. For the narrative, the system generates validation targets for:
   - The primary driver's expected behavior
   - The coherence score's expected evolution
   - The plausibility score's expected accuracy

#### 7.13.3 Scenario Monitoring

**Procedure:**

1. The system monitors each scenario's validity conditions daily (or at the appropriate frequency).
2. When a condition is triggered, the system:
   - Updates the scenario's status.
   - Records the event in the audit trail.
   - Sends a notification to the Human Trader (for review, not for action).
3. When all conditions for a scenario are resolved (either valid or invalid), the scenario is marked as "Resolved."
4. The system computes the scenario's outcome and compares it to the expected outcome.

#### 7.13.4 Quality Metric Tracking

The system tracks the following quality metrics for each research report:

| Metric | Description |
|---|---|
| **Accuracy** | Fraction of scenarios that were correct |
| **Calibration** | How well probability estimates matched outcomes |
| **Timeliness** | How early key signals were detected |
| **Completeness** | Fraction of evidence collected vs. available |
| **Relevance** | How relevant the evidence was to the question |

These metrics feed into the Research Validation Engine (Article V, Section 5.3).

---

### 7.14 Determinism and Explainability Guarantees

This section documents the guarantees that ensure every research output is deterministic and explainable.

#### 7.14.1 Determinism Guarantees

**G1: Input Determinism**
- All inputs to the research methodology are explicitly defined and versioned.
- Data sources are identified by fixed URIs.
- Parameters are stored in version-controlled configuration files.

**G2: Procedure Determinism**
- Every procedure in this document is defined as a fixed sequence of steps.
- No step involves randomness, subjective judgment, or machine learning inference.
- All formulas use fixed coefficients and thresholds.

**G3: Output Determinism**
- Given the same inputs and the same version of this methodology, the same outputs are guaranteed.
- A deterministic hash of the output is computed and stored for verification.
- Any change to inputs or methodology produces a different hash, indicating a change in output.

**G4: Reproducibility**
- Every research report includes a full list of inputs, parameters, and methodology version.
- Any researcher can reproduce the report by following the same procedure with the same inputs.
- The audit trail contains all intermediate artifacts.

#### 7.14.2 Explainability Guarantees

**G5: Traceability**
- Every conclusion in the research report is linked to its supporting evidence.
- Every evidence entry is linked to its source and collection method.
- Every weight is linked to its calculation factors.
- Every probability is linked to its contributing factors.

**G6: Plain-Language Explanations**
- Every technical term is defined in the glossary (Article IV).
- Every calculation is explained in plain language alongside the formula.
- Every conclusion includes a "Why this conclusion?" section that explains the reasoning.

**G7: Right to Explanation**
- The Human Trader can request an explanation of any conclusion at any time.
- The system provides a step-by-step trace from the conclusion to its supporting evidence.
- The explanation includes the weights, factors, and formulas used.

**G8: Transparency of AI Contribution**
- Any AI-assisted analysis is clearly labeled.
- The system distinguishes between human-authored and machine-generated content.
- All machine-generated content is produced by deterministic procedures, not stochastic models.

#### 7.14.3 Audit Trail Requirements

Every research cycle produces the following artifacts, all stored in the immutable audit trail:

| Artifact | Description |
|---|---|
| `ResearchQuestion` | The original question |
| `HypothesisSet` | All hypotheses |
| `EvidenceRegistry` | All evidence collected |
| `MacroAnalysis` | Macro analysis results |
| `TechnicalAnalysis` | Technical analysis results |
| `LiquidityAnalysis` | Liquidity analysis results |
| `Narrative` | The market narrative |
| `ScenarioSet` | All scenarios |
| `ConfidenceReport` | Confidence estimates |
| `ContradictionReport` | All contradictions |
| `ResearchReport` | The final report |
| `ValidationPlan` | The validation plan |

Each artifact includes:
- A deterministic UUID
- A timestamp
- The author (human or system)
- The methodology version used
- A hash of the artifact content
- Links to all input artifacts

#### 7.14.4 Version Control

All methodology versions, parameter sets, and data source definitions are version-controlled. Each version is identified by a semantic version number (MAJOR.MINOR.PATCH).

- **MAJOR** versions introduce breaking changes to the methodology.
- **MINOR** versions add new features without breaking changes.
- **PATCH** versions fix bugs or clarify existing procedures.

When a methodology version changes, all affected research reports are flagged for re-validation.

---

### 7.15 Methodology Summary

The ResearchOS research methodology is a deterministic, explainable pipeline that transforms market data into institutional-grade research. It is organized as follows:

1. **Research Lifecycle** (7.2): A nine-stage pipeline from question to report.
2. **Evidence Collection** (7.3): Systematic, metadata-rich gathering of all relevant data.
3. **Evidence Weighting** (7.4): Deterministic weighting based on reliability, recency, relevance, consensus, and structural importance.
4. **Macro Analysis** (7.5): Five-dimensional evaluation of the fundamental environment.
5. **Technical Analysis** (7.6): Rule-based evaluation of market structure and price action.
6. **Liquidity Analysis** (7.7): Systematic assessment of market liquidity and depth.
7. **Market Narrative** (7.8): Structured synthesis of all analyses into a coherent story.
8. **Scenario Generation** (7.9): Probabilistic scenarios with explicit validity conditions.
9. **Confidence Estimation** (7.10): Calibrated probability estimates with uncertainty ranges.
10. **Contradiction Detection** (7.11): Systematic identification and resolution of conflicts.
11. **Research Report Generation** (7.12): Structured, auditable final output.
12. **Validation Integration** (7.13): Bridge to the Research Validation Engine.
13. **Determinism and Explainability** (7.14): Guarantees that ensure the methodology is always reproducible and traceable.

---

*This concludes Article VII: Research Methodology. The next article (Article VIII) will define the Research Validation methodology.*
