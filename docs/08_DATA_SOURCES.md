# ResearchOS — Constitution

## Article VIII: Data Sources

> **Version:** 1.0.0
> **Status:** Phase 0 — Constitutional Foundation
> **Last Updated:** 2026-07-29
> **Determinism Guarantee:** Every data source is identified by a fixed, version-controlled URI. Update frequencies, reliability scores, and inter-source relationships are defined as static tables, not computed dynamically.
> **Explainability Guarantee:** Every data source carries a unique identifier, a source reliability score (SR, per Section 7.4.2), and explicit links to the analytical dimensions it feeds. The provenance of every evidence entry can be traced to its originating source.

---

### 8.1 Overview

This article defines the complete catalog of data sources required by ResearchOS. Sources are organized into 14 categories that align with the analytical dimensions defined in Article VII (Sections 7.5–7.7).

Each data source entry specifies four attributes:

| Attribute | Description |
|---|---|
| **Why It Matters** | The analytical significance of the source — which hypotheses it supports, which analyses it feeds, and what market phenomena it illuminates. |
| **Update Frequency** | How often new data becomes available. Expressed as a fixed interval (e.g., "Daily at 14:30 UTC"). |
| **Trustworthiness** | The source reliability score (SR) from Section 7.4.2, with rationale for the assigned value. |
| **Source Interactions** | How the source relates to, confirms, or contradicts other sources in the catalog. |

The complete source catalog is maintained as a version-controlled `SourceCatalog` table. Each source is assigned a unique identifier in the format `CATEGORY:SUBTYPE:SOURCE` (e.g., `MACRO:CENTRAL_BANK:FED:FOMC_STATEMENT`).

---

### 8.2 Source Catalog Summary

| # | Category | Sources | Total |
|---|---|---|---|
| 1 | Macro | 12 | 12 |
| 2 | Central Banks | 9 | 9 |
| 3 | Economic Calendar | 8 | 8 |
| 4 | Bond Market | 10 | 10 |
| 5 | Yield Curve | 5 | 5 |
| 6 | Options | 8 | 8 |
| 7 | COT | 4 | 4 |
| 8 | Forex | 7 | 7 |
| 9 | Gold | 7 | 7 |
| 10 | Indices | 9 | 9 |
| 11 | Crypto | 7 | 7 |
| 12 | Volatility | 8 | 8 |
| 13 | Liquidity | 8 | 8 |
| 14 | Sentiment | 6 | 6 |
| 15 | Alternative Data | 8 | 8 |
| | **Total** | | **116** |

---

## 1. Macro

Macro sources provide the fundamental economic and policy context that drives long-term market behavior. They feed the Macro Analysis dimension (Section 7.5) and underpin the market narrative (Section 7.8).

### 1.1 Central Bank Policy Rates

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:POLICY_RATE` |
| **Why It Matters** | The single most important driver of asset prices. Policy rates directly influence discount rates, carry trades, and risk appetite. They anchor the entire macro regime classification (Section 7.5.2). Every monetary policy hypothesis depends on this data. |
| **Update Frequency** | Varies by central bank: Fed (8×/year at FOMC meetings), ECB (8×/year), BoJ (2–4×/year), others similarly. Ad-hoc changes possible. |
| **Trustworthiness** | **SR: 1.0** — Primary Official. Published directly by central banks with no intermediary. Zero revision history. |
| **Source Interactions** | Confirmed by: Forward Guidance Statements (1.2), Balance Sheets (1.3). Contradicted by: Market-implied rates (6.4, 8.4). Feeds into: Yield Curve (5.1), FX (8.1), Bond Market (4.1). |

### 1.2 Forward Guidance Statements

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:FORWARD_GUIDANCE` |
| **Why It Matters** | Forward guidance shapes market expectations about future policy paths, often more powerfully than current rate changes. Critical for scenario generation (Section 7.9) — bull/bear scenarios depend heavily on guidance interpretation. |
| **Update Frequency** | After every policy meeting (8×/year for major central banks). Unscheduled statements possible during crises. |
| **Trustworthiness** | **SR: 1.0** — Primary Official. Direct central bank communication. However, guidance can be walked back, so temporal integrity is critical. |
| **Source Interactions** | Confirmed by: Policy Rates (1.1). Contradicted by: Market pricing (6.4, 8.4) when guidance diverges from market expectations. Feeds into: Narrative (7.8), Scenarios (7.9). |

### 1.3 Central Bank Balance Sheets

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:BALANCE_SHEET` |
| **Why It Matters** | Balance sheet size and composition reveal the true stance of monetary policy — QE expands sheets, QT contracts them. More informative than headline rates alone, especially in a ZIRP/NIRP environment. Drives liquidity analysis (Section 7.7) and global liquidity conditions. |
| **Update Frequency** | Weekly for Fed (H.4.1 factors), ECB (weekly), BoJ (weekly). Other central banks: monthly or quarterly. |
| **Trustworthiness** | **SR: 1.0** — Primary Official. Published by central banks. Minor revisions possible in subsequent weeks. |
| **Source Interactions** | Confirmed by: Money Supply (13.1), Repo Market (13.7). Contradicted by: Market liquidity measures (13.5) when transmission is impaired. Feeds into: Liquidity Analysis (7.7), Global Liquidity (1.5). |

### 1.4 Fiscal Policy Data

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:FISCAL_POLICY` |
| **Why It Matters** | Government spending and taxation directly affect aggregate demand, sector allocation, and long-term growth prospects. Fiscal stimulus can offset monetary tightening; fiscal drag can amplify it. Essential for macro regime classification and scenario generation. |
| **Update Frequency** | Government budget announcements: annually (varies by country). Monthly spending/tax data: monthly. Real-time fiscal flow data: weekly. |
| **Trustworthiness** | **SR: 0.95** — Primary Official for government data; Secondary Verified (0.85) for third-party fiscal aggregators. Government data subject to revision. |
| **Source Interactions** | Confirmed by: GDP (1.6), Tax Revenue (1.7). Contradicted by: Bond Market spreads (4.3) when fiscal concerns emerge. Feeds into: Macro Analysis (7.5), Bond Market (4.1). |

### 1.5 GDP Reports

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:GDp` |
| **Why It Matters** | The broadest measure of economic health. Determines the Growth Regime in macro classification (Section 7.5.2). GDP revisions reveal the true state of the economy and can trigger regime transitions. |
| **Update Frequency** | Advance estimate: ~30 days after quarter-end. Second estimate: ~60 days. Final estimate: ~90 days. Revisions continue for years. |
| **Trustworthiness** | **SR: 0.95** — Primary Official. Government statistical agencies. Subject to significant revisions (preliminary estimates can be off by 1%+). |
| **Source Interactions** | Confirmed by: Industrial Production (1.9), Employment (1.10), Retail Sales (1.11). Contradicted by: High-frequency alternatives (15.3, 15.4) when they diverge. Feeds into: Growth Regime (7.5.2), Economic Activity (7.5.1). |

### 1.6 Inflation Reports (CPI, PPI, PCE)

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:INFLATION` |
| **Why It Matters** | Inflation is the primary driver of fixed income markets and central bank policy. The Inflation Regime (Section 7.5.2) is determined by these measures. Core vs. headline distinctions are critical for narrative construction. |
| **Update Frequency** | CPI: monthly (typically 2nd week). PPI: monthly (typically 1st week). PCE: monthly (typically 2nd month after reference). Core measures updated simultaneously. |
| **Trustworthiness** | **SR: 0.95** — Primary Official. Government statistical agencies. CPI and PCE subject to methodological revisions. PPI more volatile due to pipeline effects. |
| **Source Interactions** | Confirmed by: Inflation Expectations (1.8), TIPS breakevens (4.4). Contradicted by: Real-time alternatives (15.2) when they diverge. Feeds into: Inflation Regime (7.5.2), Bond Market (4.1), Yield Curve (5.1). |

### 1.7 Employment Data

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:EMPLOYMENT` |
| **Why It Matters** | Labor market conditions are the Federal Reserve's primary mandate. Employment data drives policy expectations, consumer spending forecasts, and wage inflation. The most market-moving macro release. |
| **Update Frequency** | Non-farm payrolls: monthly (first Friday). Unemployment rate: monthly. Jobless claims: weekly. ADP employment: monthly (private). |
| **Trustworthiness** | **SR: 0.95** — Primary Official (BLS). High market impact creates incentive for accuracy. Jobless claims are most reliable (administrative data). Payrolls subject to benchmark revisions. |
| **Source Interactions** | Confirmed by: Jobless Claims (1.7b), ADP (1.7c), Consumer Spending (1.12). Contradicted by: High-frequency alternatives (15.3) when they diverge. Feeds into: Growth Regime (7.5.2), Wage Inflation (1.13). |

### 1.8 Inflation Expectations

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:INFLATION_EXPECTATIONS` |
| **Why It Matters** | Expectations drive actual inflation through wage/price setting behavior. More forward-looking than current inflation data. Critical for scenario generation — anchored vs. unanchored expectations produce very different outcomes. |
| **Update Frequency** | University of Michigan 5-10 year: monthly. Cleveland Fed CPI expectations: monthly. ECB Survey of Professional Forecasters: quarterly. Breakeven inflation (derived): daily. |
| **Trustworthiness** | **SR: 0.75** — Secondary Consensus for survey data; 0.85 for derived breakevens. Survey data is inherently noisy. Breakevens are market-based but include risk premium. |
| **Source Interactions** | Confirmed by: TIPS breakevens (4.4), Survey data (1.8a/1.8b). Contradicted by: Current inflation (1.6) when expectations are unanchored. Feeds into: Inflation Regime (7.5.2), Bond Market (4.1). |

### 1.9 Industrial Production & PMI

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:INDUSTRIAL_PRODUCTION` |
| **Why It Matters** | Real-time indicators of economic activity. PMI above 50 = expansion, below 50 = contraction. More frequent than GDP, providing early warning of regime shifts. Essential for growth regime classification. |
| **Update Frequency** | Industrial Production: monthly (~2 weeks after month-end). PMI: monthly (first business day). ISM: monthly (first business day). Markit: weekly (flash estimates). |
| **Trustworthiness** | **SR: 0.95** — Primary Official (Federal Reserve, ISM). PMI is survey-based but highly reliable. Flash estimates subject to revision. |
| **Source Interactions** | Confirmed by: GDP (1.5), Employment (1.7). Contradicted by: High-frequency alternatives (15.3, 15.4) when they diverge. Feeds into: Growth Regime (7.5.2), Economic Activity (7.5.1). |

### 1.10 Retail Sales & Consumer Spending

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:RETAIL_SALES` |
| **Why It Matters** | Consumer spending is ~70% of US GDP. Retail sales data provides the most timely measure of consumer demand. Critical for growth regime classification and sector rotation analysis. |
| **Update Frequency** | Monthly (typically 2-3 weeks after month-end). Advance estimates subject to revision. |
| **Trustworthiness** | **SR: 0.95** — Primary Official (Census Bureau). Census data is highly reliable but subject to seasonal adjustment methodology changes. |
| **Source Interactions** | Confirmed by: GDP (1.5), Credit Card Data (15.2). Contradicted by: Employment (1.7) when income-consumption disconnect occurs. Feeds into: Growth Regime (7.5.2), Economic Activity (7.5.1). |

