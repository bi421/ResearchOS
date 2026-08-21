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

## Article IX: Market Ontology

> **Version:** 1.0.0
> **Status:** Phase 0 — Constitutional Foundation
> **Last Updated:** 2026-07-29
> **Determinism Guarantee:** Every entity, relationship, and classification in this ontology is defined by a fixed, version-controlled schema. No entity is inferred through machine learning or subjective interpretation.
> **Explainability Guarantee:** Every market concept used in any research output can be traced to its definition in this ontology. Every relationship between concepts is explicitly documented with its analytical rationale.

---

### 9.1 Overview

The Market Ontology defines the structured vocabulary of market concepts that underpins all ResearchOS analysis. It provides the semantic foundation that connects raw data sources (Article VIII) to analytical dimensions (Article VII) through a hierarchy of market entities, relationships, states, and events.

The ontology is organized into six layers:

| Layer | Description |
|---|---|
| **Entity Types** | The fundamental categories of market objects (assets, instruments, markets, participants). |
| **Entity Classifications** | Hierarchical taxonomies that categorize entities (asset classes, sectors, geographies). |
| **Market States** | The conditions and regimes that markets can exist in (trending, volatile, stressed). |
| **Market Events** | Scheduled and unscheduled occurrences that affect markets (earnings, policy decisions). |
| **Market Relationships** | The structural, statistical, and causal connections between entities and states. |
| **Concept Mappings** | How ontology concepts map to data sources, analytical dimensions, and research artifacts. |

Every concept in this ontology is assigned a unique identifier in the format `ONTOLOGY:TYPE:NAME` (e.g., `ONTOLOGY:ENTITY:ASSET:EQUITY`, `ONTOLOGY:STATE:REGIME:TRENDING`).

---

### 9.2 Entity Types

Entity types are the fundamental categories of objects that exist in financial markets. Every data source in Article VIII maps to one or more entity types.

#### 9.2.1 Asset

An asset is any resource with economic value that is expected to provide future benefits.

| Subtype | Description | Examples |
|---|---|---|
| **Equity** | Ownership interest in a corporation | Stocks, shares, ADRs |
| **Fixed Income** | Debt obligations with fixed returns | Bonds, notes, bills, CDs |
| **Commodity** | Physical goods traded on exchanges | Gold, oil, agricultural products |
| **Currency** | Fiat money and digital currencies | USD, EUR, JPY, BTC |
| **Derivative** | Contracts whose value derives from underlying assets | Options, futures, swaps, forwards |
| **Real Estate** | Property and property-related instruments | REITs, real estate funds |
| **Alternative** | Non-traditional investments | Private equity, hedge fund indices, infrastructure |

**Ontology ID:** `ONTOLOGY:ENTITY:ASSET`

#### 9.2.2 Instrument

An instrument is a specific tradable contract or security within an asset class.

| Subtype | Description | Examples |
|---|---|---|
| **Spot** | Immediate delivery at current market price | Spot stocks, spot FX, spot commodities |
| **Forward** | Contract to buy/sell at a future date at a predetermined price | FX forwards, forward contracts |
| **Future** | Standardized forward contract traded on exchanges | Treasury futures, equity index futures, commodity futures |
| **Option** | Right to buy (call) or sell (put) at a predetermined price | Stock options, index options, currency options |
| **Swap** | Agreement to exchange cash flows | Interest rate swaps, currency swaps, credit default swaps |
| **ETF** | Exchange-traded fund tracking an index | SPY, QQQ, GLD, EEM |
| **Structured Product** | Custom-designed instruments | CDOs, CMOs, structured notes |

**Ontology ID:** `ONTOLOGY:ENTITY:INSTRUMENT`

#### 9.2.3 Market

A market is a venue or system where buyers and sellers interact to trade assets.

| Subtype | Description | Examples |
|---|---|---|
| **Exchange** | Regulated marketplace for trading | NYSE, NASDAQ, CME, LSE |
| **OTC** | Over-the-counter decentralized trading | FX spot market, CDS market |
| **Dark Pool** | Private exchange with limited transparency | Credit Suisse Cross, Goldman Sachs SIG |
| **ECN** | Electronic communication network | ARCA, BATS, EDGX |
| **Auction** | Periodic price discovery mechanism | Treasury auctions, IPO auctions |

