# ResearchOS Documentation Inventory Report

**Status:** COMPLETE
**Purpose:** Full inventory of all planning documents, audit reports, architecture
reviews, completed task reports, TODO files, and historical design documents.
**Scope:** `docs/`, root `*.md`.
**Note:** No separate `researchos/docs` directory exists; all documentation lives in
`docs/` and the repository root.

---

## 1. Root `*.md` files (ResearchOS/)

| File | Current purpose | Status | Recommended location |
|------|-----------------|--------|----------------------|
| `README.md` | Repository overview | Active | Keep at root |
| `AI_CONTEXT.md` | AI/developer context helper | Active | Keep at root |
| `ARCHITECTURE_CERTIFICATION.md` | Architecture certification report | Archived | `archive/audits/` |
| `ARCHITECTURE_CLEANUP_REPORT.md` | Architecture cleanup report | Archived | `archive/audits/` |
| `ARCHITECTURE_CONTRACT_COMPLIANCE_REPORT.md` | Contract compliance audit | Archived | `archive/audits/` |
| `ARCHITECTURE_INTEGRITY_AUDIT_REPORT.md` | Integrity audit | Archived | `archive/audits/` |
| `CPP_BACKTEST_ENGINE_REPORT.md` | C++ backtest engine report | Archived | `archive/completed_tasks/` |
| `CPP_PYTHON_BRIDGE_REPORT.md` | C++/Python bridge report | Archived | `archive/completed_tasks/` |
| `CPP_RESEARCH_OPTIMIZER_REPORT.md` | C++ research optimizer report | Archived | `archive/completed_tasks/` |
| `DATA_ENGINE_REPORT.md` | Data engine report | Archived | `archive/completed_tasks/` |
| `ECONOMETRICS_ENGINE_REPORT.md` | Econometrics engine report | Archived | `archive/completed_tasks/` |
| `EXPERIMENT_QUANT_BACKEND_INTEGRATION_REPORT.md` | Experiment/quant integration report | Archived | `archive/completed_tasks/` |
| `FINAL_PRECOMMIT_ARCHITECTURE_AUDIT.md` | Pre-commit architecture audit | Archived | `archive/audits/` |
| `INSTITUTIONAL_RELEASE_AUDIT.md` | Institutional release audit | Archived | `archive/audits/` |
| `MACRO_ARCHITECTURE_CONSOLIDATION_REPORT.md` | Macro architecture consolidation | Archived | `archive/phase_reports/` |
| `MACRO_DETERMINISM_FREEZE_REPORT.md` | Macro determinism freeze | Archived | `archive/phase_reports/` |
| `MACRO_FEATURE_ENGINEERING_FREEZE_REPORT.md` | Macro feature-engineering freeze | Archived | `archive/phase_reports/` |
| `MACRO_INTELLIGENCE_REMEDIATION_REPORT.md` | Macro intelligence remediation | Archived | `archive/phase_reports/` |
| `MACRO_KNOWLEDGE_GENERATION_FREEZE_REPORT.md` | Macro knowledge-gen freeze | Archived | `archive/phase_reports/` |
| `MACRO_PHASE1_FOUNDATION_REPORT.md` | Macro Phase 1 foundation | Archived | `archive/phase_reports/` |
| `MACRO_REGIME_CLASSIFICATION_FREEZE_REPORT.md` | Macro regime classification freeze | Archived | `archive/phase_reports/` |
| `MACRO_REGIME_PHASE1_REPORT.md` | Macro regime Phase 1 | Archived | `archive/phase_reports/` |
| `MACRO_REGIME_TRANSITION_FREEZE_REPORT.md` | Macro regime transition freeze | Archived | `archive/phase_reports/` |
| `MACRO_RELATIONSHIP_ENGINE_FREEZE_REPORT.md` | Macro relationship-engine freeze | Archived | `archive/phase_reports/` |
| `MACRO_REVISION_PROVENANCE_FREEZE_REPORT.md` | Macro revision provenance freeze | Archived | `archive/phase_reports/` |
| `MACRO_STATISTICS_FREEZE_REPORT.md` | Macro statistics freeze | Archived | `archive/phase_reports/` |
| `OLLAMA_AUDIT_PROMPT.md` | Ollama audit prompt | Archived | `archive/audits/` |
| `PHASE2_HARDENING_REPORT.md` | Phase 2 hardening report | Archived | `archive/phase_reports/` |
| `PHASE4.1_CERTIFICATION_REPORT.md` | Phase 4.1 certification | Archived | `archive/phase_reports/` |
| `PHASE4_RELEASE_AUDIT.md` | Phase 4 release audit | Archived | `archive/audits/` |
| `PHASE_4_5_PERFORMANCE_INTEGRATION_REPORT.md` | Phase 4.5 perf integration | Archived | `archive/phase_reports/` |
| `QUANT_ENGINE_AUDIT_REPORT.md` | Quant engine audit | Archived | `archive/audits/` |
| `QUANT_INFRASTRUCTURE_AUDIT.md` | Quant infrastructure audit | Archived | `archive/audits/` |
| `REPOSITORY_FREEZE_REPORT.md` | Repository freeze report | Archived | `archive/phase_reports/` |
| `STRATEGY_KERNEL_REPORT.md` | Strategy kernel report | Archived | `archive/completed_tasks/` |

