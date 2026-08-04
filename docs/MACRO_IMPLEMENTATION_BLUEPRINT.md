# ResearchOS Macro Intelligence Layer — Implementation Blueprint

**Version:** 1.0.0-frozen
**Date:** 2026-08-03
**Status:** ARCHITECTURALLY FROZEN — Ready for Implementation
**Classification:** Internal — Quantitative Platform

---

## Table of Contents

1. [Package Structure](#1-package-structure)
2. [Module Responsibilities](#2-module-responsibilities)
3. [Dependency Graph](#3-dependency-graph)
4. [Implementation Order](#4-implementation-order)
5. [Test Architecture](#5-test-architecture)
6. [Migration Plan](#6-migration-plan)
7. [Build & Deployment](#7-build--deployment)
8. [Configuration Management](#8-configuration-management)

---

## 1. Package Structure

### 1.1 Top-Level Layout

```
macro_intelligence/
│
├── __init__.py                    # Package initialization, version
├── version.py                     # Semantic version string
├── exceptions.py                  # Custom exceptions
│
├── contracts/                     # [LAYER 1] Core data contracts
│   ├── __init__.py
│   ├── series.py                  # NormalizedSeries contract
│   ├── evidence.py               # EvidenceObject contract
│   ├── event.py                   # MacroEvent contract
│   ├── reaction.py               # MarketReaction contract
│   ├── knowledge.py              # KnowledgeObject contract
│   ├── enums.py                   # Shared enumerations
│   └── registry.py               # Series registry
│
├── interfaces/                    # [LAYER 1] Interface contracts
│   ├── __init__.py
│   ├── base.py                    # Base interface definitions
│   ├── query.py                   # MacroQueryInterface
│   ├── v1_bridge.py              # V1BridgeInterface
│   └── events.py                  # MacroEventBus
│
├── storage/                       # [LAYER 2] Storage layer
│   ├── __init__.py
│   ├── base.py                    # BaseStore ABC
│   ├── parquet_store.py          # Parquet implementation
│   ├── json_store.py             # JSON document store
│   ├── indexes.py                # Index management
│   └── migration.py              # Schema migration tools
│
├── adapters/                      # [LAYER 3] Source adapters
│   ├── __init__.py
│   ├── base.py                    # BaseAdapter ABC
│   ├── registry.py               # AdapterRegistry
│   ├── retry.py                   # Retry logic
│   ├── rate_limiter.py           # Rate limiting
│   ├── circuit_breaker.py        # Failure isolation
│   ├── fred.py                    # FRED adapter
│   ├── bls.py                     # BLS adapter
│   ├── treasury.py               # Treasury adapter
│   ├── fed.py                     # Federal Reserve adapter
│   ├── cftc.py                    # CFTC adapter
│   └── cboe.py                    # CBOE adapter
│
├── validation/                    # [LAYER 4] Validation
│   ├── __init__.py
│   ├── base.py                    # BaseValidator ABC
│   ├── pipeline.py               # ValidationPipeline
│   ├── schema.py                  # SchemaValidator
│   ├── range.py                   # RangeValidator
│   ├── freshness.py               # FreshnessValidator
│   ├── revision.py               # RevisionValidator
│   └── cross_source.py           # CrossSourceValidator
│
├── quality/                       # [LAYER 4] Quality engine
│   ├── __init__.py
│   ├── score.py                   # QualityScoreEngine
│   ├── metrics.py                 # QualityMetrics
│   └── dashboard.py              # Dashboard data
│
├── quarantine/                    # [LAYER 4] Quarantine
│   ├── __init__.py
│   ├── record.py                  # QuarantineRecord
│   └── manager.py                 # QuarantineManager
│
├── alerts/                        # [LAYER 5] Alerting
│   ├── __init__.py
│   ├── contract.py               # Alert schema
│   └── manager.py                # AlertManager
│
├── evidence/                      # [LAYER 5] Evidence
│   ├── __init__.py
│   ├── repository.py             # EvidenceRepository
│   └── indexing.py               # Evidence indexes
│
├── events/                        # [LAYER 5] Events
│   ├── __init__.py
│   ├── store.py                   # MacroEventStore
│   └── indexing.py               # Event indexes
│
├── analysis/                      # [LAYER 6] Analysis engines
│   ├── __init__.py
│   ├── regime.py                  # RegimeDetectionEngine
│   ├── relationships.py          # HistoricalRelationshipEngine
│   └── statistics.py             # Statistical utilities
│
├── knowledge/                     # [LAYER 7] Knowledge
│   ├── __init__.py
│   ├── pipeline.py               # KnowledgeGenerationPipeline
│   └── context.py                 # MacroContextService
│
├── bridge/                        # [LAYER 8] V1 Bridge
│   ├── __init__.py
│   └── extension.py              # V1BridgeMacroExtension
│
├── cli/                           # CLI tools
│   ├── __init__.py
│   ├── run_ingestion.py          # Ingestion runner
│   ├── check_health.py           # Health checks
│   └── query.py                  # Ad-hoc queries
│
├── config/                        # Configuration
│   ├── __init__.py
│   ├── settings.py               # Settings schema
│   ├── sources.py                # Source configurations
│   └── schedules.py              # Cron schedules
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Shared fixtures
│   ├── fixtures/                 # Test fixtures
│   │   ├── fred_responses/
│   │   ├── bls_responses/
│   │   ├── treasury_responses/
│   │   ├── cboe_responses/
│   │   └── fed_responses/
│   ├── unit/                     # Unit tests
│   │   ├── test_contracts/
│   │   ├── test_storage/
│   │   ├── test_adapters/
│   │   ├── test_validation/
│   │   ├── test_evidence/
│   │   ├── test_analysis/
│   │   └── test_knowledge/
│   ├── integration/              # Integration tests
│   │   ├── test_pipeline/
│   │   ├── test_bridge/
│   │   └── test_end_to_end/
│   └── performance/              # Performance tests
│       ├── test_storage_perf/
│       └── test_query_perf/
│
└── docs/                          # Documentation
    ├── MACRO_INTELLIGENCE_CONTRACTS.md
    ├── MACRO_STORAGE_ARCHITECTURE.md
    ├── MACRO_ADAPTER_ARCHITECTURE.md
    ├── MACRO_DATA_QUALITY_ARCHITECTURE.md
    └── MACRO_KNOWLEDGE_ARCHITECTURE.md
```

### 1.2 File Count Estimates

| Directory | Files | Lines (est.) |
|-----------|-------|--------------|
| `contracts/` | 7 | ~800 |
| `interfaces/` | 4 | ~400 |
| `storage/` | 5 | ~1200 |
| `adapters/` | 10 | ~1500 |
| `validation/` | 7 | ~1000 |
| `quality/` | 3 | ~400 |
| `quarantine/` | 2 | ~300 |
| `alerts/` | 2 | ~250 |
| `evidence/` | 2 | ~400 |
| `events/` | 2 | ~400 |
| `analysis/` | 3 | ~800 |
| `knowledge/` | 2 | ~600 |
| `bridge/` | 1 | ~300 |
| `cli/` | 3 | ~200 |
| `config/` | 3 | ~300 |
| `tests/` | ~50 | ~5000 |
| **TOTAL** | **~106** | **~13,000** |

---

## 2. Module Responsibilities

### 2.1 Contracts Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `contracts/series.py` | NormalizedSeries definition | `NormalizedSeries`, `FrequencyEnum`, `SeriesType` |
| `contracts/evidence.py` | EvidenceObject definition | `EvidenceObject`, `RevisionRef`, `ProvenanceChain` |
| `contracts/event.py` | MacroEvent definition | `MacroEvent`, `EventTypeEnum`, `ImportanceLevel` |
| `contracts/reaction.py` | MarketReaction definition | `MarketReaction`, `ReactionMetrics` |
| `contracts/knowledge.py` | KnowledgeObject definition | `KnowledgeObject`, `Pattern`, `StatisticalAnalysis` |
| `contracts/enums.py` | Shared enumerations | `ErrorType`, `HealthStatus`, `Severity` |
| `contracts/registry.py` | Series registry | `SUPPORTED_SERIES`, `SERIES_RANGES` |

### 2.2 Interfaces Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `interfaces/base.py` | Abstract interface definitions | `BaseQueryInterface`, `BaseBridgeInterface` |
| `interfaces/query.py` | Macro query interface | `MacroQueryInterface` |
| `interfaces/v1_bridge.py` | V1 bridge interface | `V1BridgeInterface`, `BRIDGE_VERSION` |
| `interfaces/events.py` | Event bus interface | `MacroEventBus` |

### 2.3 Storage Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `storage/base.py` | Abstract storage interface | `BaseStore`, `StorageConfig` |
| `storage/parquet_store.py` | Parquet implementation | `ParquetStore`, `ParquetConfig` |
| `storage/json_store.py` | JSON document store | `JsonStore`, `JsonConfig` |
| `storage/indexes.py` | Index management | `IndexManager`, `IndexConfig` |
| `storage/migration.py` | Schema migrations | `SchemaMigration`, `MigrationTool` |

### 2.4 Adapters Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `adapters/base.py` | Abstract adapter interface | `BaseAdapter`, `RawRecord`, `AdapterError` |
| `adapters/registry.py` | Adapter registry | `AdapterRegistry` |
| `adapters/retry.py` | Retry logic | `RetryPolicy`, `RetryExecutor` |
| `adapters/rate_limiter.py` | Rate limiting | `RateLimiter`, `TokenBucket` |
| `adapters/circuit_breaker.py` | Failure isolation | `CircuitBreaker`, `CircuitState` |
| `adapters/fred.py` | FRED API adapter | `FREDAdapter` |
| `adapters/bls.py` | BLS API adapter | `BLSAdapter` |
| `adapters/treasury.py` | Treasury API adapter | `TreasuryAdapter` |
| `adapters/fed.py` | Fed communications adapter | `FederalReserveAdapter` |
| `adapters/cftc.py` | CFTC adapter | `CFTCAdapter` |
| `adapters/cboe.py` | CBOE adapter | `CBOEAdapter` |

### 2.5 Validation Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `validation/base.py` | Abstract validator interface | `BaseValidator`, `StageResult` |
| `validation/pipeline.py` | Validation pipeline | `ValidationPipeline` |
| `validation/schema.py` | Schema validation | `SchemaValidator` (10 rules) |
| `validation/range.py` | Range validation | `RangeValidator` (19 rules) |
| `validation/freshness.py` | Freshness validation | `FreshnessValidator` (7 rules) |
| `validation/revision.py` | Revision validation | `RevisionValidator` (5 rules) |
| `validation/cross_source.py` | Cross-source validation | `CrossSourceValidator` (4 rules) |

### 2.6 Quality Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `quality/score.py` | Quality score computation | `QualityScoreEngine`, `QualityScores` |
| `quality/metrics.py` | Quality metrics aggregation | `QualityMetrics`, `QualityDashboard` |
| `quality/dashboard.py` | Dashboard data | `DashboardData` |

### 2.7 Quarantine Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `quarantine/record.py` | Quarantine record schema | `QuarantineRecord`, `QuarantineStatus` |
| `quarantine/manager.py` | Quarantine workflow | `QuarantineManager` |

### 2.8 Alerts Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `alerts/contract.py` | Alert schema | `Alert`, `AlertType`, `Severity` |
| `alerts/manager.py` | Alert management | `AlertManager` |

### 2.9 Evidence Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `evidence/repository.py` | Evidence storage | `EvidenceRepository` |
| `evidence/indexing.py` | Evidence indexes | `EvidenceIndexManager` |

### 2.10 Events Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `events/store.py` | Event storage | `MacroEventStore` |
| `events/indexing.py` | Event indexes | `EventIndexManager` |

### 2.11 Analysis Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `analysis/regime.py` | Regime detection | `RegimeDetectionEngine`, `RegimeClassification` |
| `analysis/relationships.py` | Historical relationships | `HistoricalRelationshipEngine` |
| `analysis/statistics.py` | Statistical utilities | `StatisticalUtils` |

### 2.12 Knowledge Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `knowledge/pipeline.py` | Knowledge generation | `KnowledgeGenerationPipeline` |
| `knowledge/context.py` | Macro context | `MacroContextService`, `MacroContext` |

### 2.13 Bridge Layer

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `bridge/extension.py` | V1 Bridge extension | `V1BridgeMacroExtension` |

---

## 3. Dependency Graph

### 3.1 Module Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                         BRIDGE LAYER                             │
│                          bridge/                                 │
│                         extension.py                             │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE LAYER                           │
│                    knowledge/pipeline.py                         │
│                    knowledge/context.py                          │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                        ANALYSIS LAYER                            │
│                  analysis/regime.py                              │
│                analysis/relationships.py                         │
│                   analysis/statistics.py                         │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                        EVENTS LAYER                              │
│                      events/store.py                             │
│                    events/indexing.py                            │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                      EVIDENCE LAYER                              │
│                  evidence/repository.py                          │
│                    evidence/indexing.py                          │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                        ALERTS LAYER                              │
│                       alerts/manager.py                          │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                     QUARANTINE LAYER                             │
│                    quarantine/manager.py                         │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                       QUALITY LAYER                              │
│                       quality/score.py                           │
│                    quality/metrics.py                            │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATION LAYER                              │
│                  validation/pipeline.py                          │
│                validation/schema.py                              │
│                 validation/range.py                              │
│               validation/freshness.py                            │
│              validation/revision.py                              │
│           validation/cross_source.py                             │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                       ADAPTERS LAYER                             │
│                   adapters/fred.py                               │
│                    adapters/bls.py                               │
│                 adapters/treasury.py                             │
│                 adapters/fed.py                                  │
│                   adapters/cftc.py                               │
│                   adapters/cboe.py                               │
│                   adapters/base.py                               │
│                 adapters/registry.py                             │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                               │
│                  storage/parquet_store.py                        │
│                    storage/json_store.py                         │
│                   storage/indexes.py                             │
│                    storage/base.py                               │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                     INTERFACES LAYER                             │
│                interfaces/query.py                               │
│              interfaces/v1_bridge.py                             │
│                 interfaces/events.py                             │
│                   interfaces/base.py                             │
└─────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ depends on
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                      CONTRACTS LAYER                             │
│                  contracts/series.py                             │
│                 contracts/evidence.py                            │
│                   contracts/event.py                             │
│                 contracts/reaction.py                            │
│                 contracts/knowledge.py                           │
│                   contracts/enums.py                             │
│                 contracts/registry.py                            │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Dependency Matrix

| Module | Depends On | Forbidden From |
|--------|-----------|----------------|
| `contracts/*` | Python stdlib, pydantic | Any other MIL module |
| `interfaces/*` | `contracts/*` | V1 Core, any MIL implementation |
| `storage/*` | `contracts/*`, `interfaces/*` | V1 Core, adapters |
| `adapters/*` | `contracts/*`, `storage/*` | V1 Core, validation |
| `validation/*` | `contracts/*`, `storage/*` | V1 Core, adapters |
| `quality/*` | `contracts/*`, `validation/*` | V1 Core |
| `quarantine/*` | `contracts/*`, `storage/*` | V1 Core |
| `alerts/*` | `contracts/*`, `storage/*` | V1 Core |
| `evidence/*` | `contracts/*`, `storage/*`, `validation/*` | V1 Core |
| `events/*` | `contracts/*`, `storage/*` | V1 Core |
| `analysis/*` | `contracts/*`, `evidence/*`, `events/*` | V1 Core |
| `knowledge/*` | `contracts/*`, `analysis/*`, `evidence/*` | V1 Core |
| `bridge/*` | `interfaces/*`, `knowledge/*` | V1 Core implementation |

### 3.3 Circular Dependency Prevention

```
# Verified: No circular dependencies exist
# All dependencies flow bottom-up:

contracts → interfaces → storage → adapters
                                ↓
                         validation → quality
                                ↓
                         evidence ← alerts
                                ↓
                         events → analysis → knowledge → bridge
```

---

## 4. Implementation Order

### Phase 1: Foundation (Week 1)

**Goal:** Establish core contracts and storage layer

| Day | Module | Files | Status |
|-----|--------|-------|--------|
| 1 | `contracts/enums.py` | 1 | ⏳ |
| 1 | `contracts/series.py` | 1 | ⏳ |
| 2 | `contracts/evidence.py` | 1 | ⏳ |
| 2 | `contracts/event.py` | 1 | ⏳ |
| 3 | `contracts/reaction.py` | 1 | ⏳ |
| 3 | `contracts/knowledge.py` | 1 | ⏳ |
| 3 | `contracts/registry.py` | 1 | ⏳ |
| 4 | `interfaces/base.py` | 1 | ⏳ |
| 4 | `interfaces/query.py` | 1 | ⏳ |
| 5 | `interfaces/v1_bridge.py` | 1 | ⏳ |
| 5 | `interfaces/events.py` | 1 | ⏳ |
| 6 | `storage/base.py` | 1 | ⏳ |
| 6 | `storage/parquet_store.py` | 1 | ⏳ |
| 7 | `storage/json_store.py` | 1 | ⏳ |
| 7 | `storage/indexes.py` | 1 | ⏳ |

**Deliverables:**
- All contract dataclasses with serialization
- Interface definitions (ABCs)
- Parquet and JSON storage implementations
- Index management

### Phase 2: Adapters (Week 2)

**Goal:** Implement source adapters with retry/rate limiting

| Day | Module | Files | Status |
|-----|--------|-------|--------|
| 1 | `adapters/base.py` | 1 | ⏳ |
| 1 | `adapters/retry.py` | 1 | ⏳ |
| 2 | `adapters/rate_limiter.py` | 1 | ⏳ |
| 2 | `adapters/circuit_breaker.py` | 1 | ⏳ |
| 2 | `adapters/registry.py` | 1 | ⏳ |
| 3 | `adapters/fred.py` | 1 | ⏳ |
| 4 | `adapters/bls.py` | 1 | ⏳ |
| 4 | `adapters/treasury.py` | 1 | ⏳ |
| 5 | `adapters/fed.py` | 1 | ⏳ |
| 5 | `adapters/cftc.py` | 1 | ⏳ |
| 6 | `adapters/cboe.py` | 1 | ⏳ |

**Deliverables:**
- Base adapter with common functionality
- 6 production adapters
- Retry, rate limiting, circuit breaker

### Phase 3: Validation (Week 3)

**Goal:** Implement validation pipeline and quality engine

| Day | Module | Files | Status |
|-----|--------|-------|--------|
| 1 | `validation/base.py` | 1 | ⏳ |
| 1 | `validation/pipeline.py` | 1 | ⏳ |
| 2 | `validation/schema.py` | 1 | ⏳ |
| 2 | `validation/range.py` | 1 | ⏳ |
| 3 | `validation/freshness.py` | 1 | ⏳ |
| 3 | `validation/revision.py` | 1 | ⏳ |
| 4 | `validation/cross_source.py` | 1 | ⏳ |
| 5 | `quality/score.py` | 1 | ⏳ |
| 5 | `quality/metrics.py` | 1 | ⏳ |
| 6 | `quarantine/record.py` | 1 | ⏳ |
| 6 | `quarantine/manager.py` | 1 | ⏳ |

**Deliverables:**
- 5-stage validation pipeline
- Quality score engine
- Quarantine system

### Phase 4: Evidence & Events (Week 4)

**Goal:** Implement evidence repository and event store

| Day | Module | Files | Status |
|-----|--------|-------|--------|
| 1 | `alerts/contract.py` | 1 | ⏳ |
| 1 | `alerts/manager.py` | 1 | ⏳ |
| 2 | `evidence/repository.py` | 1 | ⏳ |
| 2 | `evidence/indexing.py` | 1 | ⏳ |
| 3 | `events/store.py` | 1 | ⏳ |
| 3 | `events/indexing.py` | 1 | ⏳ |
| 4-5 | Integration testing | - | ⏳ |

**Deliverables:**
- Immutable evidence repository
- Event store with search
- Alert system

### Phase 5: Analysis (Week 5)

**Goal:** Implement analysis engines

| Day | Module | Files | Status |
|-----|--------|-------|--------|
| 1 | `analysis/statistics.py` | 1 | ⏳ |
| 1-2 | `analysis/regime.py` | 1 | ⏳ |
| 2-3 | `analysis/relationships.py` | 1 | ⏳ |
| 4 | `knowledge/pipeline.py` | 1 | ⏳ |
| 4-5 | `knowledge/context.py` | 1 | ⏳ |

**Deliverables:**
- Regime detection engine
- Historical relationship engine
- Knowledge generation pipeline
- Macro context service

### Phase 6: Bridge & Integration (Week 6)

**Goal:** Complete V1 Bridge and integration

| Day | Module | Files | Status |
|-----|--------|-------|--------|
| 1 | `bridge/extension.py` | 1 | ⏳ |
| 1 | `config/settings.py` | 1 | ⏳ |
| 1 | `config/sources.py` | 1 | ⏳ |
| 2 | `cli/run_ingestion.py` | 1 | ⏳ |
| 2 | `cli/check_health.py` | 1 | ⏳ |
| 2 | `cli/query.py` | 1 | ⏳ |
| 3-5 | End-to-end testing | - | ⏳ |
| 6 | Documentation | - | ⏳ |

**Deliverables:**
- V1 Bridge extension
- CLI tools
- Complete documentation

---

## 5. Test Architecture

### 5.1 Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── fixtures/
│   ├── __init__.py
│   ├── fred_responses/
│   │   ├── gdp_observations.json
│   │   ├── cpi_observations.json
│   │   └── error_responses.json
│   ├── bls_responses/
│   │   ├── cpi_observations.json
│   │   └── unemployment_observations.json
│   ├── treasury_responses/
│   │   ├── yield_curve.json
│   │   └── latest_quotes.json
│   ├── cboe_responses/
│   │   ├── vix_current.json
│   │   └── vix_history.json
│   └── fed_responses/
│       ├── fomc_feed.xml
│       └── speeches_feed.xml
├── unit/
│   ├── __init__.py
│   ├── test_contracts/
│   │   ├── __init__.py
│   │   ├── test_series.py
│   │   ├── test_evidence.py
│   │   ├── test_event.py
│   │   ├── test_reaction.py
│   │   └── test_knowledge.py
│   ├── test_storage/
│   │   ├── __init__.py
│   │   ├── test_parquet_store.py
│   │   ├── test_json_store.py
│   │   └── test_indexes.py
│   ├── test_adapters/
│   │   ├── __init__.py
│   │   ├── test_base.py
│   │   ├── test_fred.py
│   │   ├── test_bls.py
│   │   ├── test_treasury.py
│   │   ├── test_fed.py
│   │   ├── test_cftc.py
│   │   └── test_cboe.py
│   ├── test_validation/
│   │   ├── __init__.py
│   │   ├── test_pipeline.py
│   │   ├── test_schema.py
│   │   ├── test_range.py
│   │   ├── test_freshness.py
│   │   ├── test_revision.py
│   │   └── test_cross_source.py
│   ├── test_quality/
│   │   ├── __init__.py
│   │   └── test_score.py
│   ├── test_evidence/
│   │   ├── __init__.py
│   │   └── test_repository.py
│   ├── test_events/
│   │   ├── __init__.py
│   │   └── test_store.py
│   ├── test_analysis/
│   │   ├── __init__.py
│   │   ├── test_regime.py
│   │   └── test_relationships.py
│   └── test_knowledge/
│       ├── __init__.py
│       └── test_pipeline.py
├── integration/
│   ├── __init__.py
│   ├── test_pipeline/
│   │   ├── __init__.py
│   │   ├── test_full_pipeline.py
│   │   └── test_revision_chain.py
│   ├── test_bridge/
│   │   ├── __init__.py
│   │   └── test_v1_bridge.py
│   └── test_end_to_end/
│       ├── __init__.py
│       └── test_data_flow.py
└── performance/
    ├── __init__.py
    ├── test_storage_perf/
    │   ├── __init__.py
    │   └── test_write_perf.py
    └── test_query_perf/
        ├── __init__.py
        └── test_read_perf.py
```

### 5.2 Test Coverage Targets

| Module | Unit Test Target | Integration Test Target |
|--------|-----------------|------------------------|
| `contracts/*` | 100% | N/A |
| `interfaces/*` | 100% | N/A |
| `storage/*` | 90% | 80% |
| `adapters/*` | 85% | 70% |
| `validation/*` | 95% | 80% |
| `quality/*` | 90% | 70% |
| `evidence/*` | 90% | 80% |
| `events/*` | 90% | 80% |
| `analysis/*` | 85% | 70% |
| `knowledge/*` | 85% | 70% |
| `bridge/*` | 90% | 80% |

### 5.3 Key Test Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path
from macro_intelligence.contracts.series import NormalizedSeries, FrequencyEnum
from macro_intelligence.contracts.evidence import EvidenceObject
from macro_intelligence.contracts.event import MacroEvent, EventTypeEnum

@pytest.fixture
def sample_series():
    """Sample NormalizedSeries for testing."""
    return NormalizedSeries(
        series_id="SER_20260803_001",
        source="fred",
        timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        observation_period=date(2026, 8, 1),
        release_time=datetime(2026, 8, 12, 8, 30, tzinfo=UTC),
        available_time=datetime(2026, 8, 12, 8, 35, tzinfo=UTC),
        value=4.25,
        unit="percent",
        frequency=FrequencyEnum.DAILY,
        revision_id=None,
        quality_score=0.95,
        metadata={},
    )

@pytest.fixture
def sample_evidence(sample_series):
    """Sample EvidenceObject for testing."""
    return EvidenceObject(
        evidence_id="EV_20260803_001",
        source="fred",
        source_quality_score=0.95,
        series_reference=sample_series.series_id,
        observation_time=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
        release_time=datetime(2026, 8, 12, 8, 30, tzinfo=UTC),
        available_time=datetime(2026, 8, 12, 8, 35, tzinfo=UTC),
        value=4.25,
        forecast=4.20,
        previous=4.30,
        revision=None,
        confidence=0.95,
        quality_score=0.95,
        provenance=ProvenanceChain(
            original_source="FRED",
            ingestion_pipeline=["adapter", "validator"],
            transformation_log=[],
            verification_checks=[],
        ),
    )

@pytest.fixture
def sample_event():
    """Sample MacroEvent for testing."""
    return MacroEvent(
        event_id="EVNT_20260812_001",
        event_type=EventTypeEnum.DATA_RELEASE,
        timestamp=datetime(2026, 8, 12, 8, 30, tzinfo=UTC),
        source="BLS",
        description="CPI release",
        classification="DATA_CPI",
        importance=ImportanceLevel.HIGH,
        related_series=["CPI_YOY", "CPI_CORE_YOY"],
        market_relevance=MarketRelevance(
            volatility_impact=8.0,
            liquidity_impact=-2.0,
            affected_instruments=["TLT", "SPY"],
            correlation_score=0.72,
            historical_similarity="20220310_001",
        ),
    )

@pytest.fixture
def test_storage(tmp_path):
    """Create temporary storage for tests."""
    storage_path = tmp_path / "macro_storage"
    storage_path.mkdir()
    return storage_path
```

### 5.4 Test Commands

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest --cov=macro_intelligence --cov-report=html tests/

# Run performance tests
pytest tests/performance/ -v --benchmark-only

# Run specific test
pytest tests/unit/test_validation/test_schema.py -v
```

---

## 6. Migration Plan

### 6.1 Schema Migration Strategy

```python
# storage/migration.py
class SchemaMigration:
    """
    Handles schema migrations for storage layer.
    
    Migration versions:
    - v1: Initial schema (current)
    - v2: Future schema changes
    """
    
    CURRENT_VERSION = "v1"
    MIGRATIONS = {
        "v1": {
            "created": "2026-08-03",
            "description": "Initial schema",
            "tables": ["series", "evidence", "events"],
        }
    }
    
    def check_migration_status(self, storage_path: Path) -> MigrationStatus:
        """Check current migration status."""
        ...
    
    def apply_migration(self, from_version: str, to_version: str) -> None:
        """Apply migration from version to version."""
        ...
    
    def validate_schema(self, storage_path: Path) -> bool:
        """Validate storage schema is correct."""
        ...
```

### 6.2 Data Migration Procedures

| Migration | Action | Risk | Rollback |
|-----------|--------|------|----------|
| v1 → v2 | Schema change | Medium | Backup before migration |
| Storage format change | Export → Transform → Import | High | Keep old format |
| Index rebuild | Rebuild all indexes | Low | indexes are derivable |

### 6.3 Backward Compatibility

```python
# All contract versions are backward-compatible
# New fields have default values
# Removed fields are logged but not deleted

class BackwardCompatibility:
    """Ensures backward compatibility across versions."""
    
    def validate_compatibility(self, old_version: str, new_version: str) -> bool:
        """Validate compatibility between versions."""
        # Check that all old fields exist in new version
        # Check that new fields have defaults
        # Check serialization/deserialization round-trip
        ...
```

---

## 7. Build & Deployment

### 7.1 Build Configuration

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "macro-intelligence"
version = "1.0.0"
description = "ResearchOS Macro Intelligence Layer"
requires-python = ">=3.11"

dependencies = [
    "pyarrow>=14.0.0",
    "pandas>=2.0.0",
    "pydantic>=2.0.0",
    "requests>=2.31.0",
    "apScheduler>=3.10.0",
    "loguru>=0.7.0",
    "numpy>=1.24.0",
    "scipy>=1.11.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-benchmark>=4.0.0",
    "hypothesis>=6.88.0",
    "black>=23.7.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["macro_intelligence*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
```

### 7.2 Deployment Steps

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Run tests
pytest --cov=macro_intelligence tests/

# 3. Build package
python -m build

# 4. Deploy to internal registry
twine upload dist/*
```

### 7.3 Environment Configuration

```python
# config/settings.py
from pydantic import BaseModel
from typing import Optional

class APICredentials(BaseModel):
    fred_api_key: str = ""
    bls_api_key: str = ""
    cboe_api_key: str = ""

class StorageConfig(BaseModel):
    parquet_root: str = ".agnes/data/macro/parquet"
    json_root: str = ".agnes/data/macro/json"
    compression: str = "snappy"

class SourceConfig(BaseModel):
    enabled: bool = True
    polling_interval_minutes: int = 1440
    max_retries: int = 3
    timeout_seconds: int = 30

class MILConfig(BaseModel):
    api_credentials: APICredentials = APICredentials()
    storage: StorageConfig = StorageConfig()
    sources: dict[str, SourceConfig] = {}
```

---

## 8. Configuration Management

### 8.1 Configuration Hierarchy

```
Environment Variables (highest priority)
    ↓
config/settings.yaml
    ↓
config/sources.yaml
    ↓
Default values (lowest priority)
```

### 8.2 Configuration Files

```yaml
# config/settings.yaml
storage:
  parquet_root: ".agnes/data/macro/parquet"
  json_root: ".agnes/data/macro/json"
  compression: "snappy"

validation:
  quarantine_enabled: true
  stale_threshold_days: 7
  reconciliation_tolerance_pct: 0.5

alerts:
  warning_threshold: 0.7
  critical_threshold: 0.3
  outage_threshold_failures: 5

quality:
  weights:
    source_reliability: 0.3
    completeness: 0.2
    freshness: 0.2
    anomaly: 0.3
```

```yaml
# config/sources.yaml
sources:
  fred:
    enabled: true
    api_key: "${FRED_API_KEY}"
    polling_interval_minutes: 1440
    max_retries: 3
    timeout_seconds: 30
  
  bls:
    enabled: true
    api_key: "${BLS_API_KEY}"
    polling_interval_minutes: 1440
    max_retries: 3
    timeout_seconds: 30
  
  treasury:
    enabled: true
    polling_interval_minutes: 1440
  
  cboe:
    enabled: true
    api_key: "${CBOE_API_KEY}"
    polling_interval_minutes: 1440
```

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Create contracts layer (7 files)
- [ ] Create interfaces layer (4 files)
- [ ] Create storage layer (5 files)
- [ ] Write unit tests for contracts
- [ ] Write unit tests for storage

### Phase 2: Adapters
- [ ] Create base adapter (4 files)
- [ ] Implement FRED adapter
- [ ] Implement BLS adapter
- [ ] Implement Treasury adapter
- [ ] Implement Fed adapter
- [ ] Implement CFTC adapter
- [ ] Implement CBOE adapter
- [ ] Write adapter tests

### Phase 3: Validation
- [ ] Create validation pipeline
- [ ] Implement 5 validators
- [ ] Create quality score engine
- [ ] Create quarantine system
- [ ] Write validation tests

### Phase 4: Evidence & Events
- [ ] Create evidence repository
- [ ] Create event store
- [ ] Create alert system
- [ ] Write repository tests
- [ ] Write store tests

### Phase 5: Analysis
- [ ] Create regime detection engine
- [ ] Create relationship engine
- [ ] Create knowledge pipeline
- [ ] Create context service
- [ ] Write analysis tests

### Phase 6: Bridge & Integration
- [ ] Create V1 bridge extension
- [ ] Create CLI tools
- [ ] Create configuration
- [ ] Write integration tests
- [ ] Write end-to-end tests
- [ ] Complete documentation

---

## Final Declaration

---

**Macro Intelligence Layer Implementation Blueprint is architecturally frozen and ready for execution.**

All implementation phases are defined with:
- Complete package structure
- Module responsibilities
- Dependency graph (no cycles)
- Week-by-week implementation order
- Test architecture with coverage targets
- Migration and deployment procedures

**Next Step:** Begin Phase 1 implementation — create contracts layer.

---

*Document Version: 1.0.0-frozen*
*Last Updated: 2026-08-03*
*Classification: Internal — Quantitative Platform Architecture*