**Ontology ID:** `ONTOLOGY:ENTITY:MARKET`

#### 9.2.4 Participant

A participant is any entity that trades, invests in, or facilitates trading in financial markets.

| Subtype | Description | Examples |
|---|---|---|
| **Central Bank** | Monetary authority | Federal Reserve, ECB, BoJ |
| **Commercial Bank** | Retail and commercial banking | JPMorgan Chase, Bank of America |
| **Asset Manager** | Professional investment management | BlackRock, Vanguard, Fidelity |
| **Hedge Fund** | Alternative investment vehicle | Bridgewater, Renaissance, Citadel |
| **Insurance Company** | Risk pooling and investment | Berkshire Hathaway, Prudential |
| **Pension Fund** | Retirement savings vehicle | CalPERS, CPP Investment Board |
| **Sovereign Wealth Fund** | Government-owned investment fund | GIC, Abu Dhabi Investment Authority |
| **Retail Investor** | Individual traders and investors | Individual account holders |
| **Proprietary Trader** | Firm trading its own capital | Jane Street, DRW, Optiver |

**Ontology ID:** `ONTOLOGY:ENTITY:PARTICIPANT`

#### 9.2.5 Data Provider

A data provider is any source that generates, collects, or distributes market data.

| Subtype | Description | Examples |
|---|---|---|
| **Exchange** | Direct market data from trading venues | NYSE OpenBook, CME DataMine |
| **Government** | Official statistical agencies | BLS, Census Bureau, Fed |
| **Vendor** | Commercial data aggregators | Bloomberg, Refinitiv, FactSet |
| **Association** | Industry organizations | CFTC, OCC, World Gold Council |
| **Analytics Firm** | Specialized data providers | Preqin, PitchBook, CoinMetrics |
| **Alternative** | Non-traditional data sources | Satellogic, Plaid, Yelp |

**Ontology ID:** `ONTOLOGY:ENTITY:DATA_PROVIDER`

---

### 9.3 Entity Classifications

Entity classifications are hierarchical taxonomies that categorize entities into meaningful groups. These taxonomies are used throughout ResearchOS to organize data, filter analysis, and generate reports.

#### 9.3.1 Asset Class Classification

```
ASSET_CLASS
├── REAL_ASSETS
│   ├── Commodities
│   │   ├── Precious Metals (Gold, Silver, Platinum)
│   │   ├── Energy (Crude Oil, Natural Gas, Gasoline)
│   │   ├── Agricultural (Wheat, Corn, Soybeans, Coffee)
│   │   └── Livestock (Cattle, Hogs)
│   └── Real Estate
│       ├── REITs
│       ├── Direct Property
│       └── Real Estate Debt
├── FINANCIAL_ASSETS
│   ├── Equities
│   │   ├── Developed Markets
│   │   ├── Emerging Markets
│   │   ├── Small Cap
│   │   ├── Mid Cap
│   │   └── Large Cap
│   ├── Fixed Income
│   │   ├── Government (Treasury, Agency)
│   │   ├── Corporate (Investment Grade, High Yield)
│   │   ├── Municipal
│   │   └── Supranational
│   └── Currencies
│       ├── Developed Market (G10)
│       ├── Emerging Market
│       └── Digital Assets
└── ALTERNATIVE_INVESTMENTS
    ├── Private Equity
    ├── Hedge Funds
    ├── Infrastructure
    └── Derivatives
```

**Ontology ID:** `ONTOLOGY:CLASSIFICATION:ASSET_CLASS`

#### 9.3.2 Geographic Classification

```
GEOGRAPHY
├── NORTH_AMERICA
│   ├── United States
│   ├── Canada
│   └── Mexico
├── EUROPE
│   ├── Eurozone
│   ├── United Kingdom
│   ├── Nordics
│   └── Eastern Europe
├── ASIA_PACIFIC
│   ├── Japan
│   ├── China
│   ├── India
│   ├── Australia
│   └── Emerging Asia
├── LATIN_AMERICA
│   ├── Brazil
│   ├── Argentina
│   └── Regional
└── MIDDLE_EAST_AFRICA
    ├── Gulf States
    ├── South Africa
    └── Regional
```

