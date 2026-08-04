# ResearchOS Macro Intelligence Layer — Contract Architecture

**Version:** 1.0.0-frozen
**Date:** 2026-08-03
**Status:** ARCHITECTURALLY FROZEN — Ready for Implementation
**Classification:** Internal — Quantitative Platform

---

## Table of Contents

1. [Contract Overview](#1-contract-overview)
2. [Core Data Contracts](#2-core-data-contracts)
3. [Interface Definitions](#3-interface-definitions)
4. [Revision Model](#4-revision-model)
5. [Dependency Rules](#5-dependency-rules)
6. [Versioning Strategy](#6-versioning-strategy)
7. [Extension Rules](#7-extension-rules)
8. [Module Ownership](#8-module-ownership)
9. [Implementation Roadmap](#9-implementation-roadmap)

---

## 1. Contract Overview

### 1.1 Purpose

The Macro Intelligence Layer (MIL) provides auditable, versioned, immutable contracts for macroeconomic data ingestion, storage, and consumption. All contracts are frozen in this document. Implementation must conform to these specifications without modification.

### 1.2 Design Principles

| Principle | Enforcement |
|-----------|-------------|
| **Immutability** | All evidence and event objects are frozen; never modified after creation |
| **Provenance** | Every datum carries original source information |
| **Versioning** | All contracts have explicit version numbers; changes are additive only |
| **Isolation** | MIL cannot import from V1 Core; V1 Core cannot import from MIL |
| **Determinism** | Serialization is deterministic; same input → same output bytes |
| **Auditability** | Every observation is traceable to source with quality metadata |

### 1.3 Contract Lifecycle

```
DESIGN → REVIEW → FREEZE → IMPLEMENT → DEPLOY
                ↑
         This document (v1.0.0-frozen)
```

### 1.4 Scope

**Supported Data Types:**
- DXY (US Dollar Index)
- US Treasury Yields (2Y, 5Y, 10Y, 30Y)
- Real Yield (10Y)
- CPI / Core CPI (YoY, MoM)
- PPI / Core PPI (YoY)
- PCE / Core PCE (YoY)
- NFP (Non-Farm Payrolls)
- Unemployment Rate
- JOLTS (Openings, Hires, Separations)
- FOMC Decisions & Statements
- Fed Speeches
- GDP (YoY, QoQ Annualized)
- ISM Manufacturing PMI
- ISM Services PMI
- VIX
- MOVE Index
- Gold ETF Flows
- Central Bank Gold Purchases

**Not in Scope (V1 Core):**
- Quant engine
- Experiment tracking
- Execution logic
- Trading strategy
- Portfolio management

---

## 2. Core Data Contracts

### 2.1 NormalizedSeries Contract

**Version:** `ms/v1`
**Module:** `macro_intelligence.contracts.series`
**Status:** Frozen

#### 2.1.1 Purpose

Canonical representation of macroeconomic time-series data. Every observation from every source is normalized to this contract before storage or consumption.

#### 2.1.2 Schema Definition

```
NormalizedSeries (frozen)
├── series_id: string              # Unique identifier for the time series
├── source: string                 # Originating data source
├── timestamp: datetime            # When this record was created
├── observation_period: date       # The period this observation represents
├── release_time: datetime | null  # When the data was officially released
├── available_time: datetime       # When the data became available in MIL
├── value: float | null            # The observed value (null = missing)
├── unit: string                   # Unit of measurement
├── frequency: FrequencyEnum       # daily | weekly | monthly | quarterly | ad_hoc
├── revision_id: string | null     # Revision chain identifier
├── quality_score: float           # 0.0–1.0 quality rating
└── metadata: dict                 # Source-specific metadata
```

#### 2.1.3 Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `series_id` | `string` | UUID v7 format: `SER_{YYYYMMDD}_{seq}` | Globally unique series identifier |
| `source` | `string` | Non-empty, max 128 chars | Canonical source name (e.g., "FRED", "BLS", "ICE") |
| `timestamp` | `datetime` | ISO 8601, UTC | Record creation timestamp |
| `observation_period` | `date` | Valid date | The period the observation represents |
| `release_time` | `datetime \| null` | ISO 8601, UTC | Official release timestamp (null if not yet released) |
| `available_time` | `datetime` | ISO 8601, UTC | When data became available in MIL storage |
| `value` | `float \| null` | None or valid float | The observed value (null = missing/unavailable) |
| `unit` | `string` | Enum: "index", "percent", "percent_ann", "basis_points", "thousands", "text" | Standardized unit |
| `frequency` | `FrequencyEnum` | Enum value | Data frequency classification |
| `revision_id` | `string \| null` | UUID v7 or null | Links to revision chain (null = initial) |
| `quality_score` | `float` | Range [0.0, 1.0] | Quality rating from validation |
| `metadata` | `dict` | JSON-serializable | Source-specific provenance data |

#### 2.1.4 Supported Series Registry

| series_id | Name | Unit | Frequency | Source |
|-----------|------|------|-----------|--------|
| `DXY` | US Dollar Index | index | daily | ICE |
| `US2Y` | US Treasury 2-Year Yield | percent | daily | FRED/Treasury |
| `US5Y` | US Treasury 5-Year Yield | percent | daily | FRED/Treasury |
| `US10Y` | US Treasury 10-Year Yield | percent | daily | FRED/Treasury |
| `US30Y` | US Treasury 30-Year Yield | percent | daily | FRED/Treasury |
| `REAL_10Y` | 10-Year Real Yield | percent | daily | FRED (computed) |
| `CPI_YOY` | CPI Year-over-Year | percent | monthly | BLS/FRED |
| `CPI_CORE_YOY` | Core CPI Year-over-Year | percent | monthly | BLS/FRED |
| `CPI_MOM` | CPI Month-over-Month | percent | monthly | BLS/FRED |
| `PPI_YOY` | PPI Year-over-Year | percent | monthly | BLS/FRED |
| `PPI_CORE_YOY` | Core PPI Year-over-Year | percent | monthly | BLS/FRED |
| `PCE_YOY` | PCE Year-over-Year | percent | monthly | BEA/FRED |
| `PCE_CORE_YOY` | Core PCE Year-over-Year | percent | monthly | BEA/FRED |
| `NFP_CHANGE` | Non-Farm Payrolls Change | thousands | monthly | BLS |
| `UNRATE` | Unemployment Rate | percent | monthly | BLS/FRED |
| `JOLTS_TOTAL` | JOLTS Job Openings | thousands | monthly | BLS |
| `JOLTS_HIRINGS` | JOLTS Hires | thousands | monthly | BLS |
| `JOLTS_SEPARATIONS` | JOLTS Separations | thousands | monthly | BLS |
| `GDP_YOY` | GDP Year-over-Year | percent | quarterly | BEA/FRED |
| `GDP_MOM` | GDP QoQ Annualized | percent | quarterly | BEA/FRED |
| `PMI_MFG` | ISM Manufacturing PMI | index | monthly | ISM |
| `PMI_SVC` | ISM Services PMI | index | monthly | ISM |
| `VIX` | CBOE Volatility Index | index | daily | CBOE |
| `MOVE` | ICE BofA MOVE Index | index | daily | Goldman |
| `GLD_FLOWS` | SPDR Gold ETF Flows | millions_usd | daily | State Street |
| `CB_GOLD_PURCHASES` | Central Bank Gold Purchases | tonnes | quarterly | WGC |

#### 2.1.5 Immutability Rules

1. **Once stored, a NormalizedSeries record is never modified**
2. **Revisions create new records** with updated `revision_id` and `value`
3. **Original source information is preserved** in `metadata`
4. **Quality scores are recalculated** on re-validation but original records remain

#### 2.1.6 Missing Value Handling

| Condition | `value` | `quality_score` |
|-----------|---------|-----------------|
| Data not yet released | `null` | `0.0` |
| Data released but invalid | `null` | `0.1–0.3` |
| Data with warnings | `valid` | `0.4–0.7` |
| Valid data | `valid` | `0.8–1.0` |

#### 2.1.7 Revision Chain

```
Initial Release:
  series_id: SER_20260801_001
  revision_id: null
  value: 2.4
  quality_score: 1.0

First Revision:
  series_id: SER_20260815_001
  revision_id: REV_20260815_001
  value: 2.1
  quality_score: 1.0
  metadata: { "revision_of": "SER_20260801_001", "reason": "BEA preliminary revision" }

Second Revision:
  series_id: SER_20260901_001
  revision_id: REV_20260901_001
  value: 2.3
  quality_score: 1.0
  metadata: { "revision_of": "SER_20260815_001", "reason": "BEA final estimate" }
```

---

### 2.2 Evidence Object Contract

**Version:** `ev/v1`
**Module:** `macro_intelligence.contracts.evidence`
**Status:** Frozen

#### 2.2.1 Purpose

Every macro observation becomes an auditable evidence object. Evidence objects are immutable records of what was observed, from where, and with what confidence. They form the foundation for all analysis and knowledge generation.

#### 2.2.2 Schema Definition

```
EvidenceObject (frozen)
├── evidence_id: string              # Unique evidence identifier
├── source: string                   # Original data source
├── source_quality_score: float      # Source reliability rating
├── series_reference: string         # Reference to NormalizedSeries
├── observation_time: datetime       # When the observation was made
├── release_time: datetime | null    # When data was officially released
├── available_time: datetime         # When evidence was created in MIL
├── value: float | null              # Observed value
├── forecast: float | null           # Consensus forecast (if available)
├── previous: float | null           # Previous observation value
├── revision: RevisionRef | null     # Revision chain reference
├── confidence: float                # 0.0–1.0 confidence in data quality
└── provenance: ProvenanceChain      # Full source trail
```

#### 2.2.3 Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `evidence_id` | `string` | UUID v7: `EV_{timestamp}_{hash}` | Globally unique evidence identifier |
| `source` | `string` | Non-empty, max 64 chars | Source system name |
| `source_quality_score` | `float` | Range [0.0, 1.0] | Intrinsic quality of the source |
| `series_reference` | `string` | Matches series_id pattern | Reference to NormalizedSeries |
| `observation_time` | `datetime` | ISO 8601, UTC | When the underlying observation occurred |
| `release_time` | `datetime \| null` | ISO 8601, UTC | Official release timestamp |
| `available_time` | `datetime` | ISO 8601, UTC | When evidence was ingested into MIL |
| `value` | `float \| null` | None or valid float | The observed value |
| `forecast` | `float \| null` | None or valid float | Consensus forecast (for surprise calculation) |
| `previous` | `float \| null` | None or valid float | Previous period value |
| `revision` | `RevisionRef \| null` | None or RevisionRef | Revision chain reference |
| `confidence` | `float` | Range [0.0, 1.0] | Composite confidence score |
| `provenance` | `ProvenanceChain` | Structured object | Full source trail |

#### 2.2.4 Revision Reference Schema

```
RevisionRef (frozen)
├── revision_id: string              # Revision identifier
├── original_evidence_id: string     # Reference to original evidence
├── revision_number: int             # Sequential revision number
├── revision_time: datetime          # When revision was issued
├── revision_reason: string          # Human-readable reason
└── superseded: bool                 # True if this revision was itself revised
```

#### 2.2.5 Provenance Chain Schema

```
ProvenanceChain (frozen)
├── original_source: string          # First source of record
├── ingestion_pipeline: list[string] # All systems that touched the data
├── transformation_log: list[Transformation] # Every transformation applied
└── verification_checks: list[CheckResult]   # Validation results
```

#### 2.2.6 Immutability Rules

1. **EvidenceObjects are permanently immutable once created**
2. **No field may be modified** after creation
3. **Revisions create new EvidenceObjects**, not modifications
4. **Original source data is preserved verbatim** in provenance
5. **Deleted evidence is never truly deleted** — soft-delete with audit trail

---

### 2.3 MacroEvent Contract

**Version:** `me/v1`
**Module:** `macro_intelligence.contracts.event`
**Status:** Frozen

#### 2.3.1 Purpose

Macro events are discrete occurrences that impact markets: FOMC decisions, Fed speeches, data releases, geopolitical events, sanctions, and major announcements. Events are the primary triggers for market reaction analysis.

#### 2.3.2 Schema Definition

```
MacroEvent (frozen)
├── event_id: string                 # Unique event identifier
├── event_type: EventTypeEnum        # Category of event
├── timestamp: datetime              # When the event occurred
├── source: string                   # Event source
├── description: string              # Human-readable description
├── classification: EventClassification # Detailed classification
├── importance: ImportanceLevel      # Market importance rating
├── related_series: list[string]     # Affected time series
└── market_relevance: MarketRelevance # Quantified relevance
```

#### 2.3.3 Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `event_id` | `string` | UUID v7: `EVNT_{timestamp}_{hash}` | Globally unique event identifier |
| `event_type` | `EventTypeEnum` | Enum value | Primary event category |
| `timestamp` | `datetime` | ISO 8601, UTC | Event occurrence timestamp |
| `source` | `string` | Non-empty, max 64 chars | Event source system |
| `description` | `string` | Non-empty, max 1024 chars | Human-readable event description |
| `classification` | `EventClassification` | Structured enum | Detailed classification |
| `importance` | `ImportanceLevel` | Enum value | Market importance rating |
| `related_series` | `list[string]` | Valid series_ids | Affected time series |
| `market_relevance` | `MarketRelevance` | Structured object | Quantified relevance metrics |

#### 2.3.4 Event Type Enum

```
EventTypeEnum = {
    "FOMC_MEETING",           # FOMC policy meeting
    "FOMC_STATEMENT",         # FOMC statement release
    "FOMC_SUMMARY",           # Summary of Economic Projections (SEP)
    "FED_SPEECH",             # Federal Reserve speech
    "FED_HEARING",            # Congressional hearing
    "DATA_RELEASE",           # Economic data release
    "GEOPOLITICAL",           # Geopolitical event
    "SANCTION",               # Sanctions announcement
    "CENTRAL_BANK",           # Other central bank action
    "MARKET_EVENT",           # Market-moving event (flash crash, etc.)
    "REGULATORY",             # Regulatory announcement
}
```

#### 2.3.5 Event Classification Enum

```
EventClassification = {
    # FOMC-related
    "FOMC_RATE_DECISION",           # Interest rate change
    "FOMC_DOT_PLOT",                # Dot plot release
    "FOMC_QUANTITATIVE_EASING",     # QE announcement
    "FOMC_QUANTITATIVE_TIGHTENING", # QT announcement
    
    # Data releases
    "DATA_CPI",                       # CPI release
    "DATA_PPI",                       # PPI release
    "DATA_PCE",                       # PCE release
    "DATA_NFP",                       # Non-Farm Payrolls
    "DATA_GDP",                       # GDP release
    "DATA_RETAIL",                    # Retail sales
    "DATA PMI",                       # PMI releases
    "DATA_JOBLESS",                   # Jobless claims
    
    # Fed communications
    "SPEECH_HAWKSISH",                # Hawkish speech
    "SPEECH_DOVISH",                  # Dovish speech
    "SPEECH_NEUTRAL",                 # Neutral speech
    
    # Geopolitical
    "SANCTION Announcement",          # Sanctions announcement
    "TRADE TARIFF",                   # Trade tariff change
    "CONFLICT ESCALATION",            # Conflict escalation
    "POLITICAL EVENT",                # Major political event
}
```

#### 2.3.6 Importance Level Enum

```
ImportanceLevel = {
    "LOW",         # Minimal market impact expected
    "MEDIUM",      # Moderate market impact possible
    "HIGH",        # Significant market impact likely
    "CRITICAL",    # Major market impact expected
}
```

#### 2.3.7 Market Relevance Schema

```
MarketRelevance (frozen)
├── volatility_impact: float           # Expected volatility change (bps)
├── liquidity_impact: float            # Expected liquidity change (index)
├── affected_instruments: list[string] # Instruments expected to move
├── correlation_score: float           # Correlation with historical events
└── historical_similarity: str         # Similar historical event reference
```

#### 2.3.8 Event Examples

```python
# Example: FOMC Rate Decision
MacroEvent(
    event_id="EVNT_20260917_001",
    event_type="FOMC_MEETING",
    timestamp=datetime(2026, 9, 17, 18, 0, tzinfo=UTC),
    source="Federal Reserve",
    description="FOMC announces 25bps rate hike",
    classification="FOMC_RATE_DECISION",
    importance="CRITICAL",
    related_series=["US2Y", "US5Y", "US10Y", "US30Y", "DXY", "VIX"],
    market_relevance=MarketRelevance(
        volatility_impact=15.0,
        liquidity_impact=-5.0,
        affected_instruments=["TLT", "IEF", "SHY", "UUP", "VIX"],
        correlation_score=0.85,
        historical_similarity="20220316_001"
    )
)

# Example: CPI Data Release
MacroEvent(
    event_id="EVNT_20260812_001",
    event_type="DATA_RELEASE",
    timestamp=datetime(2026, 8, 12, 8:30, tzinfo=UTC),
    source="BLS",
    description="CPI comes in hotter than expected at 3.2% YoY",
    classification="DATA_CPI",
    importance="HIGH",
    related_series=["CPI_YOY", "CPI_CORE_YOY", "US10Y", "REAL_10Y", "DXY"],
    market_relevance=MarketRelevance(
        volatility_impact=8.0,
        liquidity_impact=-2.0,
        affected_instruments=["TLT", "SPY", "GLD", "UUP"],
        correlation_score=0.72,
        historical_similarity="20220310_001"
    )
)

# Example: Geopolitical Event
MacroEvent(
    event_id="EVNT_20260715_001",
    event_type="GEOPOLITICAL",
    timestamp=datetime(2026, 7, 15, 14, 0, tzinfo=UTC),
    source="Reuters",
    description="Major trade制裁 announced affecting tech sector",
    classification="SANCTION Announcement",
    importance="CRITICAL",
    related_series=["VIX", "MOVE", "DXY", "GLD_FLOWS"],
    market_relevance=MarketRelevance(
        volatility_impact=25.0,
        liquidity_impact=-15.0,
        affected_instruments=["VIX", "GLD", "UUP", "FXI"],
        correlation_score=0.65,
        historical_similarity="20180403_001"
    )
)
```

---

### 2.4 MarketReaction Contract

**Version:** `mr/v1`
**Module:** `macro_intelligence.contracts.reaction`
**Status:** Frozen

#### 2.4.1 Purpose

MarketReaction captures the quantified impact of macro events on financial instruments. It provides structured analysis of price, volatility, and liquidity changes around events.

#### 2.4.2 Schema Definition

```
MarketReaction (frozen)
├── event_id: string                 # Reference to triggering MacroEvent
├── instrument: string               # Instrument affected
├── window_before: WindowSpec        # Pre-event window specification
├── window_after: WindowSpec         # Post-event window specification
├── reaction_metrics: ReactionMetrics # Quantified reaction data
└── calculation_version: str         # Version of calculation methodology
```

#### 2.4.3 Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `event_id` | `string` | Matches event_id pattern | Reference to triggering MacroEvent |
| `instrument` | `string` | Non-empty | Instrument symbol or series_id |
| `window_before` | `WindowSpec` | Structured | Pre-event analysis window |
| `window_after` | `WindowSpec` | Structured | Post-event analysis window |
| `reaction_metrics` | `ReactionMetrics` | Structured | Quantified reaction data |
| `calculation_version` | `string` | Semantic version | Version of calculation methodology |

#### 2.4.4 Window Specification Schema

```
WindowSpec (frozen)
├── start_offset: timedelta          # Start of window relative to event
├── end_offset: timedelta            # End of window relative to event
├── start_price: float | null        # Price at window start
├── end_price: float | null          # Price at window end
├── start_volatility: float | null   # Volatility at window start
├── end_volatility: float | null     # Volatility at window end
└── start_liquidity: float | null    # Liquidity metric at window start
```

#### 2.4.5 Reaction Metrics Schema

```
ReactionMetrics (frozen)
├── return_bps: float                # Return in basis points
├── volatility_change_bps: float     # Volatility change in basis points
├── volume_change_pct: float         # Volume change percentage
├── bid_ask_widen_bps: float         # Bid-ask spread change
├── max_drawdown_bps: float          # Maximum drawdown during window
├── max_spike_bps: float             # Maximum price spike
└── reaction_significance: float     # Statistical significance (p-value)
```

#### 2.4.6 Calculation Versioning

```
calculation_version = "mr/v1.2.0"

# Version format: {contract}/v{major}.{minor}.{patch}
# major: Breaking changes to calculation methodology
# minor: New metrics added
# patch: Bug fixes
```

#### 2.4.7 Example MarketReaction

```python
MarketReaction(
    event_id="EVNT_20260917_001",
    instrument="US10Y",
    window_before=WindowSpec(
        start_offset=timedelta(hours=-24),
        end_offset=timedelta(hours=0),
        start_price=4.25,
        end_price=4.27,
        start_volatility=0.85,
        end_volatility=0.92,
        start_liquidity=1.0
    ),
    window_after=WindowSpec(
        start_offset=timedelta(hours=0),
        end_offset=timedelta(hours=+24),
        start_price=4.27,
        end_price=4.42,
        start_volatility=0.92,
        end_volatility=1.15,
        start_liquidity=1.0
    ),
    reaction_metrics=ReactionMetrics(
        return_bps=150.0,
        volatility_change_bps=230.0,
        volume_change_pct=45.0,
        bid_ask_widen_bps=1.5,
        max_drawdown_bps=85.0,
        max_spike_bps=120.0,
        reaction_significance=0.001
    ),
    calculation_version="mr/v1.2.0"
)
```

---

### 2.5 Knowledge Object Contract

**Version:** `ko/v1`
**Module:** `macro_intelligence.contracts.knowledge`
**Status:** Frozen

#### 2.5.1 Purpose

KnowledgeObjects represent derived insights from accumulated evidence. They are NOT raw LLM output — they are structured, evidence-backed conclusions with statistical support. Knowledge Objects are generated through a pipeline: Evidence → Statistics → Pattern Detection → Knowledge Object.

#### 2.5.2 Schema Definition

```
KnowledgeObject (frozen)
├── knowledge_id: string             # Unique knowledge identifier
├── evidence_refs: list[string]      # References to supporting evidence
├── pattern_type: PatternTypeEnum    # Type of pattern detected
├── confidence: float                # 0.0–1.0 confidence in knowledge
├── statistical_support: StatisticalSupport # Statistical backing
├── created_version: str             # Version of knowledge generation
└── explanation: str                 # Human-readable explanation
```

#### 2.5.3 Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `knowledge_id` | `string` | UUID v7: `KN_{timestamp}_{hash}` | Globally unique knowledge identifier |
| `evidence_refs` | `list[string]` | Valid evidence_ids | References to supporting EvidenceObjects |
| `pattern_type` | `PatternTypeEnum` | Enum value | Type of pattern detected |
| `confidence` | `float` | Range [0.0, 1.0] | Confidence in the knowledge claim |
| `statistical_support` | `StatisticalSupport` | Structured | Statistical backing for the claim |
| `created_version` | `string` | Semantic version | Version of knowledge generation pipeline |
| `explanation` | `string` | Non-empty, max 4096 chars | Human-readable explanation |

#### 2.5.4 Pattern Type Enum

```
PatternTypeEnum = {
    # Market behavior patterns
    "REGIME_SHIFT",               # Shift in market regime
    "CORRELATION_BREAK",          # Break in historical correlation
    "VOLATILITY_CLUSTER",         # Volatility clustering detected
    "LIQUIDITY_DRY_UP",           # Liquidity contraction
    "TREND_ACCELERATION",         # Trend acceleration
    "TREND_REVERSAL",             # Trend reversal
    
    # Macro patterns
    "INFLATION_PERSISTENCE",      # Inflation proving sticky
    "RATE_PATH_SHIFT",            # Expected rate path change
    "YIELD_CURVE_INVERSION",      # Yield curve inversion
    "YIELD_CURVE_STEEPENING",     # Yield curve steepening
    
    # Event patterns
    "EVENT_SURPRISE_PATTERN",     # Recurring surprise pattern
    "MARKET_OVERREACTION",        # Market overreacting to events
    "MARKET_UNDERREACTION",       # Market underreacting to events
}
```

#### 2.5.5 Statistical Support Schema

```
StatisticalSupport (frozen)
├── sample_size: int                 # Number of observations
├── p_value: float                   # Statistical significance
├── confidence_interval: tuple[float, float] # 95% CI
├── effect_size: float               # Magnitude of effect
├── test_method: str                 # Statistical test used
├── assumptions_valid: bool          # Whether assumptions hold
└── limitations: list[string]        # Known limitations
```

#### 2.5.6 Knowledge Generation Pipeline

```
Evidence Objects
    │
    ▼
Statistical Analysis (mean, std, correlation, regression)
    │
    ▼
Pattern Detection (rule-based + ML)
    │
    ▼
Knowledge Object (structured output with evidence refs)
    │
    ▼
Human Review (optional)
    │
    ▼
Published Knowledge
```

#### 2.5.7 Example KnowledgeObject

```python
KnowledgeObject(
    knowledge_id="KN_20260815_001",
    evidence_refs=[
        "EV_20260801_001", "EV_20260802_001", "EV_20260803_001",
        "EV_20260804_001", "EV_20260805_001"
    ],
    pattern_type="INFLATION_PERSISTENCE",
    confidence=0.82,
    statistical_support=StatisticalSupport(
        sample_size=12,
        p_value=0.003,
        confidence_interval=(0.02, 0.05),
        effect_size=0.35,
        test_method="linear_regression",
        assumptions_valid=True,
        limitations=["Small sample size", "Recent data subject to revision"]
    ),
    created_version="ko/v1.0.0",
    explanation="Core inflation has shown persistent upward pressure over the past 12 months, with a statistically significant trend (p=0.003). The effect size of 0.35 indicates a moderate but consistent deviation from expected decline. This pattern suggests the Federal Reserve may need to maintain restrictive policy longer than market expects."
)
```

---

## 3. Interface Definitions

### 3.1 Macro Query Interface

**Version:** `mqi/v1`
**Module:** `macro_intelligence.interfaces.query`
**Status:** Frozen

#### 3.1.1 Purpose

The Macro Query Interface provides ResearchOS V1 Core with read-only access to MIL data. All queries are versioned and backward-compatible.

#### 3.1.2 Interface Definition

```python
class MacroQueryInterface(ABC):
    """
    Read-only interface for V1 Core to query Macro Intelligence Layer.
    All methods are synchronous for simplicity; async variants may be added.
    """
    
    # Series Queries
    @abstractmethod
    def get_series(
        self,
        series_id: str,
        start: date,
        end: date,
        include_revisions: bool = False,
    ) -> list[NormalizedSeries]:
        """
        Retrieve a time series within a date range.
        
        Args:
            series_id: Series identifier (e.g., "US10Y", "CPI_YOY")
            start: Start date (inclusive)
            end: End date (inclusive)
            include_revisions: If True, include all revisions
        
        Returns:
            List of NormalizedSeries ordered by observation_period ascending
        """
        ...
    
    @abstractmethod
    def get_latest(
        self,
        series_id: str,
    ) -> NormalizedSeries | None:
        """
        Retrieve the latest observation for a series.
        
        Returns:
            Latest NormalizedSeries or None if not found
        """
        ...
    
    @abstractmethod
    def get_surprise(
        self,
        series_id: str,
        date: date,
    ) -> float | None:
        """
        Get the consensus surprise for a data release.
        
        Returns:
            surprise = actual - forecast (null if no forecast available)
        """
        ...
    
    @abstractmethod
    def get_yield_curve(
        self,
        date: date,
    ) -> dict[str, float]:
        """
        Get the full Treasury yield curve for a date.
        
        Returns:
            {tenor: yield_in_percent} for 2Y, 5Y, 10Y, 30Y
        """
        ...
    
    @abstractmethod
    def get_spread(
        self,
        tenor_a: str,
        tenor_b: str,
        date: date,
    ) -> float:
        """
        Get the spread between two tenors in basis points.
        
        Returns:
            Spread in basis points (tenor_a - tenor_b)
        """
        ...
    
    @abstractmethod
    def get_market_context(
        self,
        series_id: str,
        date: date,
        lookback_days: int = 30,
    ) -> MarketContext:
        """
        Get market context for a series around a date.
        
        Returns:
            MarketContext with statistics and nearby events
        """
        ...
    
    # Event Queries
    @abstractmethod
    def get_event(
        self,
        event_id: str,
    ) -> MacroEvent | None:
        """
        Retrieve an event by ID.
        
        Returns:
            MacroEvent or None if not found
        """
        ...
    
    @abstractmethod
    def search_events(
        self,
        event_type: EventTypeEnum | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        related_series: list[str] | None = None,
        importance: ImportanceLevel | None = None,
        limit: int = 50,
    ) -> list[MacroEvent]:
        """
        Search events with filters.
        
        Returns:
            List of MacroEvents matching criteria
        """
        ...
    
    # Evidence Queries
    @abstractmethod
    def get_evidence(
        self,
        evidence_id: str,
    ) -> EvidenceObject | None:
        """
        Retrieve evidence by ID.
        
        Returns:
            EvidenceObject or None if not found
        """
        ...
    
    @abstractmethod
    def get_evidence_for_series(
        self,
        series_id: str,
        date: date,
    ) -> list[EvidenceObject]:
        """
        Get all evidence for a series on a date.
        
        Returns:
            List of EvidenceObjects (may include revisions)
        """
        ...
    
    # Reaction Queries
    @abstractmethod
    def get_reaction(
        self,
        event_id: str,
        instrument: str,
    ) -> MarketReaction | None:
        """
        Get market reaction for an event and instrument.
        
        Returns:
            MarketReaction or None if not found
        """
        ...
    
    @abstractmethod
    def get_reactions_for_event(
        self,
        event_id: str,
    ) -> list[MarketReaction]:
        """
        Get all market reactions for an event.
        
        Returns:
            List of MarketReaction objects
        """
        ...
    
    # Health & Status
    @abstractmethod
    def get_health(self) -> dict:
        """
        Get MIL health status.
        
        Returns:
            Dict with ingestion status, last update times, etc.
        """
        ...
    
    @abstractmethod
    def get_series_metadata(
        self,
        series_id: str,
    ) -> SeriesMetadata | None:
        """
        Get metadata for a series.
        
        Returns:
            SeriesMetadata or None if not found
        """
        ...
```

#### 3.1.3 Return Type Schemas

```python
@dataclass(frozen=True)
class MarketContext:
    series_id: str
    date: date
    value: float | None
    prior_value: float | None
    change_pct: float | None
    volatility_30d: float
    volatility_90d: float
    nearby_events: list[MacroEvent]
    recent_reactions: list[MarketReaction]

@dataclass(frozen=True)
class SeriesMetadata:
    series_id: str
    name: str
    unit: str
    frequency: FrequencyEnum
    source: str
    start_date: date
    end_date: date
    total_observations: int
    missing_observations: int
    quality_score: float
```

---

### 3.2 V1 Bridge Interface

**Version:** `v1b/v1`
**Module:** `macro_intelligence.interfaces.v1_bridge`
**Status:** Frozen

#### 3.2.1 Purpose

The V1 Bridge provides a read-only, versioned interface between ResearchOS V1 Core and MIL. V1 Core can only READ from MIL through this bridge. MIL cannot write to V1 Core.

#### 3.2.2 Interface Definition

```python
class V1BridgeInterface(ABC):
    """
    Read-only bridge from V1 Core to Macro Intelligence Layer.
    
    Rules:
    - V1 Core can ONLY READ through this interface
    - MIL cannot write to V1 Core
    - All changes are additive (new methods, not breaking changes)
    - Version is strictly enforced
    """
    
    BRIDGE_VERSION = "v1"
    
    @abstractmethod
    def query(
        self,
        query_type: str,
        params: dict,
    ) -> Any:
        """
        Generic query endpoint for V1 Core.
        
        Args:
            query_type: Type of query (e.g., "series", "event", "reaction")
            params: Query parameters
        
        Returns:
            Query result (type varies by query_type)
        """
        ...
    
    @abstractmethod
    def validate_contract(self) -> ContractValidationResult:
        """
        Validate that the current implementation matches the contract.
        
        Returns:
            ContractValidationResult with pass/fail status
        """
        ...
    
    @abstractmethod
    def get_contract_version(self) -> str:
        """
        Get the current contract version.
        
        Returns:
            Version string (e.g., "v1.0.0")
        """
        ...
```

#### 3.2.3 Contract Validation Result

```python
@dataclass(frozen=True)
class ContractValidationResult:
    is_valid: bool
    version: str
    checks_performed: list[str]
    checks_passed: list[str]
    checks_failed: list[str]
    timestamp: datetime
```

---

### 3.3 Event Subscription Interface

**Version:** `esi/v1`
**Module:** `macro_intelligence.interfaces.events`
**Status:** Frozen

#### 3.3.1 Purpose

The Event Subscription Interface provides an in-process event bus for publishing and subscribing to macro events. V1 Core components can subscribe to events without tight coupling.

#### 3.3.2 Interface Definition

```python
class MacroEventBus(ABC):
    """
    In-process event bus for macro events.
    
    Usage:
        bus = MacroEventBusImpl()
        bus.subscribe("FOMC_MEETING", handler_function)
        bus.publish(event)
    """
    
    @abstractmethod
    def subscribe(
        self,
        event_type: EventTypeEnum,
        handler: callable,
    ) -> str:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to invoke
        
        Returns:
            Subscription ID for later unsubscription
        """
        ...
    
    @abstractmethod
    def unsubscribe(
        self,
        subscription_id: str,
    ) -> bool:
        """
        Unsubscribe from events.
        
        Returns:
            True if subscription was found and removed
        """
        ...
    
    @abstractmethod
    def publish(
        self,
        event: MacroEvent,
    ) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The MacroEvent to publish
        """
        ...
    
    @abstractmethod
    def publish_batch(
        self,
        events: list[MacroEvent],
    ) -> None:
        """
        Publish multiple events atomically.
        
        Args:
            events: List of MacroEvents to publish
        """
        ...
    
    @abstractmethod
    def get_subscribers(
        self,
        event_type: EventTypeEnum,
    ) -> list[str]:
        """
        Get all subscription IDs for an event type.
        
        Returns:
            List of subscription IDs
        """
        ...
```

---

## 4. Revision Model

### 4.1 Purpose

Macroeconomic data is frequently revised. The revision model ensures that:
1. Original values are preserved
2. Revisions are tracked with full provenance
3. Historical analysis can use any version of the data
4. Auditors can reconstruct any historical state

### 4.2 Revision Chain Model

```
Revision Chain:
SER_20260801_001 (Initial: GDP = 2.4%)
    │
    ├──► REV_20260815_001 (First Revision: GDP = 2.1%)
    │       │
    │       └──► REV_20260901_001 (Second Revision: GDP = 2.3%)
    │               │
    │               └── [No further revisions]
    │
    └──► SER_20260801_001_Reconstructed (Historical snapshot)
```

### 4.3 Revision Metadata

```python
@dataclass(frozen=True)
class RevisionMetadata:
    revision_id: string
    original_evidence_id: string
    revision_number: int
    revision_time: datetime
    revision_reason: string
    superseded_by: string | None
    quality_score: float
    metadata: dict
```

### 4.4 Revision Rules

| Rule | Description |
|------|-------------|
| **Never overwrite** | Original evidence is never modified |
| **Create new records** | Revisions create new NormalizedSeries and EvidenceObjects |
| **Link revisions** | Each revision references its predecessor via `revision_id` |
| **Preserve provenance** | Original source information is preserved in metadata |
| **Quality tracking** | Each revision has its own quality_score |
| **Audit trail** | Full revision chain is queryable |

### 4.5 Revision Handling in Queries

```python
# Query with revisions
series = bridge.get_series("GDP_YOY", start=date(2026, 1, 1), end=date(2026, 12, 31), include_revisions=True)
# Returns: [SER_20260801_001, REV_20260815_001, REV_20260901_001]

# Query latest only
series = bridge.get_series("GDP_YOY", start=date(2026, 1, 1), end=date(2026, 12, 31), include_revisions=False)
# Returns: [REV_20260901_001] (latest revision only)

# Query by revision
series = bridge.get_series("GDP_YOY", start=date(2026, 1, 1), end=date(2026, 12, 31), revision_id="REV_20260815_001")
# Returns: [REV_20260815_001] (specific revision)
```

---

## 5. Dependency Rules

### 5.1 Allowed Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCHOS V1 CORE                       │
│  (quant_engine, experiments, dataset_contracts, frozen_core)│
└─────────────────────────────────────────────────────────────┘
                            │
                            │ READ-ONLY via V1 Bridge
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MACRO INTELLIGENCE LAYER                        │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Contracts  │  │  Interfaces │  │   Storage   │         │
│  │  (frozen)   │  │  (frozen)   │  │  (Parquet/  │         │
│  └─────────────┘  └─────────────┘  │   JSON)     │         │
│                                    └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Ingestion  │  │   Adapters  │  │Normalization│         │
│  │   (pipes)   │  │  (adapters) │  │  (normalizer)│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Validation  │  │   Evidence  │  │   Events    │         │
│  │  (validator)│  │  (objects)  │  │ (objects)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Reaction  │  │  Knowledge  │  │  External   │         │
│  │  (analyzer) │  │ (generator) │  │  (APIs)     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ READ-ONLY
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL DATA SOURCES                      │
│  FRED │ BLS │ CFTC │ Fed │ CBOE │ Treasury │ ISM │ WGC     │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Dependency Matrix

| MIL Module | Can Import From | Cannot Import From |
|------------|-----------------|-------------------|
| `contracts/` | Python stdlib, pydantic | V1 Core, other MIL modules (self-contained) |
| `interfaces/` | contracts/, Python stdlib | V1 Core implementation |
| `ingestion/` | contracts/, interfaces/ | V1 Core, experiments, quant_engine |
| `adapters/` | contracts/, ingestion/ | V1 Core |
| `normalization/` | contracts/, adapters/ | V1 Core |
| `validation/` | contracts/, normalization/ | V1 Core |
| `storage/` | contracts/ | V1 Core |
| `evidence/` | contracts/, storage/ | V1 Core |
| `event/` | contracts/, storage/ | V1 Core |
| `analysis/` | contracts/, evidence/, event/, storage/ | V1 Core |
| `knowledge/` | contracts/, evidence/, event/, analysis/ | V1 Core |

### 5.3 Forbidden Dependencies

```
MIL MUST NOT IMPORT:
├── quant_engine
├── experiments
├── execution
├── strategy
├── trader
├── portfolio
├── risk
└── any V1 Core internal modules

V1 Core MUST NOT IMPORT:
├── macro_intelligence (directly)
├── Any MIL internal modules
└── Only through V1 Bridge Interface
```

### 5.4 Circular Dependency Prevention

```
# MIL internal dependencies (DAG - no cycles)
contracts → interfaces → ingestion → adapters → normalization → validation → storage
                                                                              ↓
                                                                        evidence
                                                                        event
                                                                         ↓
                                                                      analysis
                                                                         ↓
                                                                     knowledge

# V1 Core → MIL (one-way only)
V1 Core ──READ──► V1 Bridge Interface ──► MIL
```

---

## 6. Versioning Strategy

### 6.1 Contract Versioning

| Component | Version Format | Change Policy |
|-----------|---------------|---------------|
| NormalizedSeries | `ms/v{major}.{minor}` | Major = breaking schema change; Minor = additive fields |
| EvidenceObject | `ev/v{major}.{minor}` | Major = breaking; Minor = additive |
| MacroEvent | `me/v{major}.{minor}` | Major = breaking; Minor = additive |
| MarketReaction | `mr/v{major}.{minor}` | Major = breaking; Minor = additive |
| KnowledgeObject | `ko/v{major}.{minor}` | Major = breaking; Minor = additive |
| MacroQueryInterface | `mqi/v{major}` | Major = breaking interface change |
| V1BridgeInterface | `v1b/v{major}` | Major = breaking bridge change |
| MacroEventBus | `esi/v{major}` | Major = breaking event bus change |

### 6.2 Current Version

```
ms/v1.0.0  — NormalizedSeries contract (frozen)
ev/v1.0.0  — EvidenceObject contract (frozen)
me/v1.0.0  — MacroEvent contract (frozen)
mr/v1.0.0  — MarketReaction contract (frozen)
ko/v1.0.0  — KnowledgeObject contract (frozen)
mqi/v1.0.0 — Macro Query Interface (frozen)
v1b/v1.0.0 — V1 Bridge Interface (frozen)
esi/v1.0.0 — Event Subscription Interface (frozen)
```

### 6.3 Version Compatibility Rules

1. **Backward Compatibility:** New minor versions must be readable by old minor versions (unknown fields ignored)
2. **Forward Compatibility:** Old clients must work with new minor versions (graceful degradation)
3. **Breaking Changes:** Require major version bump; old versions remain supported for migration period
4. **Deprecation:** Deprecated fields/versions must be supported for at least 2 major versions

### 6.4 Serialization Determinism

```python
# All contracts must serialize deterministically
# Same input → Same output bytes

# Use canonical JSON serialization:
# - Sorted keys
# - No whitespace compression variations
# - Consistent datetime formatting (ISO 8601, UTC)
# - Consistent float formatting (no trailing zeros)

def canonical_serialize(obj: FrozenDataclass) -> bytes:
    """Deterministic serialization for auditability."""
    # Implementation ensures byte-for-byte reproducibility
    ...
```

---

## 7. Extension Rules

### 7.1 Adding New Series

1. Add to `SUPPORTED_SERIES` registry in `contracts/series.py`
2. Add validation rules in `validation/ranges.py`
3. Add adapter in `adapters/` (if new source)
4. Add feeder in `ingestion/feeders/` (if new ingestion method)
5. No contract changes required (additive to registry only)

### 7.2 Adding New Event Types

1. Add to `EventTypeEnum` in `contracts/event.py`
2. Add to `EventClassification` in `contracts/event.py`
3. Add handling in `knowledge/generator.py`
4. Contract version stays same (additive to enum)

### 7.3 Adding New Analysis Types

1. Add new analyzer class in `analysis/`
2. Register in `analysis/__init__.py`
3. Add query methods to `MacroQueryInterface` (if needed by V1)
4. May require minor version bump to interface contract

### 7.4 Contract Extension Rules

| Change Type | Version Bump | Backward Compatible |
|-------------|--------------|---------------------|
| Add new field with default | Minor | Yes |
| Add new enum value | Minor | Yes |
| Add new method to interface | Minor | Yes |
| Change field type | Major | No |
| Remove field | Major (with deprecation) | No |
| Change serialization format | Major | No |

---

## 8. Module Ownership

### 8.1 Ownership Matrix

| Module | Owner | Review Required | Change Process |
|--------|-------|-----------------|----------------|
| `contracts/` | Platform Architecture | Full Review | RFC + Review |
| `interfaces/` | Platform Architecture | Full Review | RFC + Review |
| `ingestion/` | Data Engineering | Tech Lead | PR + Review |
| `adapters/` | Data Engineering | Tech Lead | PR + Review |
| `normalization/` | Data Engineering | Tech Lead | PR + Review |
| `validation/` | Data Engineering | Tech Lead | PR + Review |
| `storage/` | Platform Engineering | Tech Lead | PR + Review |
| `evidence/` | Platform Engineering | Tech Lead | PR + Review |
| `event/` | Platform Engineering | Tech Lead | PR + Review |
| `analysis/` | Quant Research | Head of Quant | PR + Review |
| `knowledge/` | Quant Research | Head of Quant | PR + Review |

### 8.2 Change Control

```
CONTRACT CHANGES:
1. Submit RFC to Platform Architecture
2. Review by Quant Research Lead
3. Review by Data Engineering Lead
4. Vote: 2/3 majority required
5. Document in CHANGELOG.md
6. Bump version as required
7. Announce to all consumers

MODULE CHANGES:
1. Submit PR
2. Tech Lead review
3. Automated tests pass
4. Merge to main
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

- [ ] Create `contracts/` module with all frozen dataclasses
- [ ] Implement serialization/deserialization with determinism
- [ ] Create `interfaces/` module with ABC definitions
- [ ] Set up test infrastructure with fixtures
- [ ] Document all contracts

### Phase 2: Core Pipeline (Weeks 3-4)

- [ ] Implement `storage/` with Parquet and JSON
- [ ] Implement `validation/` with schema, range, freshness checks
- [ ] Implement `normalization/` with frequency conversion
- [ ] Create initial adapters for FRED and BLS
- [ ] Set up ingestion scheduler

### Phase 3: Data Ingestion (Weeks 5-6)

- [ ] Implement all feeders (FRED, BLS, CFTC, Fed, CBOE, Treasury, ISM)
- [ ] Implement all adapters (18 total)
- [ ] Set up credential management
- [ ] Implement backoff and retry logic
- [ ] Create health monitoring

### Phase 4: Analysis Layer (Weeks 7-8)

- [ ] Implement `evidence/` registry
- [ ] Implement `event/` generation from data releases
- [ ] Implement `analysis/market_reaction.py`
- [ ] Implement `analysis/correlation.py`
- [ ] Create knowledge generation pipeline

### Phase 5: Integration (Weeks 9-10)

- [ ] Implement V1 Bridge with read-only access
- [ ] Implement Event Subscription Interface
- [ ] Connect to ResearchOS V1 Core
- [ ] End-to-end testing
- [ ] Performance benchmarking

### Phase 6: Hardening (Weeks 11-12)

- [ ] Add comprehensive error handling
- [ ] Implement audit logging
- [ ] Add data quality dashboards
- [ ] Security review
- [ ] Documentation completion
- [ ] Production deployment

---

## Final Declaration

---

**Macro Intelligence Layer Contracts are architecturally frozen and ready for implementation.**

All contracts in this document are versioned, immutable, and backward-compatible. No implementation code has been written. No external APIs have been connected. No V1 Core modifications have been made.

**Next Step:** Begin Phase 1 implementation — create the contracts module with all frozen dataclasses.

---

*Document Version: 1.0.0-frozen*
*Last Updated: 2026-08-03*
*Classification: Internal — Quantitative Platform Architecture*