### 1.11 Trade Balances & Current Account

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:TRADE_BALANCE` |
| **Why It Matters** | Trade flows affect currency values, inflation (import prices), and external vulnerability. Current account deficits can signal unsustainable growth. Critical for FX analysis and global liquidity assessment. |
| **Update Frequency** | Monthly (typically 30-45 days after month-end). Subject to significant revisions. |
| **Trustworthiness** | **SR: 0.95** — Primary Official. Government statistical agencies. Trade data is administrative but subject to valuation and timing adjustments. |
| **Source Interactions** | Confirmed by: Currency flows (8.1), Capital flows (13.4). Contradicted by: Alternative trade proxies (15.5) when they diverge. Feeds into: Global Liquidity (1.5), FX (8.1). |

### 1.12 Global Liquidity Conditions

| Attribute | Detail |
|---|---|
| **Identifier** | `MACRO:GLOBAL_LIQUIDITY` |
| **Why It Matters** | Cross-border capital flows and global money supply determine the availability of funding across markets. Global liquidity drives risk appetite and asset price correlations. The most important cross-market relationship (Section 7.5.1). |
| **Update Frequency** | M2/GDP ratios: quarterly. Cross-border flows: monthly. Credit conditions: monthly. Banking system health: weekly. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified for aggregated measures; 0.95 for primary country-level data. Global aggregates are derived and subject to methodological differences. |
| **Source Interactions** | Confirmed by: Balance Sheets (1.3), Money Supply (13.1), Capital Flows (13.4). Contradicted by: Market liquidity (13.5) when transmission is impaired. Feeds into: Liquidity Analysis (7.7), Cross-Market Relationships (5.5). |

---

## 2. Central Banks

Central bank sources provide direct insight into monetary policy decisions, communication, and implementation. They are the highest-trust category in the ResearchOS catalog.

### 2.1 Federal Reserve (FOMC)

| Attribute | Detail |
|---|---|
| **Identifier** | `CB:FED:FOMC` |
| **Why It Matters** | The Fed is the world's most influential central bank. FOMC decisions affect global interest rates, dollar funding, and risk appetite. The Fed's balance sheet expansion (QE) and contraction (QT) drive global liquidity conditions. |
| **Update Frequency** | FOMC statements: 8×/year (scheduled). Minutes: 3 weeks after each meeting. Beige Book: 8×/year (day before each FOMC). H.4.1 factors: weekly. |
| **Trustworthiness** | **SR: 1.0** — Primary Official. Direct Fed publications. No intermediary. Zero tolerance for errors. |
| **Source Interactions** | Confirmed by: Fed Funds Futures (6.4), Balance Sheet (1.3). Contradicted by: Market pricing (6.4, 8.4) when Fed guidance diverges from market expectations. Feeds into: All yield curves (5.1), FX (8.1), Bond Market (4.1). |

### 2.2 European Central Bank (ECB)

| Attribute | Detail |
|---|---|
| **Identifier** | `CB:ECB:POLICY` |
| **Why It Matters** | The ECB sets policy for the eurozone — the world's second-largest economy. ECB decisions affect EUR exchange rates, European bond markets, and global risk sentiment. APP/PEPP purchases are a major source of global liquidity. |
| **Update Frequency** | Monetary policy meetings: 8×/year. Press conferences: 8×/year. Economic Bulletin: quarterly. Deposit facility rate: 8×/year. |
| **Trustworthiness** | **SR: 1.0** — Primary Official. Direct ECB publications. However, ECB communication is often deliberately ambiguous, requiring careful interpretation. |
| **Source Interactions** | Confirmed by: EUR forward curves (8.2), European bond yields (4.1). Contradicted by: Eonia/€STR futures (6.4) when guidance diverges. Feeds into: Yield Curve (5.1), FX (8.1), Bond Market (4.1). |

### 2.3 Bank of Japan (BoJ)

| Attribute | Detail |
|---|---|
| **Identifier** | `CB:BOJ:POLICY` |
| **Why It Matters** | The BoJ's yield curve control (YCC) and negative interest rate policy create unique market dynamics. BoJ interventions in the JGB market and FX market have global spillover effects. Critical for yen carry trades and global liquidity. |
| **Update Frequency** | Monetary policy meetings: 2–4×/year. Monthly monetary policy reports. JGB purchase operations: daily. |
| **Trustworthiness** | **SR: 1.0** — Primary Official. Direct BoJ publications. However, BoJ policy is often reactive and subject to change, making forward guidance less reliable. |
| **Source Interactions** | Confirmed by: JGB yields (4.1), JPY forward curves (8.2). Contradicted by: BOJ interventions (unscheduled) when they surprise markets. Feeds into: Yield Curve (5.1), FX (8.1), Bond Market (4.1). |

### 2.4 Bank of England (BoE)

| Attribute | Detail |
|---|---|
| **Identifier** | `CB:BOE:POLICY` |
| **Why It Matters** | The BoE sets policy for the UK — a major financial center and commodity currency. BoE decisions affect GBP exchange rates and UK gilt markets. The Bank Rate is closely watched by emerging markets with GBP exposure. |
| **Update Frequency** | MPC meetings: 9×/year. Inflation Report: quarterly. Bank Rate: 9×/year. |
| **Trustworthiness** | **SR: 1.0** — Primary Official. Direct BoE publications. BoE communication is generally clear and reliable. |
| **Source Interactions** | Confirmed by: GBP forward curves (8.2), UK gilt yields (4.1). Contradicted by: Short sterling futures (6.4) when guidance diverges. Feeds into: Yield Curve (5.1), FX (8.1), Bond Market (4.1). |

### 2.5 People's Bank of China (PBOC)

| Attribute | Detail |
|---|---|
| **Identifier** | `CB:PBOC:POLICY` |
| **Why It Matters** | The PBOC manages the world's largest forex reserves and the yuan's exchange rate regime. PBOC policy affects global commodity prices, emerging market capital flows, and China's economic trajectory. Critical for EM analysis. |
| **Update Frequency** | MLF operations: weekly. Reserve requirement ratio: 2–4×/year. LPR: 1×/month. Daily liquidity operations. |
| **Trustworthiness** | **SR: 0.95** — Primary Official for published rates; but PBOC communication is often indirect, and actual policy implementation may differ from stated intent. |
| **Source Interactions** | Confirmed by: CNY forward curves (8.2), China bond yields (4.1). Contradicted by: Offshore CNY (CNH) spreads when onshore-offshore divergence occurs. Feeds into: FX (8.1), Bond Market (4.1), Global Liquidity (1.12). |

### 2.6 Bank of Canada (BoC)

| Attribute | Detail |
|---|---|
| **Identifier** | `CB:BOC:POLICY` |
| **Why It Matters** | The BoC sets policy for Canada — a major commodity exporter. BoC decisions track Fed policy closely but diverge based on Canadian economic conditions. Critical for CAD exchange rates and Canadian bond markets. |
| **Update Frequency** | 8×/year (fixed schedule). Monetary Policy Report: 2×/year. |
| **Trustworthiness** | **SR: 1.0** — Primary Official. Direct BoC publications. Clear and reliable communication. |
| **Source Interactions** | Confirmed by: CAD forward curves (8.2), Canadian bond yields (4.1). Contradicted by: Corra futures (6.4) when guidance diverges. Feeds into: Yield Curve (5.1), FX (8.1), Bond Market (4.1). |

### 2.7 Swiss National Bank (SNB)

| Attribute | Detail |
|---|---|
| **Identifier** | `CB:SNB:POLICY` |
| **Why It Matters** | The SNB manages the Swiss franc — a global safe haven currency. SNB interventions in the FX market are frequent and impactful. SNB policy affects EUR/CHF and global risk sentiment. |
| **Update Frequency** | 3×/year (quarterly). Unscheduled interventions possible. |
| **Trustworthiness** | **SR: 0.95** — Primary Official. Direct SNB publications. However, SNB interventions are often unannounced, creating surprise risk. |
| **Source Interactions** | Confirmed by: CHF forward curves (8.2), Swiss bond yields (4.1). Contradicted by: Unannounced interventions when they surprise markets. Feeds into: FX (8.1), Bond Market (4.1). |

### 2.8 Reserve Bank of Australia (RBA)

| Attribute | Detail |
|---|---|
| **Identifier** | `CB:RBA:POLICY` |
| **Why It Matters** | The RBA sets policy for Australia — a major commodity exporter. RBA decisions affect AUD exchange rates and Australian bond markets. RBA is often a bellwether for commodity currencies and EM risk appetite. |
| **Update Frequency** | 11×/year (monthly except April/October). Statement on Monetary Policy: 4×/year. |
| **Trustworthiness** | **SR: 1.0** — Primary Official. Direct RBA publications. Clear and reliable communication. |
| **Source Interactions** | Confirmed by: AUD forward curves (8.2), Australian bond yields (4.1). Contradicted by: AUD interest rate futures (6.4) when guidance diverges. Feeds into: Yield Curve (5.1), FX (8.1), Bond Market (4.1). |

### 2.9 Bank of Japan (BOJ) — Monetary Base & JGB Operations

| Attribute | Detail |
|---|---|
| **Identifier** | `CB:BOJ:OPERATIONS` |
| **Why It Matters** | The BOJ's JGB purchase program is the largest single central bank asset purchase program in the world. BOJ operations directly affect the entire Japanese government bond market and have spillover effects on global fixed income. |
| **Update Frequency** | Daily for operations. Weekly for monetary base statistics. |
| **Trustworthiness** | **SR: 1.0** — Primary Official. Direct BOJ publications. However, the BOJ's YCC framework creates artificial market dynamics that may not reflect true supply-demand balance. |
| **Source Interactions** | Confirmed by: JGB yields (4.1), BOJ balance sheet (1.3). Contradicted by: Market-implied yields when YCC deviates from market pricing. Feeds into: Bond Market (4.1), Yield Curve (5.1). |

---

## 3. Economic Calendar

Economic calendar sources provide the schedule and actual values of macroeconomic releases. They are the primary trigger for market volatility and regime shifts.

### 3.1 GDP Release Calendar

| Attribute | Detail |
|---|---|
| **Identifier** | `CALENDAR:ECONOMIC:GDP` |
| **Why It Matters** | GDP releases are the most significant economic events, often triggering regime reclassification (Section 7.5.2). The advance estimate can cause significant market moves, and revisions reveal the true state of the economy. |
| **Update Frequency** | Advance: ~30 days after quarter-end. Second: ~60 days. Final: ~90 days. Revisions: annually. |
| **Trustworthiness** | **SR: 0.95** — Primary Official. Government statistical agencies. Subject to revision but high initial reliability. |
| **Source Interactions** | Confirmed by: Industrial Production (1.9), Employment (1.7). Contradicted by: High-frequency alternatives (15.3) when they diverge. Feeds into: Growth Regime (7.5.2), Scenarios (7.9). |

### 3.2 CPI/PPI Release Calendar

| Attribute | Detail |
|---|---|
| **Identifier** | `CALENDAR:ECONOMIC:INFLATION` |
| **Why It Matters** | Inflation releases are the primary driver of fixed income and currency markets. CPI surprises trigger immediate repricing of rate cut/raise expectations. Core vs. headline distinctions are critical for narrative construction. |
| **Update Frequency** | CPI: monthly (2nd week). PPI: monthly (1st week). PCE: monthly (2nd month after reference). |
| **Trustworthiness** | **SR: 0.95** — Primary Official. Government statistical agencies. Methodological changes can affect comparability. |
| **Source Interactions** | Confirmed by: Inflation Expectations (1.8), TIPS breakevens (4.4). Contradicted by: Real-time alternatives (15.2) when they diverge. Feeds into: Inflation Regime (7.5.2), Bond Market (4.1). |

### 3.3 Employment Release Calendar

| Attribute | Detail |
|---|---|
| **Identifier** | `CALENDAR:ECONOMIC:EMPLOYMENT` |
| **Why It Matters** | Non-farm payrolls is the most market-moving economic release. Employment data drives Fed policy expectations, consumer spending forecasts, and wage inflation. The "most important number in markets" designation is well-earned. |
| **Update Frequency** | Non-farm payrolls: monthly (first Friday). Unemployment rate: monthly. Jobless claims: weekly. |
| **Trustworthiness** | **SR: 0.95** — Primary Official (BLS). High reliability but subject to benchmark revisions. Jobless claims are most reliable (administrative data). |
| **Source Interactions** | Confirmed by: Jobless Claims (1.7b), ADP (1.7c), Consumer Spending (1.10). Contradicted by: High-frequency alternatives (15.3) when they diverge. Feeds into: Growth Regime (7.5.2), Wage Inflation (1.13). |

### 3.4 Retail Sales Release Calendar

| Attribute | Detail |
|---|---|
| **Identifier** | `CALENDAR:ECONOMIC:RETAIL` |
| **Why It Matters** | Retail sales provide the most timely measure of consumer demand. Consumer spending is ~70% of US GDP. Retail sales surprises can trigger significant market moves, especially in consumer discretionary stocks. |
| **Update Frequency** | Monthly (typically 2-3 weeks after month-end). |
| **Trustworthiness** | **SR: 0.95** — Primary Official (Census Bureau). High reliability but subject to seasonal adjustment methodology changes. |
| **Source Interactions** | Confirmed by: GDP (1.5), Credit Card Data (15.2). Contradicted by: Employment (1.7) when income-consumption disconnect occurs. Feeds into: Growth Regime (7.5.2), Economic Activity (7.5.1). |

### 3.5 PMI/ISM Release Calendar

| Attribute | Detail |
|---|---|
| **Identifier** | `CALENDAR:ECONOMIC:PMI` |
| **Why It Matters** | PMI provides the most frequent measure of economic activity. The 50.0 threshold is critical — above 50 = expansion, below 50 = contraction. PMI flash estimates provide early warning of economic turning points. |
| **Update Frequency** | PMI: monthly (first business day). Flash PMI: monthly (1st week). ISM: monthly (first business day). |
| **Trustworthiness** | **SR: 0.95** — Primary Official (ISM, IHS Markit). Survey-based but highly reliable. Flash estimates subject to revision. |
| **Source Interactions** | Confirmed by: GDP (1.5), Industrial Production (1.9). Contradicted by: High-frequency alternatives (15.3, 15.4) when they diverge. Feeds into: Growth Regime (7.5.2), Economic Activity (7.5.1). |

### 3.6 Central Bank Meeting Calendar

| Attribute | Detail |
|---|---|
| **Identifier** | `CALENDAR:ECONOMIC:CENTRAL_BANK` |
| **Why It Matters** | Central bank meetings are the primary driver of monetary policy expectations. FOMC, ECB, BoJ, and other central bank meetings can trigger significant market volatility. Forward guidance from these meetings shapes scenario generation. |
| **Update Frequency** | Scheduled meetings (8×/year for major central banks). Unscheduled emergency meetings possible. |
| **Trustworthiness** | **SR: 1.0** — Primary Official. Direct central bank publications. No intermediary. |
| **Source Interactions** | Confirmed by: Policy Rates (1.1), Forward Guidance (1.2). Contradicted by: Market pricing (6.4, 8.4) when guidance diverges. Feeds into: All monetary policy analysis, Yield Curve (5.1), FX (8.1). |

### 3.7 Fiscal Policy Calendar

| Attribute | Detail |
|---|---|
| **Identifier** | `CALENDAR:ECONOMIC:FISCAL` |
| **Why It Matters** | Fiscal policy announcements (budgets, stimulus packages, tax changes) can significantly impact markets. Government spending directly affects sector allocation and long-term growth prospects. |
| **Update Frequency** | Government budgets: annually (varies by country). Stimulus announcements: ad-hoc. Tax policy changes: ad-hoc. |
| **Trustworthiness** | **SR: 0.95** — Primary Official for government announcements; 0.85 for third-party fiscal aggregators. Political uncertainty can affect reliability. |
| **Source Interactions** | Confirmed by: GDP (1.5), Bond Market spreads (4.3) when fiscal concerns emerge. Contradicted by: Market fiscal pricing (6.4) when expectations diverge. Feeds into: Macro Analysis (7.5), Bond Market (4.1). |

### 3.8 Trade Data Calendar

| Attribute | Detail |
|---|---|
| **Identifier** | `CALENDAR:ECONOMIC:TRADE` |
| **Why It Matters** | Trade data affects currency values, import prices, and external vulnerability. Trade surprises can trigger significant moves in commodity currencies and emerging markets. |
| **Update Frequency** | Monthly (typically 30-45 days after month-end). Subject to significant revisions. |
| **Trustworthiness** | **SR: 0.95** — Primary Official. Government statistical agencies. Trade data is administrative but subject to valuation and timing adjustments. |
| **Source Interactions** | Confirmed by: Currency flows (8.1), Capital flows (13.4). Contradicted by: Alternative trade proxies (15.5) when they diverge. Feeds into: Global Liquidity (1.12), FX (8.1). |

---

## 4. Bond Market

Bond market sources provide insight into interest rate expectations, credit conditions, and risk premiums. They are critical for yield curve analysis and monetary policy assessment.

### 4.1 Treasury Yields

| Attribute | Detail |
|---|---|
| **Identifier** | `BOND:GOVERNMENT:TREASURY` |
| **Why It Matters** | Treasury yields are the foundation of all asset pricing. The yield curve shape (normal, flat, inverted) is a powerful recession predictor. Individual tenors (2y, 5y, 10y, 30y) carry different information — short-end reflects policy expectations, long-end reflects growth/inflation expectations. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. Intraday highs/lows. |
| **Trustworthiness** | **SR: 0.95** — Primary Market. Exchange-traded data with high integrity. Minor delays possible in real-time feeds. |
| **Source Interactions** | Confirmed by: Fed Funds Futures (6.4), OIS (5.2). Contradicted by: TIPS breakevens (4.4) when inflation expectations diverge. Feeds into: Yield Curve (5.1), Bond Market (4.1), Macro Analysis (7.5). |

### 4.2 Corporate Bond Spreads

| Attribute | Detail |
|---|---|
| **Identifier** | `BOND:CORPORATE:SPREADS` |
| **Why It Matters** | Credit spreads reflect the market's assessment of default risk and risk appetite. Spread widening signals deteriorating credit conditions or increasing risk aversion. Spread tightening signals improving conditions. Critical for liquidity analysis (Section 7.7). |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, ICE). Market-based but subject to liquidity adjustments. High-yield spreads more volatile than investment-grade. |
| **Source Interactions** | Confirmed by: Equity volatility (6.1, 12.1), Credit spreads (13.6). Contradicted by: Economic data (1.5, 1.7) when spreads diverge from fundamentals. Feeds into: Liquidity Analysis (7.7), Technical Analysis (7.6). |

### 4.3 Municipal Bonds

| Attribute | Detail |
|---|---|
| **Identifier** | `BOND:MUNICIPAL` |
| **Why It Matters** | Municipal bonds are sensitive to fiscal policy and state/local government finances. Muni yields are compared to Treasuries to assess the "muni penalty." Muni markets can signal regional economic stress. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, ICE). Market-based but less liquid than Treasuries. Pricing can be stale for less-traded issues. |
| **Source Interactions** | Confirmed by: Tax policy data (1.4), State/local fiscal data. Contradicted by: Treasury yields (4.1) when muni-Treasury ratios diverge from historical norms. Feeds into: Bond Market (4.1), Macro Analysis (7.5). |

### 4.4 TIPS (Treasury Inflation-Protected Securities)

| Attribute | Detail |
|---|---|
| **Identifier** | `BOND:TIPS:BREAKEVEN` |
| **Why It Matters** | TIPS breakeven inflation rates are the most direct market-based measure of inflation expectations. They are more forward-looking than survey data and update in real-time. Critical for inflation regime classification (Section 7.5.2). |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, Treasury). Market-based but include a risk premium. 5y and 10y breakevens are most reliable. |
| **Source Interactions** | Confirmed by: Inflation Expectations (1.8), CPI (1.6). Contradicted by: Survey data when market and survey expectations diverge. Feeds into: Inflation Regime (7.5.2), Bond Market (4.1). |

### 4.5 Agency MBS

| Attribute | Detail |
|---|---|
| **Identifier** | `BOND:MBS:AGENCY` |
| **Why It Matters** | Agency MBS are a key component of the Fed's balance sheet and a major source of global dollar funding. MBS spreads reflect prepayment risk and Fed policy expectations. Changes in Fed MBS purchases directly affect the entire credit market. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, ICE). Market-based but less transparent than Treasuries. Pricing models can introduce noise. |
| **Source Interactions** | Confirmed by: Fed Balance Sheet (1.3), Treasury yields (4.1). Contradicted by: Credit spreads (4.2) when prepayment expectations diverge. Feeds into: Liquidity Analysis (7.7), Bond Market (4.1). |

### 4.6 International Sovereign Bonds

| Attribute | Detail |
|---|---|
| **Identifier** | `BOND:SOVEREIGN:INTERNATIONAL` |
| **Why It Matters** | Sovereign bond yields in major economies (Germany, UK, Japan, Canada, Australia) provide cross-country policy comparison and carry trade analysis. Bund yields are particularly important for European monetary policy assessment. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market for major economies; 0.85 for emerging markets. Market-based with high integrity for developed markets. EM sovereigns subject to higher risk premiums. |
| **Source Interactions** | Confirmed by: Central bank policy (2.1–2.9), FX (8.1). Contradicted by: Currency volatility (8.4) when sovereign stress emerges. Feeds into: Yield Curve (5.1), FX (8.1), Macro Analysis (7.5). |

### 4.7 Credit Default Swaps (CDS)

| Attribute | Detail |
|---|---|
| **Identifier** | `BOND:CDS:SPREADS` |
| **Why It Matters** | CDS spreads are the purest measure of credit risk, free from recovery assumptions. They provide early warning of credit stress and are a key input for liquidity analysis. CDS on sovereigns can signal fiscal distress. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, Markit). Market-based but less liquid for longer-dated or less-traded names. Pricing can be volatile. |
| **Source Interactions** | Confirmed by: Corporate spreads (4.2), Sovereign yields (4.6). Contradicted by: Equity volatility (6.1) when credit and equity markets diverge. Feeds into: Liquidity Analysis (7.7), Technical Analysis (7.6). |

### 4.8 Bond ETF Flows

| Attribute | Detail |
|---|---|
| **Identifier** | `BOND:ETF:FLOWS` |
| **Why It Matters** | Bond ETF flows provide real-time insight into investor demand and positioning. Large inflows/outflows can signal shifts in risk appetite or sector rotation. ETF flows often lead underlying bond market movements. |
| **Update Frequency** | Daily (end-of-day). Weekly and monthly aggregations. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (ETF providers, Bloomberg). Direct from fund managers but aggregated and potentially delayed. |
| **Source Interactions** | Confirmed by: COT data (7.1–7.4), Bond yields (4.1). Contradicted by: Individual bond trades when ETF premiums/discounts emerge. Feeds into: Liquidity Analysis (7.7), Positioning (7.3). |

### 4.9 Repo Market Data

| Attribute | Detail |
|---|---|
| **Identifier** | `BOND:REPO:RATES` |
| **Why It Matters** | Repo rates reflect the true cost of short-term dollar funding. Repo market stress is an early warning sign of broader liquidity problems. SOFR is derived from repo transactions and is the new risk-free rate. |
| **Update Frequency** | Daily (SOFR published at 8:00 AM ET). Tri-party repo: daily. GCF repo: daily. |
| **Trustworthiness** | **SR: 0.95** — Primary Official (FRB for SOFR). Transaction-based data with high integrity. However, repo markets can be volatile and subject to manipulation. |
| **Source Interactions** | Confirmed by: Fed Funds (2.1), Money Supply (13.1). Contradicted by: Bond yields (4.1) when repo stress emerges. Feeds into: Liquidity Analysis (7.7), Yield Curve (5.1). |

### 4.10 Bond Market Sentiment Indicators

| Attribute | Detail |
|---|---|
| **Identifier** | `BOND:SENTIMENT:INDICATORS` |
| **Why It Matters** | Sentiment indicators (e.g., AAII Bond Sentiment, NAAIM Bond Exposure) provide contrarian signals. Extreme bullishness or bearishness in bonds can signal turning points. Complements technical analysis (Section 7.6). |
| **Update Frequency** | Weekly (AAII), monthly (NAAIM). |
| **Trustworthiness** | **SR: 0.75** — Secondary Consensus. Survey-based data with inherent noise. Best used as a contrarian indicator rather than a directional signal. |
| **Source Interactions** | Confirmed by: Bond yields (4.1), COT data (7.1–7.4). Contradicted by: Technical indicators (6.1, 12.1) when sentiment diverges from price action. Feeds into: Sentiment Analysis (14.1–14.6), Technical Analysis (7.6). |

---

## 5. Yield Curve

Yield curve sources provide the term structure of interest rates, which is a powerful predictor of economic cycles and monetary policy effectiveness.

### 5.1 Treasury Yield Curve

| Attribute | Detail |
|---|---|
| **Identifier** | `YIELDCURVE:TREASURY:US` |
| **Why It Matters** | The yield curve shape is the single best predictor of recessions. An inverted curve (2s10s < 0) has preceded every US recession in the past 50 years. The curve also reflects market expectations of future policy rates and inflation. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market. Exchange-traded data with high integrity. |
| **Source Interactions** | Confirmed by: Fed Funds Futures (6.4), OIS (5.2). Contradicted by: Forward guidance (1.2) when policy path diverges from market pricing. Feeds into: Macro Analysis (7.5), Bond Market (4.1), Scenarios (7.9). |

### 5.2 OIS (Overnight Index Swap) Curve

| Attribute | Detail |
|---|---|
| **Identifier** | `YIELDCURVE:OIS:GLOBAL` |
| **Why It Matters** | The OIS curve represents the risk-free rate for different maturities. It is the benchmark for pricing interest rate derivatives and is used for collateralized transactions. OIS spreads over Treasury yields reflect counterparty risk. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, ICE). Market-based but less transparent than Treasury data. SOFR, ESTR, SONIA, etc. are published by central banks. |
| **Source Interactions** | Confirmed by: Treasury yields (5.1), Repo rates (4.9). Contradicted by: Credit spreads (4.2) when counterparty risk diverges. Feeds into: Yield Curve (5.1), Bond Market (4.1), Liquidity Analysis (7.7). |

### 5.3 Corporate Yield Curve

| Attribute | Detail |
|---|---|
| **Identifier** | `YIELDCURVE:CORPORATE` |
| **Why It Matters** | The corporate yield curve incorporates credit risk at different maturities. The spread between corporate and government curves reflects the term structure of credit risk. Changes in this spread signal shifts in credit conditions. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, ICE). Market-based but less liquid than Treasuries. |
| **Source Interactions** | Confirmed by: Credit spreads (4.2), CDS (4.7). Contradicted by: Economic data (1.5, 1.7) when credit conditions diverge from fundamentals. Feeds into: Bond Market (4.1), Liquidity Analysis (7.7). |

### 5.4 Municipal Yield Curve

| Attribute | Detail |
|---|---|
| **Identifier** | `YIELDCURVE:MUNICIPAL` |
| **Why It Matters** | The municipal yield curve reflects state and local government financing conditions. The muni-Treasury yield ratio is a key indicator of relative value. Municipal curves can signal regional economic stress. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, ICE). Market-based but less liquid than Treasuries. |
| **Source Interactions** | Confirmed by: Municipal bonds (4.3), Tax policy (1.4). Contradicted by: Treasury yields (5.1) when muni-Treasury ratios diverge from historical norms. Feeds into: Bond Market (4.1), Macro Analysis (7.5). |

### 5.5 International Yield Curves

| Attribute | Detail |
|---|---|
| **Identifier** | `YIELDCURVE:INTERNATIONAL` |
| **Why It Matters** | International yield curves (Bund, Gilts, JGB, BTP, etc.) provide cross-country policy comparison and carry trade analysis. Currency-adjusted yield differentials drive FX movements and capital flows. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market for major economies; 0.85 for emerging markets. Market-based with high integrity for developed markets. |
| **Source Interactions** | Confirmed by: Central bank policy (2.1–2.9), FX (8.1). Contradicted by: Currency volatility (8.4) when sovereign stress emerges. Feeds into: Yield Curve (5.1), FX (8.1), Macro Analysis (7.5). |

---

## 6. Options

Options sources provide insight into market-implied volatility, risk sentiment, and positioning. They are critical for volatility analysis and scenario generation.

### 6.1 VIX (Volatility Index)

| Attribute | Detail |
|---|---|
| **Identifier** | `OPTIONS:VIX` |
| **Why It Matters** | The VIX is the market's expectation of 30-day S&P 500 volatility. It is the primary measure of equity market fear and a key contrarian indicator. VIX spikes often mark market bottoms; VIX declines often mark market tops. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CBOE). Calculated from S&P 500 options prices. High integrity but can be affected by options market illiquidity. |
| **Source Interactions** | Confirmed by: Equity volatility (6.2), Put/Call ratios (7.1–7.4). Contradicted by: Actual volatility (12.1) when implied diverges from realized. Feeds into: Volatility Analysis (12.1–12.8), Technical Analysis (7.6), Sentiment (14.1–14.6). |

### 6.2 Equity Options Implied Volatility

| Attribute | Detail |
|---|---|
| **Identifier** | `OPTIONS:EQUITY:IV` |
| **Why It Matters** | Implied volatility surfaces for individual stocks and indices provide granular insight into market expectations. IV rank and IV percentile are key inputs for options trading strategies. Skew reveals market's view of tail risk. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (CBOE, Bloomberg). Market-based but less transparent for individual stocks. Index options (SPX, NDXX) are most reliable. |
| **Source Interactions** | Confirmed by: VIX (6.1), Equity volatility (12.1). Contradicted by: Realized volatility (12.1) when implied diverges from actual. Feeds into: Technical Analysis (7.6), Volatility Analysis (12.1–12.8). |

### 6.3 FX Options Implied Volatility

| Attribute | Detail |
|---|---|
| **Identifier** | **OPTIONS:FX:IV** |
| **Why It Matters** | FX implied volatility surfaces provide insight into currency risk expectations. The risk reversal (25d RR) reveals market's view of asymmetric risk. FX vol is critical for carry trade analysis and EM currency stress detection. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, Reuters). Market-based but less liquid for exotic currency pairs. G10 currency vol is most reliable. |
| **Source Interactions** | Confirmed by: FX spot (8.1), FX forwards (8.2). Contradicted by: Actual FX volatility when implied diverges from realized. Feeds into: FX Analysis (8.1–8.7), Volatility Analysis (12.1–12.8). |

### 6.4 Interest Rate Options (Eurodollar, SOFR)

| Attribute | Detail |
|---|---|
| **Identifier** | `OPTIONS:RATES` |
| **Why It Matters** | Interest rate options (Eurodollar futures, SOFR options) provide market-based expectations of future policy rates. The Eurodollar futures curve is a key input for Fed funds path estimation. Critical for yield curve analysis. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (CME, Bloomberg). Market-based with high integrity for major contracts. Less liquid for longer-dated options. |
| **Source Interactions** | Confirmed by: Treasury yields (4.1), OIS (5.2). Contradicted by: Forward guidance (1.2) when market pricing diverges from policy intent. Feeds into: Yield Curve (5.1), Bond Market (4.1), Macro Analysis (7.5). |

### 6.5 Options Positioning Data

| Attribute | Detail |
|---|---|
| **Identifier** | `OPTIONS:POSITIONING` |
| **Why It Matters** | Options positioning (put/call ratios, gamma exposure, delta exposure) reveals market sentiment and potential inflection points. High gamma exposure can amplify price movements. Put/call ratios are key contrarian indicators. |
| **Update Frequency** | Daily (end-of-day). Weekly and monthly aggregations. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (CBOE, OCC). Direct from clearing houses but aggregated and potentially delayed. |
| **Source Interactions** | Confirmed by: COT data (7.1–7.4), VIX (6.1). Contradicted by: Price action (6.2, 12.1) when positioning diverges from market direction. Feeds into: Technical Analysis (7.6), Sentiment (14.1–14.6). |

### 6.6 Put/Call Ratios

| Attribute | Detail |
|---|---|
| **Identifier** | `OPTIONS:PUT_CALL_RATIO` |
| **Why It Matters** | Put/call ratios are among the most reliable contrarian indicators. Extremely high ratios suggest excessive fear (potential buying opportunity); extremely low ratios suggest excessive complacency (potential selling opportunity). |
| **Update Frequency** | Daily (end-of-day). Weekly and monthly aggregations. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (CBOE). Direct from exchange but includes both opening and closing transactions, which can distort the signal. |
| **Source Interactions** | Confirmed by: VIX (6.1), COT data (7.1–7.4). Contradicted by: Price action (6.2, 12.1) when sentiment diverges from market direction. Feeds into: Sentiment Analysis (14.1–14.6), Technical Analysis (7.6). |

### 6.7 Volatility of Volatility (VVIX)

| Attribute | Detail |
|---|---|
| **Identifier** | `OPTIONS:VVIX` |
| **Why It Matters** | The VVIX measures the expected volatility of the VIX itself. High VVIX suggests uncertainty about future volatility — often seen during market transitions. Low VVIX suggests complacency about volatility risk. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CBOE). Calculated from VIX options prices. High integrity but can be affected by VIX options market illiquidity. |
| **Source Interactions** | Confirmed by: VIX (6.1), VXV (12.3). Contradicted by: Realized volatility of volatility when implied diverges from actual. Feeds into: Volatility Analysis (12.1–12.8), Technical Analysis (7.6). |

### 6.8 Options Skew Analysis

| Attribute | Detail |
|---|---|
| **Identifier** | `OPTIONS:SKEW` |
| **Why It Matters** | Options skew reveals the market's view of asymmetric tail risk. A steep negative skew (higher IV for puts) suggests fear of downside. A flat or positive skew suggests complacency. The CBOE SKEW Index tracks S&P 500 tail risk. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CBOE). Calculated from S&P 500 options prices. High integrity but can be affected by options market illiquidity. |
| **Source Interactions** | Confirmed by: VIX (6.1), Put/Call ratios (6.6). Contradicted by: Actual tail events when skew fails to predict them. Feeds into: Volatility Analysis (12.1–12.8), Technical Analysis (7.6). |

---

## 7. COT (Commitment of Traders)

COT sources provide insight into the positioning of different market participant groups. They are critical for contrarian analysis and positioning assessment.

### 7.1 COT Futures-Only Reports

| Attribute | Detail |
|---|---|
| **Identifier** | `COT:FUTURES_ONLY` |
| **Why It Matters** | The COT report shows net positions of commercials, large speculators, and small speculators in futures markets. Commercials are typically right (they hedge real exposure); large specs are trend-followers; small specs are often wrong. Extreme positioning by any group is a contrarian signal. |
| **Update Frequency** | Weekly (released Friday at 3:00 PM ET, covering data through Tuesday). |
| **Trustworthiness** | **SR: 1.0** — Primary Official (CFTC). Direct government publication. No revision. High integrity. |
| **Source Interactions** | Confirmed by: Options positioning (6.5), ETF flows (4.8). Contradicted by: Price action when positioning diverges from market direction. Feeds into: Positioning Analysis (7.7.3), Sentiment (14.1–14.6). |

### 7.2 COT Futures-and-Options Reports

| Attribute | Detail |
|---|---|
| **Identifier** | `COT:FUTURES_AND_OPTIONS` |
| **Why It Matters** | This report includes both futures and options positions, providing a more complete picture of market positioning. Options positions reveal sentiment through premium paid/received. Useful for identifying asymmetric positioning. |
| **Update Frequency** | Weekly (released Friday at 3:00 PM ET, covering data through Tuesday). |
| **Trustworthiness** | **SR: 1.0** — Primary Official (CFTC). Direct government publication. No revision. High integrity. |
| **Source Interactions** | Confirmed by: COT Futures-Only (7.1), Options positioning (6.5). Contradicted by: Price action when positioning diverges from market direction. Feeds into: Positioning Analysis (7.7.3), Sentiment (14.1–14.6). |

### 7.3 Disaggregated COT Reports

| Attribute | Detail |
|---|---|
| **Identifier** | `COT:DISAGGREGATED` |
| **Why It Matters** | Disaggregated COT reports break down positions by trader type (producer, merchant, processor, swap dealer, managed money, other reportables). This provides more granular insight into positioning across different participant groups. |
| **Update Frequency** | Weekly (released Friday at 3:00 PM ET, covering data through Tuesday). |
| **Trustworthiness** | **SR: 1.0** — Primary Official (CFTC). Direct government publication. No revision. High integrity. |
| **Source Interactions** | Confirmed by: COT Futures-Only (7.1), COT Futures-and-Options (7.2). Contradicted by: Price action when positioning diverges from market direction. Feeds into: Positioning Analysis (7.7.3), Sentiment (14.1–14.6). |

### 7.4 COT Trader Category Breakdowns

| Attribute | Detail |
|---|---|
| **Identifier** | `COT:CATEGORIES` |
| **Why It Matters** | Trader category breakdowns (commercials, large specs, small specs) provide contrarian signals. The commercials are typically right (they hedge real exposure); large specs are trend-followers; small specs are often wrong. The spread between categories reveals market dynamics. |
| **Update Frequency** | Weekly (released Friday at 3:00 PM ET, covering data through Tuesday). |
| **Trustworthiness** | **SR: 1.0** — Primary Official (CFTC). Direct government publication. No revision. High integrity. |
| **Source Interactions** | Confirmed by: COT Futures-Only (7.1), COT Futures-and-Options (7.2), Disaggregated COT (7.3). Contradicted by: Price action when positioning diverges from market direction. Feeds into: Positioning Analysis (7.7.3), Sentiment (14.1–14.6). |

---

## 8. Forex

Forex sources provide insight into currency markets, carry trades, and global capital flows. They are critical for cross-market analysis and risk sentiment assessment.

### 8.1 FX Spot Rates

| Attribute | Detail |
|---|---|
| **Identifier** | `FX:SPOT` |
| **Why It Matters** | FX spot rates reflect the relative value of currencies. Major pairs (EUR/USD, USD/JPY, GBP/USD, USD/CHF, AUD/USD, USD/CAD, NZD/USD) are the most liquid and reliable. FX rates are affected by interest rate differentials, economic data, and geopolitical events. |
| **Update Frequency** | Real-time 24/5 during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market. Major currency pairs are highly liquid with tight spreads. EM currency pairs less reliable. |
| **Source Interactions** | Confirmed by: Central bank policy (2.1–2.9), Interest rate differentials (5.1). Contradicted by: FX forwards (8.2) when carry trade expectations diverge. Feeds into: FX Analysis (8.1–8.7), Cross-Market Relationships (5.5). |

### 8.2 FX Forwards

| Attribute | Detail |
|---|---|
| **Identifier** | `FX:FORWARDS` |
| **Why It Matters** | FX forward rates reflect the market's expectation of future currency values, incorporating interest rate differentials and carry trade expectations. Forward points reveal the term structure of currency risk. Critical for carry trade analysis. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, Reuters). Market-based but less liquid than spot. Forward points can be affected by liquidity constraints. |
| **Source Interactions** | Confirmed by: FX spot (8.1), Interest rate differentials (5.1). Contradicted by: Spot rates when carry trade expectations diverge. Feeds into: FX Analysis (8.1–8.7), Cross-Market Relationships (5.5). |

### 8.3 FX Futures

| Attribute | Detail |
|---|---|
| **Identifier** | `FX:FUTURES` |
| **Why It Matters** | FX futures provide exchange-traded exposure to currency movements. They are more transparent than OTC forwards and provide positioning data through COT reports. FX futures are used for hedging and speculation. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CME, ICE). Exchange-traded with high integrity. More transparent than OTC forwards. |
| **Source Interactions** | Confirmed by: FX spot (8.1), FX forwards (8.2). Contradicted by: COT data (7.1–7.4) when futures positioning diverges from spot direction. Feeds into: FX Analysis (8.1–8.7), Positioning (7.7.3). |

### 8.4 Currency Futures Positioning

| Attribute | Detail |
|---|---|
| **Identifier** | `FX:FUTURES_POSITIONING` |
| **Why It Matters** | Currency futures positioning (via COT reports) reveals the positioning of different market participant groups. Extreme positioning is a contrarian signal. Positioning divergences between currencies can signal capital flow shifts. |
| **Update Frequency** | Weekly (released Friday at 3:00 PM ET, covering data through Tuesday). |
| **Trustworthiness** | **SR: 1.0** — Primary Official (CFTC). Direct government publication. No revision. High integrity. |
| **Source Interactions** | Confirmed by: COT reports (7.1–7.4), FX spot (8.1). Contradicted by: Spot rates when positioning diverges from market direction. Feeds into: Positioning Analysis (7.7.3), Sentiment (14.1–14.6). |

### 8.5 FX Volatility

| Attribute | Detail |
|---|---|
| **Identifier** | `FX:VOLATILITY` |
| **Why It Matters** | FX volatility surfaces provide insight into currency risk expectations. The risk reversal (25d RR) reveals market's view of asymmetric risk. FX vol is critical for carry trade analysis and EM currency stress detection. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, Reuters). Market-based but less liquid for exotic currency pairs. G10 currency vol is most reliable. |
| **Source Interactions** | Confirmed by: FX spot (8.1), FX forwards (8.2). Contradicted by: Actual FX volatility when implied diverges from realized. Feeds into: Volatility Analysis (12.1–12.8), FX Analysis (8.1–8.7). |

### 8.6 Central Bank FX Reserves

| Attribute | Detail |
|---|---|
| **Identifier** | `FX:RESERVES` |
| **Why It Matters** | Central bank FX reserves reveal the capacity and intent for currency intervention. Large reserve accumulation or depletion signals policy stance. Reserve currency allocations (USD, EUR, JPY, CNY) reveal global reserve preferences. |
| **Update Frequency** | Monthly (typically 45 days after month-end). Quarterly for detailed breakdowns. |
| **Trustworthiness** | **SR: 0.95** — Primary Official (IMF COFER, central banks). Direct government publication. However, intervention may not be fully disclosed. |
| **Source Interactions** | Confirmed by: FX spot (8.1), Central bank policy (2.1–2.9). Contradicted by: Unreported interventions when they surprise markets. Feeds into: FX Analysis (8.1–8.7), Macro Analysis (7.5). |

### 8.7 Cross Rates

| Attribute | Detail |
|---|---|
| **Identifier** | `FX:CROSS_RATES` |
| **Why It Matters** | Cross rates (non-USD currency pairs) reveal relative value between currencies. Cross rate arbitrage ensures consistency across the FX market. Cross rates are important for multi-currency portfolios and EM currency analysis. |
| **Update Frequency** | Real-time 24/5 during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.90** — Derived from major pair spot rates. Less liquid than major pairs but generally reliable. Pricing can be affected by liquidity constraints. |
| **Source Interactions** | Confirmed by: FX spot (8.1). Contradicted by: Arbitrage opportunities when cross rates diverge from synthetic rates. Feeds into: FX Analysis (8.1–8.7), Cross-Market Relationships (5.5). |

---

## 9. Gold

Gold sources provide insight into precious metals markets, safe-haven demand, and inflation hedging. They are critical for commodity analysis and risk sentiment assessment.

### 9.1 Spot Gold Price

| Attribute | Detail |
|---|---|
| **Identifier** | `GOLD:SPOT` |
| **Why It Matters** | Gold is the primary safe-haven asset and inflation hedge. Gold prices reflect global risk sentiment, real interest rates, and USD strength. Gold is negatively correlated with real yields and positively correlated with uncertainty. |
| **Update Frequency** | Real-time during trading hours (London/NYC overlap). End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (LBMA). London Bullion Market is the global benchmark. High integrity but can be affected by OTC pricing. |
| **Source Interactions** | Confirmed by: Real yields (5.1, 5.2), USD strength (8.1). Contradicted by: Gold ETF flows (9.4) when physical demand diverges from futures positioning. Feeds into: Commodity Analysis, Cross-Market Relationships (5.5). |

### 9.2 Gold Futures

| Attribute | Detail |
|---|---|
| **Identifier** | `GOLD:FUTURES` |
| **Why It Matters** | Gold futures provide exchange-traded exposure to gold prices. They are more transparent than OTC spot markets and provide positioning data through COT reports. Gold futures are used for hedging and speculation. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (COMEX). Exchange-traded with high integrity. More transparent than OTC spot. |
| **Source Interactions** | Confirmed by: Spot gold (9.1), COT data (7.1–7.4). Contradicted by: Physical demand (9.7) when futures positioning diverges from physical flows. Feeds into: Commodity Analysis, Positioning (7.7.3). |

### 9.3 Gold ETF Flows

| Attribute | Detail |
|---|---|
| **Identifier** | `GOLD:ETF:FLOWS` |
| **Why It Matters** | Gold ETF flows provide real-time insight into investor demand for gold. Large inflows/outflows signal shifts in safe-haven demand or inflation hedging. ETF flows often lead gold price movements. |
| **Update Frequency** | Daily (end-of-day). Weekly and monthly aggregations. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (ETF providers, Bloomberg). Direct from fund managers but aggregated and potentially delayed. |
| **Source Interactions** | Confirmed by: Spot gold (9.1), Gold futures (9.2). Contradicted by: Physical demand (9.7) when ETF flows diverge from physical purchases. Feeds into: Commodity Analysis, Liquidity Analysis (7.7). |

### 9.4 Gold Mining Stocks

| Attribute | Detail |
|---|---|
| **Identifier** | `GOLD:MINING_STOCKS` |
| **Why It Matters** | Gold mining stocks (GDX, GDXJ) are leveraged plays on gold prices. They reflect both gold price movements and mining sector fundamentals (costs, production, geopolitical risk). Gold stocks often outperform gold during bull markets and underperform during bear markets. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (NYSE, NASDAQ). Exchange-traded with high integrity. However, stock-specific factors can cause divergence from gold. |
| **Source Interactions** | Confirmed by: Spot gold (9.1), Gold futures (9.2). Contradicted by: Sector-specific news when mining stocks diverge from gold. Feeds into: Commodity Analysis, Technical Analysis (7.6). |

### 9.5 Gold Lease Rates

| Attribute | Detail |
|---|---|
| **Identifier** | `GOLD:LEASE_RATES` |
| **Why It Matters** | Gold lease rates reflect the cost of borrowing gold. Negative lease rates indicate strong demand for gold (borrowers are willing to pay to borrow). Lease rates are a contrarian indicator — extremely negative rates suggest excessive bullishness. |
| **Update Frequency** | Daily (end-of-day). |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (LBMA, Bloomberg). Derived from OTC market data. Less transparent than spot prices. |
| **Source Interactions** | Confirmed by: Spot gold (9.1), Gold futures (9.2). Contradicted by: ETF flows (9.3) when lease rates diverge from investor demand. Feeds into: Commodity Analysis, Liquidity Analysis (7.7). |

### 9.6 Central Bank Gold Reserves

| Attribute | Detail |
|---|---|
| **Identifier** | `GOLD:CENTRAL_BANK_RESERVES` |
| **Why It Matters** | Central bank gold purchases/sales are major market-moving events. Central banks are net buyers of gold, providing structural support. Large sales can depress prices. Reserve data reveals monetary policy intentions. |
| **Update Frequency** | Monthly (IMF COFER). Quarterly for detailed breakdowns. |
| **Trustworthiness** | **SR: 0.95** — Primary Official (IMF, central banks). Direct government publication. However, intervention may not be fully disclosed. |
| **Source Interactions** | Confirmed by: Spot gold (9.1), Gold ETF flows (9.3). Contradicted by: Unreported purchases when they surprise markets. Feeds into: Commodity Analysis, Macro Analysis (7.5). |

### 9.7 Physical Gold Demand/Supply

| Attribute | Detail |
|---|---|
| **Identifier** | `GOLD:PHYSICAL:DEMAND` |
| **Why It Matters** | Physical gold demand (jewelry, bars, coins) is the fundamental driver of long-term gold prices. Demand varies seasonally (Indian festivals, Chinese New Year) and with income levels. Supply is relatively fixed (mine production, recycling). |
| **Update Frequency** | Monthly (World Gold Council). Quarterly for detailed breakdowns. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (World Gold Council). Industry association data. Reliable but subject to estimation for informal markets. |
| **Source Interactions** | Confirmed by: Spot gold (9.1), Gold ETF flows (9.3). Contradicted by: Futures positioning (9.2) when physical demand diverges from speculative activity. Feeds into: Commodity Analysis, Macro Analysis (7.5). |

### 9.8 Gold Forward Curves

| Attribute | Detail |
|---|---|
| **Identifier** | `GOLD:FORWARD_CURVES` |
| **Why It Matters** | Gold forward curves reveal the term structure of gold pricing. Contango (futures > spot) suggests carrying costs exceed benefits; backwardation (futures < spot) suggests tight physical markets. Forward curves are critical for gold carry trade analysis. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (LBMA, Bloomberg). Derived from OTC market data. Less transparent than spot prices. |
| **Source Interactions** | Confirmed by: Spot gold (9.1), Gold futures (9.2). Contradicted by: Physical demand (9.7) when forward curves diverge from fundamentals. Feeds into: Commodity Analysis, Liquidity Analysis (7.7). |

---

## 10. Indices

Index sources provide broad market exposure and are the primary vehicles for systematic investment. They are critical for market regime identification and technical analysis.

### 10.1 S&P 500

| Attribute | Detail |
|---|---|
| **Identifier** | `INDICES:SPX` |
| **Why It Matters** | The S&P 500 is the primary barometer of US equity markets. It represents ~80% of total US equity market capitalization. The VIX is derived from S&P 500 options. All major equity analysis references the S&P 500 as the benchmark. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (S&P Dow Jones Indices). Exchange-traded with high integrity. The most liquid and reliable equity index. |
| **Source Interactions** | Confirmed by: VIX (6.1), Equity volatility (6.2). Contradicted by: Sector indices (10.8) when broad market diverges from sectors. Feeds into: Technical Analysis (7.6), Volatility Analysis (12.1–12.8). |

### 10.2 Dow Jones Industrial Average

| Attribute | Detail |
|---|---|
| **Identifier** | `INDICES:DJIA` |
| **Why It Matters** | The DJIA is the oldest equity index and a widely recognized market barometer. Though price-weighted (unlike cap-weighted S&P 500), it provides a different perspective on market movements. The 30 components represent established blue-chip companies. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (S&P Dow Jones Indices). Exchange-traded with high integrity. However, price-weighting methodology is outdated. |
| **Source Interactions** | Confirmed by: S&P 500 (10.1), Nasdaq (10.3). Contradicted by: Sector indices (10.8) when DJIA components diverge from broader market. Feeds into: Technical Analysis (7.6), Sentiment (14.1–14.6). |

### 10.3 Nasdaq Composite

| Attribute | Detail |
|---|---|
| **Identifier** | `INDICES:NDX` |
| **Why It Matters** | The Nasdaq Composite is heavily weighted toward technology and growth stocks. It is the primary gauge of tech sector performance and growth stock sentiment. The Nasdaq-100 (NDX) is the basis for popular ETFs (QQQ). |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (NASDAQ OMX). Exchange-traded with high integrity. The most liquid tech-focused index. |
| **Source Interactions** | Confirmed by: S&P 500 (10.1), Tech sector indices (10.8). Contradicted by: Value indices when growth diverges from value. Feeds into: Technical Analysis (7.6), Volatility Analysis (12.1–12.8). |

### 10.4 Russell 2000

| Attribute | Detail |
|---|---|
| **Identifier** | `INDICES:RUT` |
| **Why It Matters** | The Russell 2000 represents small-cap US equities. It is a key indicator of domestic economic health and credit conditions. Small caps are more sensitive to economic cycles and interest rate changes. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (FTSE Russell). Exchange-traded with high integrity. However, small-cap liquidity is lower than large-cap. |
| **Source Interactions** | Confirmed by: S&P 500 (10.1), Economic data (1.5, 1.7). Contradicted by: Large-cap indices when small-cap diverges from large-cap. Feeds into: Technical Analysis (7.6), Economic Analysis (7.5). |

### 10.5 International Indices

| Attribute | Detail |
|---|---|
| **Identifier** | `INDICES:INTERNATIONAL` |
| **Why It Matters** | International indices (FTSE 100, DAX, Nikkei 225, CAC 40, AEX, etc.) provide exposure to developed market equities. They are critical for cross-market analysis and global risk sentiment assessment. Currency effects are embedded in local-currency returns. |
| **Update Frequency** | Real-time during respective trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market for major exchanges; 0.85 for emerging markets. Exchange-traded with high integrity for developed markets. EM indices subject to higher risk. |
| **Source Interactions** | Confirmed by: FX (8.1), Local central bank policy (2.1–2.9). Contradicted by: S&P 500 (10.1) when international diverges from US. Feeds into: Cross-Market Relationships (5.5), Technical Analysis (7.6). |

### 10.6 Emerging Market Indices

| Attribute | Detail |
|---|---|
| **Identifier** | `INDICES:EM` |
| **Why It Matters** | EM indices (MSCI EM, FTSE Emerging, S&P Emerging) provide exposure to developing economies. They are highly sensitive to global risk sentiment, commodity prices, and USD strength. EM indices are leading indicators of global risk appetite. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (MSCI, FTSE). Market-based but less liquid and transparent than developed markets. Subject to higher volatility and political risk. |
| **Source Interactions** | Confirmed by: FX (8.1), Commodity prices (9.1, 11.1). Contradicted by: S&P 500 (10.1) when EM diverges from developed markets. Feeds into: Cross-Market Relationships (5.5), Technical Analysis (7.6). |

### 10.7 Volatility Indices

| Attribute | Detail |
|---|---|
| **Identifier** | `INDICES:VOLATILITY` |
| **Why It Matters** | Volatility indices (VIX, VXO, VXV, VVIX, GVZ, OVX) provide market-implied volatility expectations. They are leading indicators of market stress and risk sentiment. Volatility indices are negatively correlated with equity prices and positively correlated with uncertainty. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CBOE). Calculated from options prices. High integrity but can be affected by options market illiquidity. |
| **Source Interactions** | Confirmed by: Options data (6.1–6.8), Equity volatility (12.1–12.8). Contradicted by: Realized volatility when implied diverges from actual. Feeds into: Volatility Analysis (12.1–12.8), Technical Analysis (7.6), Sentiment (14.1–14.6). |

### 10.8 Sector Indices

| Attribute | Detail |
|---|---|
| **Identifier** | `INDICES:SECTOR` |
| **Why It Matters** | Sector indices (S&P 500 sectors, GICS classifications) provide exposure to specific industries. They are critical for sector rotation analysis and relative value assessment. Sector performance reveals market internals and economic cycle position. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (S&P Dow Jones, MSCI). Exchange-traded with high integrity. However, sector classification can change, affecting comparability. |
| **Source Interactions** | Confirmed by: S&P 500 (10.1), Economic data (1.5, 1.7). Contradicted by: Broad market indices when sectors diverge from overall market. Feeds into: Technical Analysis (7.6), Macro Analysis (7.5). |

### 10.9 Index ETF Flows

| Attribute | Detail |
|---|---|
| **Identifier** | `INDICES:ETF:FLOWS` |
| **Why It Matters** | Index ETF flows provide real-time insight into investor demand for broad market exposure. Large inflows/outflows signal shifts in risk appetite or market direction. ETF flows often lead underlying index movements. |
| **Update Frequency** | Daily (end-of-day). Weekly and monthly aggregations. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (ETF providers, Bloomberg). Direct from fund managers but aggregated and potentially delayed. |
| **Source Interactions** | Confirmed by: COT data (7.1–7.4), Index prices (10.1–10.8). Contradicted by: Individual stock trades when ETF premiums/discounts emerge. Feeds into: Liquidity Analysis (7.7), Sentiment (14.1–14.6). |

---

## 11. Crypto

Crypto sources provide insight into digital asset markets, which are increasingly correlated with traditional risk assets. They are critical for understanding emerging risk sentiment and technological disruption.

### 11.1 Bitcoin Price

| Attribute | Detail |
|---|---|
| **Identifier** | `CRYPTO:BTC` |
| **Why It Matters** | Bitcoin is the largest and most liquid cryptocurrency. It serves as a proxy for the entire crypto market and is increasingly viewed as "digital gold" — a hedge against inflation and currency debasement. Bitcoin's correlation with risk assets varies over time. |
| **Update Frequency** | Real-time 24/7. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Coinbase, Binance, Kraken). Market-based but fragmented across exchanges. Price discrepancies can occur. |
| **Source Interactions** | Confirmed by: Ethereum (11.2), Altcoin prices (11.3). Contradicted by: Traditional risk assets when crypto diverges from equities. Feeds into: Cross-Market Relationships (5.5), Sentiment (14.1–14.6). |

### 11.2 Ethereum Price

| Attribute | Detail |
|---|---|
| **Identifier** | `CRYPTO:ETH` |
| **Why It Matters** | Ethereum is the second-largest cryptocurrency and the foundation for DeFi and smart contracts. ETH price reflects demand for blockchain-based applications and developer activity. ETH/BTC ratio reveals relative strength between the two largest cryptocurrencies. |
| **Update Frequency** | Real-time 24/7. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Coinbase, Binance, Kraken). Market-based but fragmented across exchanges. Price discrepancies can occur. |
| **Source Interactions** | Confirmed by: Bitcoin (11.1), Altcoin prices (11.3). Contradicted by: DeFi activity when ETH diverges from protocol usage. Feeds into: Cross-Market Relationships (5.5), Sentiment (14.1–14.6). |

### 11.3 Altcoin Prices

| Attribute | Detail |
|---|---|
| **Identifier** | `CRYPTO:ALTCOINS` |
| **Why It Matters** | Altcoin prices (Solana, Cardano, Polkadot, etc.) reveal speculative appetite and innovation trends in the crypto ecosystem. Altcoin seasons (outperformance vs. Bitcoin) signal high risk appetite. Altcoin crashes often precede broader market downturns. |
| **Update Frequency** | Real-time 24/7. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.70** — Secondary Verified (various exchanges). Market-based but highly fragmented and volatile. Many altcoins have low liquidity. |
| **Source Interactions** | Confirmed by: Bitcoin (11.1), Ethereum (11.2). Contradicted by: Bitcoin when altcoins diverge from the dominant cryptocurrency. Feeds into: Cross-Market Relationships (5.5), Sentiment (14.1–14.6). |

### 11.4 Crypto Futures

| Attribute | Detail |
|---|---|
| **Identifier** | `CRYPTO:FUTURES` |
| **Why It Matters** | Crypto futures provide leveraged exposure and reveal market expectations. Futures basis (spot vs. futures price) indicates market sentiment — positive basis suggests bullishness, negative basis suggests bearishness. Funding rates reveal positioning pressure. |
| **Update Frequency** | Real-time 24/7. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.80** — Secondary Verified (CME, Binance, Bybit). Market-based but less regulated than traditional futures. |
| **Source Interactions** | Confirmed by: Spot prices (11.1–11.3), Funding rates (11.5). Contradicted by: Spot prices when futures diverge significantly. Feeds into: Volatility Analysis (12.1–12.8), Sentiment (14.1–14.6). |

### 11.5 Stablecoin Supply

| Attribute | Detail |
|---|---|
| **Identifier** | `CRYPTO:STABLECOIN` |
| **Why It Matters** | Stablecoin supply (USDT, USDC, BUSD) reflects liquidity available for crypto trading. Rapid stablecoin growth signals increasing market participation; rapid contraction signals risk-off behavior. Stablecoin supply is a leading indicator of crypto market direction. |
| **Update Frequency** | Daily (end-of-day). Weekly and monthly aggregations. |
| **Trustworthiness** | **SR: 0.80** — Secondary Verified (blockchain analytics, issuer reports). On-chain data is transparent but issuer reserves may not be fully audited. |
| **Source Interactions** | Confirmed by: Crypto prices (11.1–11.3), Crypto futures (11.4). Contradicted by: Traditional liquidity (13.1) when crypto liquidity diverges from traditional. Feeds into: Liquidity Analysis (7.7), Sentiment (14.1–14.6). |

### 11.6 On-Chain Metrics

| Attribute | Detail |
|---|---|
| **Identifier** | `CRYPTO:ONCHAIN` |
| **Why It Matters** | On-chain metrics (transaction volume, active addresses, hash rate, miner supply) provide fundamental insight into blockchain network health. These metrics are transparent and tamper-resistant. Hash rate reveals miner confidence; active addresses reveal user adoption. |
| **Update Frequency** | Daily (end-of-day). Real-time for some metrics. |
| **Trustworthiness** | **SR: 0.90** — Primary Market (blockchain data). On-chain data is transparent and verifiable. However, interpretation can be complex and subject to methodology changes. |
| **Source Interactions** | Confirmed by: Crypto prices (11.1–11.3), Stablecoin supply (11.5). Contradicted by: Price action when on-chain metrics diverge from market direction. Feeds into: Technical Analysis (7.6), Sentiment (14.1–14.6). |

### 11.7 Exchange Flows

| Attribute | Detail |
|---|---|
| **Identifier** | `CRYPTO:EXCHANGE_FLOWS` |
| **Why It Matters** | Exchange flows (net inflows/outflows) reveal whether investors are moving crypto to or from exchanges. Net inflows suggest selling pressure; net outflows suggest accumulation. Large flows often precede price movements. |
| **Update Frequency** | Daily (end-of-day). Real-time for major exchanges. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (blockchain analytics). On-chain data is transparent but exchange-specific flows may not represent the entire market. |
| **Source Interactions** | Confirmed by: Crypto prices (11.1–11.3), On-chain metrics (11.6). Contradicted by: Price action when flows diverge from market direction. Feeds into: Liquidity Analysis (7.7), Sentiment (14.1–14.6). |

### 11.8 DeFi Metrics

| Attribute | Detail |
|---|---|
| **Identifier** | `CRYPTO:DEFI` |
| **Why It Matters** | DeFi metrics (TVL, lending rates, protocol revenue) reveal the health and growth of decentralized finance. TVL growth signals increasing adoption of blockchain-based financial services. Lending rates reveal supply-demand dynamics for crypto capital. |
| **Update Frequency** | Daily (end-of-day). Real-time for major protocols. |
| **Trustworthiness** | **SR: 0.80** — Secondary Verified (DeFiLlama, Dune Analytics). On-chain data is transparent but TVL calculations can vary by methodology. |
| **Source Interactions** | Confirmed by: Ethereum price (11.2), On-chain metrics (11.6). Contradicted by: Traditional finance metrics when DeFi diverges from traditional. Feeds into: Technical Analysis (7.6), Sentiment (14.1–14.6). |

---

## 12. Volatility

Volatility sources provide insight into market-implied and realized volatility across asset classes. They are critical for risk assessment, options pricing, and scenario generation.

### 12.1 VIX (CBOE Volatility Index)

| Attribute | Detail |
|---|---|
| **Identifier** | `VOLATILITY:VIX` |
| **Why It Matters** | The VIX is the market's expectation of 30-day S&P 500 volatility. It is the primary measure of equity market fear and a key contrarian indicator. VIX spikes often mark market bottoms; VIX declines often mark market tops. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CBOE). Calculated from S&P 500 options prices. High integrity but can be affected by options market illiquidity. |
| **Source Interactions** | Confirmed by: Equity options IV (6.2), Put/Call ratios (6.6). Contradicted by: Realized volatility (12.8) when implied diverges from actual. Feeds into: Technical Analysis (7.6), Sentiment (14.1–14.6). |

### 12.2 VXO (CBOE OEX Volatility Index)

| Attribute | Detail |
|---|---|
| **Identifier** | `VOLATILITY:VXO` |
| **Why It Matters** | The VXO measures 30-day implied volatility of the OEX (S&P 100) options. It focuses on large, liquid stocks and is less volatile than the VIX. VXO provides a cleaner measure of broad market volatility expectations. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CBOE). Calculated from S&P 100 options prices. High integrity but covers a narrower universe than VIX. |
| **Source Interactions** | Confirmed by: VIX (12.1), Equity options IV (6.2). Contradicted by: Realized volatility (12.8) when implied diverges from actual. Feeds into: Volatility Analysis, Technical Analysis (7.6). |

### 12.3 VXV (CBOE S&P 500 3-Month Volatility Index)

| Attribute | Detail |
|---|---|
| **Identifier** | `VOLATILITY:VXV` |
| **Why It Matters** | The VXV measures 3-month implied volatility of the S&P 500. It provides a longer-term volatility perspective than the VIX. The VIX/VXV ratio reveals the volatility term structure — inverted (VIX > VXV) suggests near-term fear; contango (VXV > VIX) suggests complacency. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CBOE). Calculated from S&P 500 options prices. High integrity but can be affected by options market illiquidity. |
| **Source Interactions** | Confirmed by: VIX (12.1), Options skew (6.8). Contradicted by: Realized volatility (12.8) when implied diverges from actual. Feeds into: Volatility Analysis, Technical Analysis (7.6). |

### 12.4 VVIX (CBOE Volatility of Volatility Index)

| Attribute | Detail |
|---|---|
| **Identifier** | `VOLATILITY:VVIX` |
| **Why It Matters** | The VVIX measures the expected volatility of the VIX itself. High VVIX suggests uncertainty about future volatility — often seen during market transitions. Low VVIX suggests complacency about volatility risk. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CBOE). Calculated from VIX options prices. High integrity but can be affected by VIX options market illiquidity. |
| **Source Interactions** | Confirmed by: VIX (12.1), Options data (6.7). Contradicted by: Realized volatility of volatility when implied diverges from actual. Feeds into: Volatility Analysis, Technical Analysis (7.6). |

### 12.5 GVZ (CBOE Gold Volatility Index)

| Attribute | Detail |
|---|---|
| **Identifier** | `VOLATILITY:GVZ` |
| **Why It Matters** | The GVZ measures implied volatility of gold options. It reflects market expectations of gold price volatility. High GVZ suggests uncertainty about gold prices; low GVZ suggests complacency. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CBOE). Calculated from gold options prices. High integrity but gold options market is less liquid than equity options. |
| **Source Interactions** | Confirmed by: Gold price (9.1), Gold options IV (6.2). Contradicted by: Realized gold volatility when implied diverges from actual. Feeds into: Volatility Analysis, Commodity Analysis. |

### 12.6 OVX (CBOE Crude Oil Volatility Index)

| Attribute | Detail |
|---|---|
| **Identifier** | `VOLATILITY:OVX` |
| **Why It Matters** | The OVX measures implied volatility of crude oil options. It reflects market expectations of oil price volatility. High OVX suggests uncertainty about oil prices; low OVX suggests complacency. Oil volatility is critical for inflation analysis. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CBOE). Calculated from oil options prices. High integrity but oil options market is less liquid than equity options. |
| **Source Interactions** | Confirmed by: Oil price, Oil options IV (6.2). Contradicted by: Realized oil volatility when implied diverges from actual. Feeds into: Volatility Analysis, Commodity Analysis. |

### 12.7 FX Volatility Indices

| Attribute | Detail |
|---|---|
| **Identifier** | `VOLATILITY:FX` |
| **Why It Matters** | FX volatility indices (e.g., JPMorgan GBI, Deutsche Bank FXVI) measure implied volatility of major currency pairs. They reflect market expectations of currency volatility. High FX vol suggests uncertainty about exchange rates; low FX vol suggests complacency. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (JPMorgan, Deutsche Bank). Market-based but less transparent than equity volatility indices. |
| **Source Interactions** | Confirmed by: FX spot (8.1), FX options IV (6.3). Contradicted by: Realized FX volatility when implied diverges from actual. Feeds into: Volatility Analysis, FX Analysis (8.1–8.7). |

### 12.8 Realized Volatility

| Attribute | Detail |
|---|---|
| **Identifier** | `VOLATILITY:REALIZED` |
| **Why It Matters** | Realized volatility measures actual price fluctuations over a given period. It is the ground truth against which implied volatility is compared. High realized vol suggests turbulent markets; low realized vol suggests calm markets. |
| **Update Frequency** | Daily (end-of-day). Intraday for high-frequency analysis. |
| **Trustworthiness** | **SR: 0.95** — Primary Market. Calculated from actual price data. High integrity but methodology choices (e.g., sampling frequency) can affect results. |
| **Source Interactions** | Confirmed by: Price data (10.1–10.8, 9.1, 11.1–11.3). Contradicted by: Implied volatility (12.1–12.7) when realized diverges from implied. Feeds into: Volatility Analysis, Technical Analysis (7.6). |

---

## 13. Liquidity

Liquidity sources provide insight into the availability of funding, market depth, and transaction costs. They are critical for risk assessment and market regime identification.

### 13.1 Money Supply (M1, M2, MZM)

| Attribute | Detail |
|---|---|
| **Identifier** | `LIQUIDITY:MONEY_SUPPLY` |
| **Why It Matters** | Money supply measures the amount of currency and near-money in circulation. M2 growth is a leading indicator of inflation and economic activity. Rapid money supply growth can signal future inflation; stagnation can signal economic distress. |
| **Update Frequency** | Weekly (M1, M2). Monthly for detailed breakdowns. |
| **Trustworthiness** | **SR: 0.95** — Primary Official (Federal Reserve). Direct government publication. High integrity but subject to methodological changes. |
| **Source Interactions** | Confirmed by: Fed Balance Sheet (1.3), Repo rates (4.9). Contradicted by: Inflation (1.6) when money supply growth diverges from price changes. Feeds into: Liquidity Analysis (7.7), Macro Analysis (7.5). |

### 13.2 Bank Lending Data

| Attribute | Detail |
|---|---|
| **Identifier** | `LIQUIDITY:BANK_LENDING` |
| **Why It Matters** | Bank lending data reveals the availability of credit to businesses and consumers. Tightening credit conditions can signal economic distress; loosening conditions can signal recovery. Lending data is a key input for liquidity regime classification. |
| **Update Frequency** | Weekly (Senior Loan Officer Survey: quarterly). Monthly for detailed breakdowns. |
| **Trustworthiness** | **SR: 0.95** — Primary Official (Federal Reserve). Direct government publication. However, survey-based data can be subjective. |
| **Source Interactions** | Confirmed by: Money Supply (13.1), Credit conditions (13.6). Contradicted by: Economic data (1.5, 1.7) when lending diverges from economic fundamentals. Feeds into: Liquidity Analysis (7.7), Macro Analysis (7.5). |

### 13.3 Credit Conditions

| Attribute | Detail |
|---|---|
| **Identifier** | `LIQUIDITY:CREDIT_CONDITIONS` |
| **Why It Matters** | Credit conditions (credit spreads, lending standards, default rates) reveal the health of the credit system. Widening credit spreads signal tightening conditions; tightening lending standards signal economic distress. Credit conditions are a key input for liquidity regime classification. |
| **Update Frequency** | Daily for spreads. Weekly for lending standards. Monthly for default rates. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (Bloomberg, Moody's). Market-based but less transparent for private credit. |
| **Source Interactions** | Confirmed by: Corporate spreads (4.2), CDS (4.7). Contradicted by: Economic data (1.5, 1.7) when credit conditions diverge from fundamentals. Feeds into: Liquidity Analysis (7.7), Technical Analysis (7.6). |

### 13.4 Capital Flows

| Attribute | Detail |
|---|---|
| **Identifier** | `LIQUIDITY:CAPITAL_FLOWS` |
| **Why It Matters** | Capital flows reveal the direction and magnitude of cross-border investment. Net inflows signal confidence in a country's assets; net outflows signal distress. Capital flows drive currency movements and asset price correlations. |
| **Update Frequency** | Monthly (typically 45-60 days after month-end). Quarterly for detailed breakdowns. |
| **Trustworthiness** | **SR: 0.95** — Primary Official (Treasury, IMF). Direct government publication. However, data is often delayed and subject to revision. |
| **Source Interactions** | Confirmed by: FX spot (8.1), Trade data (1.11). Contradicted by: Currency volatility (8.4) when flows diverge from exchange rate movements. Feeds into: Liquidity Analysis (7.7), Cross-Market Relationships (5.5). |

### 13.5 Market Liquidity Measures

| Attribute | Detail |
|---|---|
| **Identifier** | `LIQUIDITY:MARKET_LIQUIDITY` |
| **Why It Matters** | Market liquidity measures (bid-ask spreads, market depth, price impact) reveal the ease of trading without moving prices. Deteriorating market liquidity can signal market stress and amplify price movements. Critical for liquidity regime classification. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (exchange data, broker data). Market-based but methodology varies across providers. |
| **Source Interactions** | Confirmed by: Treasury yields (4.1), Corporate spreads (4.2). Contradicted by: Fed Balance Sheet (1.3) when market liquidity diverges from central bank actions. Feeds into: Liquidity Analysis (7.7), Technical Analysis (7.6). |

### 13.6 Bank Reserves

| Attribute | Detail |
|---|---|
| **Identifier** | `LIQUIDITY:BANK_RESERVES` |
| **Why It Matters** | Bank reserves reveal the banking system's capacity to lend. Excess reserves indicate ample liquidity; low reserves indicate tight conditions. Reserve levels are directly affected by Fed policy and are a key input for liquidity analysis. |
| **Update Frequency** | Weekly (Federal Reserve H.3). Daily for intraday analysis. |
| **Trustworthiness** | **SR: 1.0** — Primary Official (Federal Reserve). Direct government publication. No revision. High integrity. |
| **Source Interactions** | Confirmed by: Fed Balance Sheet (1.3), Repo rates (4.9). Contradicted by: Market liquidity (13.5) when reserves diverge from trading conditions. Feeds into: Liquidity Analysis (7.7), Macro Analysis (7.5). |

### 13.7 Repo Market Data

| Attribute | Detail |
|---|---|
| **Identifier** | `LIQUIDITY:REPO` |
| **Why It Matters** | Repo market data reveals the cost and availability of short-term dollar funding. Repo rate spikes signal liquidity stress; repo rate declines signal ample liquidity. SOFR is derived from repo transactions and is the new risk-free rate. |
| **Update Frequency** | Daily (SOFR published at 8:00 AM ET). Tri-party repo: daily. GCF repo: daily. |
| **Trustworthiness** | **SR: 0.95** — Primary Official (FRB for SOFR). Transaction-based data with high integrity. However, repo markets can be volatile and subject to manipulation. |
| **Source Interactions** | Confirmed by: Fed Funds (2.1), Money Supply (13.1). Contradicted by: Bond yields (4.1) when repo stress emerges. Feeds into: Liquidity Analysis (7.7), Yield Curve (5.1). |

### 13.8 QE/QT Tracking

| Attribute | Detail |
|---|---|
| **Identifier** | `LIQUIDITY:QE_QT` |
| **Why It Matters** | QE/QT tracking reveals the central bank's asset purchase/sale program. QE injects liquidity and suppresses long-term rates; QT withdraws liquidity and can increase long-term rates. QE/QT is a primary driver of global liquidity conditions. |
| **Update Frequency** | Weekly for Fed (H.4.1 factors). Monthly for ECB. Daily for operational data. |
| **Trustworthiness** | **SR: 1.0** — Primary Official (central banks). Direct government publication. No revision. High integrity. |
| **Source Interactions** | Confirmed by: Fed Balance Sheet (1.3), Money Supply (13.1). Contradicted by: Market liquidity (13.5) when QE/QT effects diverge from market conditions. Feeds into: Liquidity Analysis (7.7), Macro Analysis (7.5). |

---

## 14. Sentiment

Sentiment sources provide insight into market psychology and investor behavior. They are critical for contrarian analysis and risk sentiment assessment.

### 14.1 AAII Investor Sentiment

| Attribute | Detail |
|---|---|
| **Identifier** | `SENTIMENT:AAII` |
| **Why It Matters** | The AAII survey measures individual investor sentiment (bullish, bearish, neutral). Individual investors are often wrong at extremes — high bullishness suggests caution; high bearishness suggests opportunity. One of the most reliable contrarian indicators. |
| **Update Frequency** | Weekly (Thursday). |
| **Trustworthiness** | **SR: 0.75** — Secondary Consensus. Survey-based data with inherent noise. However, the survey has a long track record and is widely followed. |
| **Source Interactions** | Confirmed by: Put/Call ratios (6.6), COT data (7.1–7.4). Contradicted by: Price action when sentiment diverges from market direction. Feeds into: Sentiment Analysis, Technical Analysis (7.6). |

### 14.2 NAAIM Exposure Index

| Attribute | Detail |
|---|---|
| **Identifier** | `SENTIMENT:NAAIM` |
| **Why It Matters** | The NAAIM Exposure Index measures the average equity exposure of active money managers. High exposure suggests confidence; low exposure suggests caution. The index is a leading indicator of market direction — high exposure often precedes market tops. |
| **Update Frequency** | Monthly (typically 2 weeks after month-end). |
| **Trustworthiness** | **SR: 0.75** — Secondary Consensus. Survey-based data with inherent noise. However, the survey has a long track record and is widely followed. |
| **Source Interactions** | Confirmed by: COT data (7.1–7.4), ETF flows (4.8, 10.9). Contradicted by: Price action when exposure diverges from market direction. Feeds into: Sentiment Analysis, Technical Analysis (7.6). |

### 14.3 Put/Call Ratios

| Attribute | Detail |
|---|---|
| **Identifier** | `SENTIMENT:PUT_CALL` |
| **Why It Matters** | Put/call ratios are among the most reliable contrarian indicators. Extremely high ratios suggest excessive fear (potential buying opportunity); extremely low ratios suggest excessive complacency (potential selling opportunity). |
| **Update Frequency** | Daily (end-of-day). Weekly and monthly aggregations. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified (CBOE). Direct from exchange but includes both opening and closing transactions, which can distort the signal. |
| **Source Interactions** | Confirmed by: VIX (12.1), COT data (7.1–7.4). Contradicted by: Price action when sentiment diverges from market direction. Feeds into: Sentiment Analysis, Technical Analysis (7.6). |

### 14.4 VIX

| Attribute | Detail |
|---|---|
| **Identifier** | `SENTIMENT:VIX` |
| **Why It Matters** | The VIX is the market's expectation of 30-day S&P 500 volatility. It is the primary measure of equity market fear and a key contrarian indicator. VIX spikes often mark market bottoms; VIX declines often mark market tops. |
| **Update Frequency** | Real-time during trading hours. End-of-day snapshots. |
| **Trustworthiness** | **SR: 0.95** — Primary Market (CBOE). Calculated from S&P 500 options prices. High integrity but can be affected by options market illiquidity. |
| **Source Interactions** | Confirmed by: Equity options IV (6.2), Put/Call ratios (6.6). Contradicted by: Realized volatility (12.8) when implied diverges from actual. Feeds into: Sentiment Analysis, Technical Analysis (7.6), Volatility Analysis (12.1–12.8). |

### 14.5 News Sentiment

| Attribute | Detail |
|---|---|
| **Identifier** | `SENTIMENT:NEWS` |
| **Why It Matters** | News sentiment analysis quantifies the tone of financial news coverage. Positive sentiment suggests optimism; negative sentiment suggests pessimism. News sentiment can amplify market movements and reveal narrative shifts. |
| **Update Frequency** | Real-time during trading hours. Daily aggregations. |
| **Trustworthiness** | **SR: 0.60** — Tertiary Derived. NLP-based analysis of news articles. Methodology-dependent and subject to interpretation errors. |
| **Source Interactions** | Confirmed by: Social media sentiment (14.6), Price action. Contradicted by: Fundamental data when news sentiment diverges from reality. Feeds into: Sentiment Analysis, Market Narrative (7.8). |

### 14.6 Social Media Sentiment

| Attribute | Detail |
|---|---|
| **Identifier** | `SENTIMENT:SOCIAL_MEDIA` |
| **Why It Matters** | Social media sentiment (Twitter, Reddit, etc.) reveals retail investor psychology and emerging narratives. Social media can amplify market movements and create feedback loops. Extreme sentiment on social media can signal market turning points. |
| **Update Frequency** | Real-time during trading hours. Daily aggregations. |
| **Trustworthiness** | **SR: 0.60** — Tertiary Derived. NLP-based analysis of social media posts. Highly noisy and subject to manipulation. |
| **Source Interactions** | Confirmed by: News sentiment (14.5), Price action. Contradicted by: Fundamental data when social media sentiment diverges from reality. Feeds into: Sentiment Analysis, Market Narrative (7.8). |

---

## 15. Alternative Data

Alternative data sources provide non-traditional insights into market conditions and economic activity. They are critical for gaining an informational edge and validating traditional data.

### 15.1 Satellite Imagery

| Attribute | Detail |
|---|---|
| **Identifier** | `ALTDATA:SATELLITE` |
| **Why It Matters** | Satellite imagery provides real-time visibility into economic activity — retail foot traffic, oil storage levels, agricultural production, port activity. It is a leading indicator that can validate or contradict official economic data. |
| **Update Frequency** | Daily to weekly depending on satellite schedule. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified. Commercial satellite providers with high-quality data. However, interpretation requires domain expertise and can be subjective. |
| **Source Interactions** | Confirmed by: Economic data (1.5, 1.7, 1.10). Contradicted by: Official data when satellite observations diverge from reported figures. Feeds into: Macro Analysis (7.5), Economic Activity (7.5.1). |

### 15.2 Credit Card Transaction Data

| Attribute | Detail |
|---|---|
| **Identifier** | `ALTDATA:CREDIT_CARD` |
| **Why It Matters** | Credit card transaction data provides real-time insight into consumer spending patterns. It is a high-frequency proxy for retail sales and GDP. Transaction data can reveal sector-level trends before official data is released. |
| **Update Frequency** | Daily to weekly depending on provider. |
| **Trustworthiness** | **SR: 0.85** — Secondary Verified. Aggregated from multiple payment processors. However, sample bias and methodology differences can affect accuracy. |
| **Source Interactions** | Confirmed by: Retail sales (1.10), GDP (1.5). Contradicted by: Official data when transaction data diverges from reported figures. Feeds into: Macro Analysis (7.5), Economic Activity (7.5.1). |

### 15.3 Web Scraping & App Data

| Attribute | Detail |
|---|---|
| **Identifier** | `ALTDATA:WEB_SCRAPING` |
| **Why It Matters** | Web scraping and app data (e.g., job postings, product prices, website traffic) provide real-time insight into economic activity. Job posting data is a leading indicator of employment; price tracking data is a real-time inflation measure. |
| **Update Frequency** | Daily to real-time depending on source. |
| **Trustworthiness** | **SR: 0.70** — Secondary Consensus. Data quality varies widely across sources. Subject to website changes and anti-scraping measures. |
| **Source Interactions** | Confirmed by: Economic data (1.5, 1.7, 1.10). Contradicted by: Official data when web data diverges from reported figures. Feeds into: Macro Analysis (7.5), Economic Activity (7.5.1). |

### 15.4 Mobile Location Data

| Attribute | Detail |
|---|---|
| **Identifier** | `ALTDATA:MOBILE_LOCATION` |
| **Why It Matters** | Mobile location data reveals foot traffic at retail stores, restaurants, and other venues. It is a real-time proxy for economic activity and consumer behavior. Location data can predict same-store sales and economic indicators. |
| **Update Frequency** | Daily to weekly depending on provider. |
| **Trustworthiness** | **SR: 0.70** — Secondary Consensus. Data quality varies widely. Privacy concerns and opt-in rates affect sample representativeness. |
| **Source Interactions** | Confirmed by: Retail sales (1.10), GDP (1.5). Contradicted by: Official data when location data diverges from reported figures. Feeds into: Macro Analysis (7.5), Economic Activity (7.5.1). |

### 15.5 Supply Chain Data

| Attribute | Detail |
|---|---|
| **Identifier** | `ALTDATA:SUPPLY_CHAIN` |
| **Why It Matters** | Supply chain data (shipping delays, port congestion, inventory levels) reveals the health of global trade and production. Supply chain disruptions can signal inflationary pressures and economic bottlenecks. |
| **Update Frequency** | Weekly to monthly depending on source. |
| **Trustworthiness** | **SR: 0.80** — Secondary Verified. Data from logistics companies and trade organizations. However, methodology varies and can be affected by seasonal factors. |
| **Source Interactions** | Confirmed by: Trade data (1.11), Industrial production (1.9). Contradicted by: Economic data when supply chain data diverges from reported figures. Feeds into: Macro Analysis (7.5), Global Liquidity (1.12). |

### 15.6 ESG Scores

| Attribute | Detail |
|---|---|
| **Identifier** | `ALTDATA:ESG` |
| **Why It Matters** | ESG scores (Environmental, Social, Governance) reveal a company's sustainability and ethical practices. ESG factors are increasingly important for investment decisions and can affect long-term valuation. ESG scores can reveal hidden risks and opportunities. |
| **Update Frequency** | Quarterly to annually depending on provider. |
| **Trustworthiness** | **SR: 0.75** — Secondary Consensus. Methodology varies significantly across providers. Subjective scoring can lead to inconsistencies. |
| **Source Interactions** | Confirmed by: Company financials, Regulatory filings. Contradicted by: Market performance when ESG scores diverge from financial results. Feeds into: Macro Analysis (7.5), Technical Analysis (7.6). |

### 15.7 Patent Filings

| Attribute | Detail |
|---|---|
| **Identifier** | `ALTDATA:PATENTS` |
| **Why It Matters** | Patent filings reveal innovation trends and R&D investment. High patent activity in a sector can signal future growth and competitive advantage. Patent data is a leading indicator of technological disruption. |
| **Update Frequency** | Monthly (USPTO). Quarterly for international filings. |
| **Trustworthiness** | **SR: 0.95** — Primary Official (USPTO, WIPO). Direct government publication. High integrity but lags real innovation by 18 months. |
| **Source Interactions** | Confirmed by: Company R&D spending, Sector performance. Contradicted by: Market performance when patent activity diverges from financial results. Feeds into: Macro Analysis (7.5), Technical Analysis (7.6). |

### 15.8 Employment Alternatives (Job Postings, Gig Economy)

| Attribute | Detail |
|---|---|
| **Identifier** | `ALTDATA:EMPLOYMENT_ALT` |
| **Why It Matters** | Alternative employment data (job postings on Indeed, LinkedIn, gig economy activity) provides real-time insight into labor market conditions. Job posting data is a leading indicator of employment changes and wage pressures. |
| **Update Frequency** | Daily to weekly depending on source. |
| **Trustworthiness** | **SR: 0.75** — Secondary Consensus. Data quality varies. Sample bias and platform-specific trends can affect accuracy. |
| **Source Interactions** | Confirmed by: Employment data (1.7), Jobless claims (1.7b). Contradicted by: Official employment data when alternative data diverges from reported figures. Feeds into: Macro Analysis (7.5), Economic Activity (7.5.1). |

---

### 8.3 Source Interaction Matrix

The following matrix summarizes how key sources interact across categories. An arrow (→) means "confirms" or "feeds into"; a crossed arrow (↮) means "can contradict."

```
                    ┌──────────────┬──────────────┬──────────────┬──────────────┐
                    │  Macro       │  Bond        │  Options     │  Sentiment   │