**Ontology ID:** `ONTOLOGY:CLASSIFICATION:GEOGRAPHY`

#### 9.3.3 Sector Classification

Using the Global Industry Classification Standard (GICS):

```
SECTOR
├── Energy
├── Materials
├── Industrials
├── Utilities
├── Health Care
├── Financials
├── Information Technology
├── Communication Services
├── Consumer Discretionary
└── Consumer Staples
```

**Ontology ID:** `ONTOLOGY:CLASSIFICATION:SECTOR`

#### 9.3.4 Market Cap Classification

```
MARKET_CAP
├── Mega Cap (> $200B)
├── Large Cap ($10B - $200B)
├── Mid Cap ($2B - $10B)
├── Small Cap ($250M - $2B)
└── Micro Cap (< $250M)
```

**Ontology ID:** `ONTOLOGY:CLASSIFICATION:MARKET_CAP`

#### 9.3.5 Rating Classification

```
RATING
├── Investment Grade
│   ├── AAA
│   ├── AA
│   ├── A
│   └── BBB
└── High Yield
    ├── BB
    ├── B
    ├── CCC
    ├── CC
    ├── C
    └── D (Default)
```

**Ontology ID:** `ONTOLOGY:CLASSIFICATION:RATING`

---

### 9.4 Market States

Market states describe the conditions and regimes that markets can exist in. These are the fundamental categories used in regime identification (Section 7.6.2) and macro regime classification (Section 7.5.2).

#### 9.4.1 Trend States

| State | Description | Ontology ID |
|---|---|---|
| **Trending** | Price is moving consistently in one direction with momentum | `ONTOLOGY:STATE:TREND:TRENDING` |
| **Ranging** | Price is oscillating within a bounded range without clear direction | `ONTOLOGY:STATE:TREND:RANGING` |
| **Reversing** | Price is changing direction after a sustained move | `ONTOLOGY:STATE:TREND:REVERSING` |
| **Accelerating** | Price momentum is increasing in magnitude | `ONTOLOGY:STATE:TREND:ACCELERATING` |
| **Decelerating** | Price momentum is decreasing in magnitude | `ONTOLOGY:STATE:TREND:DECELERATING` |

#### 9.4.2 Volatility States

| State | Description | Ontology ID |
|---|---|---|
| **Low Volatility** | Realized volatility is below the 25th percentile of historical range | `ONTOLOGY:STATE:VOL:LOW` |
| **Normal Volatility** | Realized volatility is between the 25th and 75th percentile | `ONTOLOGY:STATE:VOL:NORMAL` |
| **High Volatility** | Realized volatility is above the 75th percentile | `ONTOLOGY:STATE:VOL:HIGH` |
| **Expanding Volatility** | Volatility is increasing over time | `ONTOLOGY:STATE:VOL:EXPANDING` |
| **Contracting Volatility** | Volatility is decreasing over time | `ONTOLOGY:STATE:VOL:CONTRACTING` |

#### 9.4.3 Liquidity States

| State | Description | Ontology ID |
|---|---|---|
| **Abundant Liquidity** | Market depth is high, bid-ask spreads are tight, price impact is low | `ONTOLOGY:STATE:LIQUIDITY:ABUNDANT` |
| **Normal Liquidity** | Market depth and spreads are within historical norms | `ONTOLOGY:STATE:LIQUIDITY:NORMAL` |
| **Stressed Liquidity** | Market depth is low, bid-ask spreads are wide, price impact is high | `ONTOLOGY:STATE:LIQUIDITY:STRESSED` |
| **Concentrated Liquidity** | Liquidity is concentrated at specific price levels | `ONTOLOGY:STATE:LIQUIDITY:CONCENTRATED` |
| **Fragmented Liquidity** | Liquidity is spread across many venues with no dominant center | `ONTOLOGY:STATE:LIQUIDITY:FRAGMENTED` |

#### 9.4.4 Sentiment States

