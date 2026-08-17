# PHASE 4 — Capability Layers Roadmap

**Date:** 2026-08-16  
**Status:** Planning and Dependency Analysis

---

## Dependency Analysis & Sequencing

### Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                    Evidence Repository (exists)             │
│         (provides: emit_dataset, emit_run, emit_result)      │
└──────────────┬────────────────────────┬──────────────────────┘
               │                        │
        ┌──────▼──────┐         ┌──────▼──────┐
        │  4.1: Feature│       │  4.2: Model  │
        │  Registry    │       │  Registry    │
        │  (features   │       │  (trained    │
        │  versioning) │       │  models)     │
        └──────┬──────┘       └──────┬──────┘
               │                      │
               └──────────┬───────────┘
                          │
                   ┌──────▼──────────┐
                   │  4.3: Experiment│
                   │  Comparison     │
                   │  (ranks results)│
                   └──────┬──────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐     ┌─────▼────┐
   │4.5: Risk│      │4.4: KG  │     │4.6:      │
   │Analytics│      │(evidence│     │Reports   │
   │(tail    │      │graph)   │     │Generator │
   │risk)    │      │         │     │          │
   └────┬────┘      └────┬────┘     └─────┬────┘
        │                │               │
        └────────┬───────┴───────────────┘
                 │
          ┌──────▼────────┐
          │  4.7: Search  │
          │  (KG + Evidence)
          └──────┬────────┘
                 │
          ┌──────▼──────────┐
          │  4.8: Viz/      │
          │  Dashboard      │
          └──────┬──────────┘
                 │
        ┌────────▼─────────┐
        │  4.9: Archive/   │
        │  Lifecycle (can  │
        │  run anytime)    │
        └──────────────────┘
```

---

## Critical Path Analysis

### **TIER 1: Foundation Layers** (must complete first)

| Item | Title | Dependencies | Criticality | Effort | Timeline |
|------|-------|--------------|-------------|--------|----------|
| 4.1 | Feature Registry | Evidence Repo (exists) | HIGH | MEDIUM | 2-3 days |
| 4.2 | Model Registry | Evidence Repo (exists) | HIGH | MEDIUM | 2-3 days |

**Rationale:** Both are data infrastructure layers that enable everything else. No dependencies on each other, can run in parallel.

### **TIER 2: Analysis & Aggregation Layers** (depends on Tier 1)

| Item | Title | Dependencies | Criticality | Effort | Timeline |
|------|-------|--------------|-------------|--------|----------|
| 4.3 | Experiment Comparison | ExperimentResult (exists) | HIGH | LOW | 1-2 days |
| 4.5 | Risk Analytics | Portfolio module (exists) | HIGH | MEDIUM | 2-3 days |
| 4.4 | Knowledge Graph | Knowledge objects (exist) | MEDIUM | MEDIUM | 2-3 days |

**Rationale:** These consume existing objects and produce ranked/aggregated views. Can run in parallel once Tier 1 is done.

### **TIER 3: Output/Consumption Layers** (depends on Tier 1-2)

| Item | Title | Dependencies | Criticality | Effort | Timeline |
|------|-------|--------------|-------------|--------|----------|
| 4.6 | Reports Generator | Evidence Repo, Experiment Comparison | HIGH | MEDIUM | 1-2 days |
| 4.7 | Search Interface | Knowledge Graph, Evidence Repo | MEDIUM | MEDIUM | 2-3 days |

**Rationale:** Consumes data from Tier 1-2 to produce user-facing outputs.

### **TIER 4: UI/UX Layers** (depends on Tier 2-3)

| Item | Title | Dependencies | Criticality | Effort | Timeline |
|------|-------|--------------|-------------|--------|----------|
| 4.8 | Dashboard/Visualization | All of Tier 1-3 | MEDIUM | HIGH | 3-4 days |

**Rationale:** Depends on all data/aggregation/output layers. Can show current status, evidence chains, risk profiles.

### **TIER 5: Operational Layers** (independent, can run anytime)

| Item | Title | Dependencies | Criticality | Effort | Timeline |
|------|-------|--------------|-------------|--------|----------|
| 4.9 | Archive/Lifecycle | Schema definitions only | LOW | LOW | 1 day |

**Rationale:** Purely operational; can be implemented once before or after any tier.

---

## Recommended Execution Order

```
WEEK 1 (Tier 1 Foundation)
├─ 4.1: Feature Registry ──┐
└─ 4.2: Model Registry ────┤ (parallel, 4-5 days)
                            │