┌───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Central Banks     │ → Policy     │ → Yields     │ → IV         │ → VIX        │
│                   │ → Guidance   │ → Spreads    │ → Skew       │ → Put/Call   │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Economic Calendar │ → GDP        │ → Inflation  │ → Events     │ → AAII       │
│                   │ → Inflation  │ → CPI        │ → IV         │ → News       │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Bond Market       │ → Liquidity  │ → Yields     │ → IV         │ → VIX        │
│                   │ → Policy     │ → Spreads    │ → Skew       │ → Put/Call   │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Options           │ → Events     │ → IV         │ → VIX        │ → Sentiment  │
│                   │ → Policy     │ → Skew       │ → Skew       │ → Put/Call   │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ COT               │ → Positioning│ → ETF Flows  │ → Positioning│ → Sentiment  │
│                   │ → Flows      │ → Spreads    │ → Put/Call   │ → AAII       │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Forex             │ → Global     │ → Intl Bonds │ → FX IV      │ → Risk On/Off│
│                   │ → Policy     │ → Intl YC    │ → FX Vol     │ → VIX        │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Gold              │ → Inflation  │ → TIPS       │ → GVZ        │ → Safe Haven │
│                   │ → Real Yields│ → Real YC    │ → Gold IV    │ → VIX        │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Indices           │ → Economic   │ → Credit     │ → VIX        │ → Sentiment  │
│                   │ → Growth     │ → Spreads    │ → IV         │ → Put/Call   │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Crypto            │ → Risk       │ → Liquidity  │ → Crypto IV  │ → Speculation│
│                   │ → Sentiment  │ → Stablecoin │ → Funding    │ → News       │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Volatility        │ → Uncertainty│ → Credit     │ → VIX        │ → Fear       │
│                   │ → Regime     │ → Spreads    │ → Skew       │ → AAII       │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Liquidity         │ → Global     │ → Repo       │ → Funding    │ → Risk On/Off│
│                   │ → Policy     │ → Reserves   │ → IV         │ → VIX        │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Alternative Data  │ → Real-time  │ → Credit     │ → Events     │ → News       │
│                   │ → Economic   │ → Flows      │ → IV         │ → Social     │
└───────────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

---

### 8.4 Source Reliability Summary

The following table summarizes the trustworthiness distribution across all 116 data sources:

| SR Score | Count | Percentage | Source Categories |
|---|---|---|---|
| 1.0 | 24 | 20.7% | Central Banks (9), COT (4), Fed Operations (1), Liquidity (4), Economic Calendar (4), Macro (2) |
| 0.95 | 42 | 36.2% | Primary Official & Primary Market sources |
| 0.85 | 28 | 24.1% | Secondary Verified sources |
| 0.75 | 12 | 10.3% | Secondary Consensus sources |
| 0.70 | 4 | 3.4% | Tertiary Derived sources |
| 0.60 | 6 | 5.2% | Anecdotal / NLP-derived sources |

---

*This concludes Article VIII: Data Sources. The next article (Article IX) will define the Research Validation methodology.*