| State | Description | Ontology ID |
|---|---|---|
| **Bullish** | Market participants are optimistic about future price direction | `ONTOLOGY:STATE:SENTIMENT:BULLISH` |
| **Bearish** | Market participants are pessimistic about future price direction | `ONTOLOGY:STATE:SENTIMENT:BEARISH` |
| **Neutral** | Market participants have balanced views with no strong directional bias | `ONTOLOGY:STATE:SENTIMENT:NEUTRAL` |
| **Overbought** | Prices have risen to levels where further upside is unlikely | `ONTOLOGY:STATE:SENTIMENT:OVERBOUGHT` |
| **Oversold** | Prices have fallen to levels where further downside is unlikely | `ONTOLOGY:STATE:SENTIMENT:OVERSOLD` |
| **Complacent** | Market participants are not adequately pricing in risk | `ONTOLOGY:STATE:SENTIMENT:COMPLACENT` |
| **Fearful** | Market participants are excessively worried about downside risk | `ONTOLOGY:STATE:SENTIMENT:FEARFUL` |

#### 9.4.5 Macro Regime States

| State | Inflation | Growth | Description | Ontology ID |
|---|---|---|---|---|
| **Stagflation** | High | Weak | Rising prices, slowing growth, central bank constrained | `ONTOLOGY:STATE:REGIME:STAGFLATION` |
| **Reflation** | Low→High | Strong→Weak | Recovery phase, inflation rising from lows | `ONTOLOGY:STATE:REGIME:REFLATION` |
| **Expansion** | Low | Strong | Healthy growth, stable prices, accommodative policy | `ONTOLOGY:STATE:REGIME:EXPANSION` |
| **Deflationary Slump** | Low | Weak | Falling prices, weak growth, deflationary spiral risk | `ONTOLOGY:STATE:REGIME:DEFLATIONARY_SLUMP` |

#### 9.4.6 Technical Regime States

| Volatility | Trend | State | Ontology ID |
|---|---|---|---|
| High | Trending | Volatile Trend | `ONTOLOGY:STATE:TECH:VOLATILE_TREND` |
| High | Ranging | High Volatility Range | `ONTOLOGY:STATE:TECH:HIGH_VOL_RANGE` |
| Normal | Trending | Normal Trend | `ONTOLOGY:STATE:TECH:NORMAL_TREND` |
| Normal | Ranging | Normal Range | `ONTOLOGY:STATE:TECH:NORMAL_RANGE` |
| Low | Trending | Low Volatility Trend | `ONTOLOGY:STATE:TECH:LOW_VOL_TREND` |
| Low | Ranging | Low Volatility Range | `ONTOLOGY:STATE:TECH:LOW_VOL_RANGE` |

---

### 9.5 Market Events

Market events are occurrences that affect market prices, sentiment, or structure. They are classified by type, frequency, and predictability.

#### 9.5.1 Scheduled Events

Scheduled events are known in advance and have predictable timing.

| Event Type | Description | Typical Impact | Ontology ID |
|---|---|---|---|
| **Central Bank Meeting** | Policy decision announcement | High | `ONTOLOGY:EVENT:CENTRAL_BANK_MEETING` |
| **Economic Release** | GDP, CPI, employment, PMI data | High | `ONTOLOGY:EVENT:ECONOMIC_RELEASE` |
| **Earnings Announcement** | Corporate quarterly results | Medium-High | `ONTOLOGY:EVENT:EARNINGS` |
| **Dividend Payment** | Distribution of corporate profits | Medium | `ONTOLOGY:EVENT:DIVIDEND` |
| **Bond Auction** | Government debt issuance | Medium | `ONTOLOGY:EVENT:BOND_AUCTION` |
| **IPO** | Initial public offering | Medium | `ONTOLOGY:EVENT:IPO` |
| **Fed Testimony** | Central bank official speaks to Congress | Medium | `ONTOLOGY:EVENT:FED_TESTIMONY` |
| **Fiscal Policy Announcement** | Budget, stimulus, tax changes | Medium-High | `ONTOLOGY:EVENT:FISCAL_POLICY` |

#### 9.5.2 Unscheduled Events

Unscheduled events are unpredictable and can cause significant market disruption.