WEEK 2 (Tier 2 Analysis)    │
├─ 4.3: Experiment Comparison (depends on Tier 1) ──┐
├─ 4.5: Risk Analytics ────────────────────────────┤ (parallel, 3-4 days)
└─ 4.4: Knowledge Graph ───────────────────────────┘
                                                    │
WEEK 3 (Tier 3 Output)                              │
├─ 4.6: Reports Generator ────────────────────────┐ │
└─ 4.7: Search Interface ─────────────────────────┤─┘ (parallel, 2-3 days)
                                                    │
WEEK 4 (Tier 4 UI)                                  │
└─ 4.8: Dashboard ────────────────────────────────┤ (3-4 days)
                                                    │
TIER 5 (Operational, can insert anywhere)           │
└─ 4.9: Archive/Lifecycle ─────────────────────────┘ (1 day, anytime)

Total Estimated Duration: 3-4 weeks (sequential tiers)
With parallelization: 2-2.5 weeks (parallel within tiers)
```

---

## Scope Decision Needed

Phase 4 is substantial (9 major components, 20-25 days of effort total). 

**Options:**

### Option A: Full Phase 4 (All 9 Items)
- Estimated time: 20-25 days (3.5-4 weeks)
- Delivers: Complete institutional-grade OS infrastructure
- Ideal for: Long-term capability building

### Option B: Phased Approach (Recommended)
- **Phase 4a (Weeks 1-2):** Tiers 1-2 (4.1, 4.2, 4.3, 4.5, 4.4)
  - Deliverable: Complete data infrastructure + comparison/risk analysis
  - Enables: Reproducible experiments, quantitative experiment ranking
  - Effort: 10-12 days
  
- **Phase 4b (Week 3):** Tiers 3-4 (4.6, 4.7, 4.8)
  - Deliverable: Reports + search + dashboard
  - Enables: User-facing research interface
  - Effort: 8-10 days
  
- **Phase 5:** Tier 5 (4.9)
  - Deliverable: Lifecycle management
  - Enables: Long-term system sustainability
  - Effort: 1-2 days

### Option C: MVP (Tiers 1-2 only)
- **Phase 4 MVP:** 4.1, 4.2, 4.3 (Feature Registry, Model Registry, Experiment Comparison)
- Estimated time: 5-7 days
- Deliverable: Foundation layers sufficient for Phase 2 BTC/ETH research reinvocation
- Next phase: Extend with 4.4-4.9

---

## Pre-Implementation Checklist

- [ ] Confirm scope choice (Option A / B / C)
- [ ] Review existing codebase for scaffolding:
  - [ ] `researchos/quant_engine/models/registry.py` (already exists, needs extension)
  - [ ] `macro_intelligence/knowledge/` objects (exist, need graph structure)
  - [ ] `researchos/quant_engine/portfolio/analytics.py` (exists, needs risk layer)
  - [ ] `static/index.html` and `build_dashboard.py` (exist, need integration)
- [ ] Confirm test isolation standards from Phase 3
- [ ] Plan coverage targets for Phase 4 modules (must maintain >70%)

---

## Sign-Off

**Awaiting scope decision before proceeding with implementation.**

Recommend: **Option B (Phased Approach)** 
- 4a: Weeks 1-2 → Data infrastructure (highest ROI, enables BTC/ETH research restart)
- 4b: Week 3 → Output layers (user-facing, high visibility)
- 5: Later → Lifecycle (operational, lower urgency)