### Root TODO files → `archive/todo_history/`
`TODO.md`, `TODO_architecture_hardening.md`, `TODO_backend_integration.md`,
`TODO_backtesting.md`, `TODO_backtest_core.md`, `TODO_boundary_freeze.md`,
`TODO_evidence.md`, `TODO_experiments.md`, `TODO_orchestration.md`,
`TODO_phase4_5_performance_integration.md`, `TODO_phase5.md`,
`TODO_phase5_1_certified_analytical_surface.md`, `TODO_phase5_1_implementation.md`,
`TODO_phase5_3b5.md`, `TODO_phase5_3c_step3.md`, `TODO_phase6_knowledge.md`,
`TODO_probability.md`, `TODO_Q17.md`, `TODO_quant_engine.md`,
`TODO_quant_research_engine.md`, `MACRO_INTELLIGENCE_REMEDIATION_TODO.md`,
`PHASE2_HARDENING_TODO.md`, `PHASE3_5_HARDENING_TODO.md`,
`PHASE3_ECONOMETRICS_TODO.md`.

---

## 2. `docs/` files

### Active (keep in place)
| File | Purpose | Status |
|------|---------|--------|
| `ARCHITECTURE_FREEZE_V2.md` | Current architecture constitution | **Active** |
| `ARCHITECTURE_INVARIANTS.md` | Current architecture invariants | **Active** |

### Archived → `archive/architecture_history/`
`RESEARCHOS_V1_ARCHITECTURE_FREEZE.md`, `PHASE5_ARCHITECTURE_PLAN.md`,
`PHASE_5_3_EVIDENCE_LINEAGE_ARCHITECTURE.md`,
`PHASE_5_3C_LINEAGE_REPRODUCTION_ARCHITECTURE.md`, `COMPUTE_BACKEND_ARCHITECTURE.md`,
`COMPUTE_BACKEND_BASELINE.md`, `ECONOMETRICS_ENGINE.md`, `MACRO_ADAPTER_ARCHITECTURE.md`,
`MACRO_DATA_QUALITY_ARCHITECTURE.md`, `MACRO_DETERMINISM_ARCHITECTURE.md`,
`MACRO_FEATURE_ENGINEERING_ARCHITECTURE.md`, `MACRO_IMPLEMENTATION_BLUEPRINT.md`,
`MACRO_INTELLIGENCE_CONTRACTS.md`, `MACRO_KNOWLEDGE_ARCHITECTURE.md`,
`MACRO_KNOWLEDGE_GENERATION_ARCHITECTURE.md`, `MACRO_REGIME_TRANSITION_ARCHITECTURE.md`,
`MACRO_RELATIONSHIP_ENGINE_ARCHITECTURE.md`, `MACRO_REVISION_ARCHITECTURE.md`,
`MACRO_STATISTICS_ARCHITECTURE.md`, `MACRO_STORAGE_ARCHITECTURE.md`.

### Archived → `archive/completed_tasks/`
`PHASE_5_1_CERTIFIED_ANALYTICAL_SURFACE_REPORT.md`,
`PHASE_5_3A_EVIDENCE_LINEAGE_REPORT.md`,
`PHASE_5_3B1_DATASET_EVIDENCE_EMISSION_REPORT.md`,
`PHASE_5_3B2_EXPERIMENT_EVIDENCE_EMISSION_REPORT.md`,
`PHASE_5_3B3_RUN_EVIDENCE_EMISSION_REPORT.md`,
`PHASE_5_3B4_RESULT_EVIDENCE_EMISSION_REPORT.md`,
`PHASE_5_3B5_VALIDATION_EVIDENCE_EMISSION_REPORT.md`,
`PHASE_5_3C_STEP1_CONTRACT_RESOLVERS_REPORT.md`,
`PHASE_5_3C_STEP3_REPRODUCTION_ENGINE_REPORT.md`,
`RESEARCHOS_SYSTEM_VERIFICATION_REPORT.md`, `DETERMINISM_CLOSURE_REPORT.md`,
`RESEARCHOS_CORE_FREEZE_REPORT.md`.

### Archived → `archive/audits/`
`PHASE6_ARCHITECTURE_DESIGN_AUDIT.md`, `PHASE6_ADVERSARIAL_ARCHITECTURE_AUDIT.md`,
`PHASE6_RED_TEAM_ARCHITECTURE_AUDIT.md`, `MACRO_INTELLIGENCE_ARCHITECTURE_AUDIT.md`.

### Archived → `archive/deprecated_designs/`
`01_VISION.md`, `02_SCOPE.md`, `03_PRINCIPLES.md`, `04_GLOSSARY.md`,
`05_ARCHITECTURE.md`, `06_ROADMAP.md`, `07_RESEARCH_METHODOLOGY.md`,
`08_DATA_SOURCES.md`, `09_MARKET_ONTOLOGY.md`, `10_REASONING_ENGINE.md`,
`11_SCENARIO_ENGINE.md`, `12_VALIDATION_ENGINE.md`, `13_KNOWLEDGE_ENGINE.md`,
`14_COGNITIVE_ENGINE.md`, `15_SYSTEM_ARCHITECTURE.md`, `16_REASONING_FRAMEWORK.md`,
`17_OBJECT_MODEL.md`.

---

## 3. Summary counts

| Category | Count |
|----------|-------|
| Total markdown documents scanned | **~110** |
| Active (kept in place) | **4** (`README.md`, `AI_CONTEXT.md`, `ARCHITECTURE_FREEZE_V2.md`, `ARCHITECTURE_INVARIANTS.md`) |
| Archived | **~106** |
| — architecture_history | 19 |
| — phase_reports | 16 |
| — audits | 14 |
| — completed_tasks | 19 |
| — todo_history | 24 |
| — deprecated_designs | 17 |

*Counts reflect the classification performed during this cleanup.*