| Event Type | Description | Typical Impact | Ontology ID |
|---|---|---|---|
| **Geopolitical Crisis** | War, conflict, political instability | Very High | `ONTOLOGY:EVENT:GEOPOLITICAL` |
| **Natural Disaster** | Earthquake, hurricane, pandemic | High | `ONTOLOGY:EVENT:NATURAL_DISASTER` |
| **Cyber Attack** | Security breach affecting markets or institutions | Medium-High | `ONTOLOGY:EVENT:CYBER_ATTACK` |
| **Corporate Scandal** | Fraud, misconduct, regulatory violation | High | `ONTOLOGY:EVENT:CORPORATE_SCANDAL` |
| **Systemic Crisis** | Financial system-wide disruption | Very High | `ONTOLOGY:EVENT:SYSTEMIC_CRISIS` |
| **Regulatory Intervention** | Unexpected policy change or enforcement action | Medium-High | `ONTOLOGY:EVENT:REGULATORY` |

#### 9.5.3 Event Impact Classification

| Impact Level | Description | Typical Price Move | Ontology ID |
|---|---|---|---|
| **Very High** | Market-wide disruption, regime shift potential | >5% | `ONTOLOGY:EVENT_IMPACT:VERY_HIGH` |
| **High** | Significant price movement, broad market effect | 2-5% | `ONTOLOGY:EVENT_IMPACT:HIGH` |
| **Medium** | Noticeable price movement, sector-specific effect | 1-2% | `ONTOLOGY:EVENT_IMPACT:MEDIUM` |
| **Low** | Minor price movement, limited market effect | 0.5-1% | `ONTOLOGY:EVENT_IMPACT:LOW` |
| **Minimal** | Negligible market impact | <0.5% | `ONTOLOGY:EVENT_IMPACT:MINIMAL` |

---

### 9.6 Market Relationships

Market relationships describe the structural, statistical, and causal connections between entities, states, and events. These relationships are the foundation of cross-market analysis (Section 7.5.1) and scenario generation (Section 7.9).

#### 9.6.1 Structural Relationships

Structural relationships are based on the fundamental architecture of financial markets.

| Relationship Type | Description | Examples | Ontology ID |
|---|---|---|---|
| **Causal** | One entity directly affects another through a mechanism | Fed rate hike → Bond yields rise | `ONTOLOGY:RELATIONSHIP:CAUSAL` |
| **Derives From** | One instrument's value is derived from another | Stock option derives from stock | `ONTOLOGY:RELATIONSHIP:DERIVES_FROM` |
| **Traded On** | An instrument is traded on a specific market | S&P 500 futures on CME | `ONTOLOGY:RELATIONSHIP:TRADED_ON` |
| **Issued By** | An instrument is issued by an entity | Treasury bonds by US Treasury | `ONTOLOGY:RELATIONSHIP:ISSUED_BY` |
| **Managed By** | An instrument is managed by a participant | Vanguard funds managed by Vanguard | `ONTOLOGY:RELATIONSHIP:MANAGED_BY` |
| **Competes With** | Two entities compete in the same market | Coca-Cola vs. Pepsi | `ONTOLOGY:RELATIONSHIP:COMPETES_WITH` |

#### 9.6.2 Statistical Relationships

Statistical relationships are based on observed co-movement patterns in market data.

| Relationship Type | Description | Examples | Ontology ID |
|---|---|---|---|
| **Correlated** | Two entities tend to move together | Gold and Swiss Franc | `ONTOLOGY:RELATIONSHIP:CORRELATED` |
| **Anti-Correlated** | Two entities tend to move in opposite directions | Stocks and bonds (sometimes) | `ONTOLOGY:RELATIONSHIP:ANTI_CORRELATED` |
| **Leads** | One entity's movement tends to precede another's | Yield curve inversion leads recession | `ONTOLOGY:RELATIONSHIP:LEADS` |
| **Lags** | One entity's movement tends to follow another's | Employment lags economic growth | `ONTOLOGY:RELATIONSHIP:LAGS` |
| **Granger-Causes** | Statistical causality based on time-series analysis | Oil prices Granger-cause inflation | `ONTOLOGY:RELATIONSHIP:GRANGER_CAUSES` |
| **Regime-Dependent** | Relationship changes based on market state | Stocks-bonds correlation varies by regime | `ONTOLOGY:RELATIONSHIP:REGIME_DEPENDENT` |

#### 9.6.3 Cross-Market Relationships

Cross-market relationships describe how different asset classes, geographies, and sectors interact.

| Relationship Type | Description | Examples | Ontology ID |
|---|---|---|---|
| **Intermarket** | Relationship between different asset classes | USD and commodities (inverse) | `ONTOLOGY:RELATIONSHIP:INTERMARKET` |
| **Interregional** | Relationship between different geographic markets | US and EM equities | `ONTOLOGY:RELATIONSHIP:INTERREGIONAL` |
| **Intersectoral** | Relationship between different industry sectors | Tech and energy | `ONTOLOGY:RELATIONSHIP:INTERSECTORAL` |
| **Cross-Currency** | Relationship between different currencies | EUR/USD and USD/JPY | `ONTOLOGY:RELATIONSHIP:CROSS_CURRENCY` |
| **Capital Flow** | Movement of funds between markets | US to EM capital flows | `ONTOLOGY:RELATIONSHIP:CAPITAL_FLOW` |
| **Contagion** | Crisis spreading from one market to another | LTCM crisis contagion | `ONTOLOGY:RELATIONSHIP:CONTAGION` |

#### 9.6.4 Sentiment Relationships

Sentiment relationships describe how market psychology affects price behavior.

| Relationship Type | Description | Examples | Ontology ID |
|---|---|---|---|
| **Amplifies** | Sentiment increases the magnitude of price moves | Fear amplifies sell-offs | `ONTOLOGY:RELATIONSHIP:AMPLIFIES` |
| **Dampens** | Sentiment reduces the magnitude of price moves | Complacency dampens volatility | `ONTOLOGY:RELATIONSHIP:DAMPENS` |
| **Reverses At** | Sentiment extremes tend to reverse | Overbought → Reversal | `ONTOLOGY:RELATIONSHIP:REVERSES_AT` |
| **Confirms** | Sentiment aligns with price direction | Bullish sentiment confirms uptrend | `ONTOLOGY:RELATIONSHIP:CONFIRMS` |
| **Contradicts** | Sentiment diverges from price direction | Bearish sentiment during rally | `ONTOLOGY:RELATIONSHIP:CONTRADICTS` |

---

### 9.7 Concept Mappings

Concept mappings define how ontology concepts connect to data sources, analytical dimensions, and research artifacts. These mappings ensure that every piece of data, every analysis, and every conclusion can be traced to its conceptual foundation.

#### 9.7.1 Data Source to Entity Type Mapping

| Data Source Category | Primary Entity Types | Ontology IDs |
|---|---|---|
| Macro | Asset, Participant, Event | `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:ENTITY:PARTICIPANT`, `ONTOLOGY:EVENT` |
| Central Banks | Participant, Event | `ONTOLOGY:ENTITY:PARTICIPANT`, `ONTOLOGY:EVENT` |
| Economic Calendar | Event | `ONTOLOGY:EVENT` |
| Bond Market | Asset, Instrument | `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:ENTITY:INSTRUMENT` |
| Yield Curve | Instrument, State | `ONTOLOGY:ENTITY:INSTRUMENT`, `ONTOLOGY:STATE` |
| Options | Instrument, State | `ONTOLOGY:ENTITY:INSTRUMENT`, `ONTOLOGY:STATE` |
| COT | Participant, Instrument | `ONTOLOGY:ENTITY:PARTICIPANT`, `ONTOLOGY:ENTITY:INSTRUMENT` |
| Forex | Asset, Instrument | `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:ENTITY:INSTRUMENT` |
| Gold | Asset, Instrument | `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:ENTITY:INSTRUMENT` |
| Indices | Asset, Instrument | `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:ENTITY:INSTRUMENT` |
| Crypto | Asset, Instrument | `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:ENTITY:INSTRUMENT` |
| Volatility | State | `ONTOLOGY:STATE` |
| Liquidity | State | `ONTOLOGY:STATE` |
| Sentiment | State, Participant | `ONTOLOGY:STATE`, `ONTOLOGY:ENTITY:PARTICIPANT` |
| Alternative Data | Asset, Event, Participant | `ONTOLOGY:ENTITY:ASSET`, `ONTOLOGY:EVENT`, `ONTOLOGY:ENTITY:PARTICIPANT` |

#### 9.7.2 Analytical Dimension to Ontology Mapping

| Analytical Dimension | Ontology Concepts Used | Article VII Section |
|---|---|---|
| **Macro Analysis** | Entity:Participant (Central Banks), Entity:Asset (Currencies), State:Regime, Event:Economic Release, Relationship:Causal | 7.5 |
| **Technical Analysis** | State:Trend, State:Volatility, State:Sentiment, Entity:Instrument, Relationship:Statistical | 7.6 |
| **Liquidity Analysis** | State:Liquidity, Entity:Participant (Market Makers), Relationship:Structural, Entity:Instrument | 7.7 |
| **Market Narrative** | Entity:Asset, State:Regime, Event:Scheduled/Unscheduled, Relationship:Causal | 7.8 |
| **Scenario Generation** | State:All States, Event:All Events, Relationship:All Relationships | 7.9 |
| **Confidence Estimation** | State:Volatility, Relationship:Regime-Dependent | 7.10 |
| **Contradiction Detection** | State:All States, Relationship:All Relationships, Entity:All Entities | 7.11 |

#### 9.7.3 Research Artifact to Ontology Mapping

| Research Artifact | Ontology Concepts Referenced | Article VII Section |
|---|---|---|
| **ResearchQuestion** | Entity:Asset, Entity:Instrument, Event | 7.2 |
| **HypothesisSet** | Entity:Asset, State:All States, Relationship:Causal | 7.2 |
| **EvidenceRegistry** | Entity:All, State:All, Event:All, Provider:All | 7.3 |
| **MacroAnalysis** | Entity:Participant, State:Regime, Event:Economic, Relationship:Causal | 7.5 |
| **TechnicalAnalysis** | State:Trend, State:Volatility, Entity:Instrument, Relationship:Statistical | 7.6 |
| **LiquidityAnalysis** | State:Liquidity, Entity:Participant, Relationship:Structural | 7.7 |
| **Narrative** | Entity:Asset, State:Regime, Event:All, Relationship:Causal | 7.8 |
| **ScenarioSet** | State:All States, Event:All Events, Relationship:All | 7.9 |
| **ConfidenceReport** | State:Volatility, Relationship:Regime-Dependent | 7.10 |
| **ContradictionReport** | State:All States, Relationship:All, Entity:All | 7.11 |
| **ResearchReport** | All ontology concepts | 7.12 |

---

### 9.8 Ontology Usage in Research

The market ontology is used throughout the research lifecycle to ensure consistency, traceability, and explainability.

#### 9.8.1 Evidence Tagging

Every evidence entry in the `EvidenceRegistry` (Section 7.3.2) is tagged with ontology concepts:

```
EvidenceEntry Tags:
  entity_type:     ONTOLOGY:ENTITY:ASSET:COMMODOITY
  entity_subtype:  ONTOLOGY:ENTITY:ASSET:COMMODITY:PRESCO_METALS:GOLD
  state:           ONTOLOGY:STATE:SENTIMENT:SAFE_HAVEN
  event:           ONTOLOGY:EVENT:CENTRAL_BANK_MEETING
  relationship:    ONTOLOGY:RELATIONSHIP:INTERMARKET
  geography:       ONTOLOGY:CLASSIFICATION:GEOGRAPHY:NORTH_AMERICA:UNITED_STATES
  sector:          ONTOLOGY:CLASSIFICATION:SECTOR:FINANCIALS
```

These tags enable:
- **Semantic search** — Find all evidence related to a specific entity or state
- **Cross-dimensional linking** — Connect evidence across analytical dimensions
- **Contradiction detection** — Identify when evidence tags conflict
- **Narrative construction** — Build narratives from tagged evidence

#### 9.8.2 Analysis Classification

Every analysis result is classified using ontology concepts:

```
AnalysisResult Classification:
  primary_entity:   ONTOLOGY:ENTITY:ASSET:EQUITY
  primary_state:    ONTOLOGY:STATE:TREND:TRENDING
  primary_relationship: ONTOLOGY:RELATIONSHIP:INTERMARKET
  supporting_entities: [ONTOLOGY:ENTITY:ASSET:COMMODITY, ONTOLOGY:ENTITY:ASSET:CURRENCY]
  supporting_states: [ONTOLOGY:STATE:VOL:HIGH, ONTOLOGY:STATE:SENTIMENT:BULLISH]
```

#### 9.8.3 Scenario Ontology

Every scenario is defined using ontology concepts:

```
Scenario Definition:
  base_entity:     ONTOLOGY:ENTITY:ASSET:EQUITY
  base_state:      ONTOLOGY:STATE:REGIME:EXPANSION
  trigger_events:  [ONTOLOGY:EVENT:ECONOMIC_RELEASE, ONTOLOGY:EVENT:CENTRAL_BANK_MEETING]
  outcome_state:   ONTOLOGY:STATE:TREND:TRENDING
  relationships:   [ONTOLOGY:RELATIONSHIP:CAUSAL, ONTOLOGY:RELATIONSHIP:LEADS]
```

#### 9.8.4 Contradiction Ontology

Every contradiction is classified using ontology concepts:

```
Contradiction Classification:
  type:            ONTOLOGY:RELATIONSHIP:CONTRADICTS
  entity_a:        ONTOLOGY:ENTITY:ASSET:EQUITY
  state_a:         ONTOLOGY:STATE:TREND:TRENDING
  entity_b:        ONTOLOGY:ENTITY:ASSET:COMMODITY
  state_b:         ONTOLOGY:STATE:TREND:RANGING
  relationship:    ONTOLOGY:RELATIONSHIP:REGIME_DEPENDENT
```

---

### 9.9 Ontology Evolution

The market ontology evolves over time as new concepts emerge and old ones become obsolete. All changes are version-controlled and tracked.

#### 9.9.1 Versioning

The ontology uses semantic versioning:
- **MAJOR** versions introduce breaking changes (concepts removed or redefined)
- **MINOR** versions add new concepts without breaking existing ones
- **PATCH** versions fix typos or clarify existing definitions

#### 9.9.2 Change Management

Changes to the ontology follow a deterministic process:

1. **Proposal** — A new concept or relationship is proposed with a use case.
2. **Review** — The proposal is reviewed against existing concepts for conflicts.
3. **Approval** — If no conflicts exist, the concept is approved and assigned an ID.
4. **Documentation** — The concept is documented with its definition, rationale, and mappings.
5. **Deployment** — The updated ontology is deployed to all ResearchOS components.
6. **Migration** — Existing data tagged with old concepts is migrated to new ones.

#### 9.9.3 Deprecation

Deprecated concepts are marked with a deprecation notice and a migration path. They remain in the ontology for at least two MAJOR versions before removal.

---

### 9.10 Ontology Summary

The market ontology provides the semantic foundation for all ResearchOS analysis. It ensures that:

1. **Consistency** — All market concepts are defined in a single, authoritative source.
2. **Traceability** — Every analysis can be traced to its conceptual foundation.
3. **Interoperability** — Different analytical dimensions share a common vocabulary.
4. **Explainability** — Every conclusion can be explained in terms of ontology concepts.
5. **Extensibility** — New concepts can be added without breaking existing analysis.

The ontology is organized into:
- **5 Entity Types** (Asset, Instrument, Market, Participant, Data Provider)
- **5 Entity Classifications** (Asset Class, Geography, Sector, Market Cap, Rating)
- **6 Market State Categories** (Trend, Volatility, Liquidity, Sentiment, Macro Regime, Technical Regime)
- **3 Market Event Categories** (Scheduled, Unscheduled, Impact Levels)
- **4 Market Relationship Categories** (Structural, Statistical, Cross-Market, Sentiment)
- **4 Concept Mapping Categories** (Data Source, Analytical Dimension, Research Artifact, Usage)

---

*This concludes Article IX: Market Ontology. The next article (Article X) will define the Research Validation methodology.*
