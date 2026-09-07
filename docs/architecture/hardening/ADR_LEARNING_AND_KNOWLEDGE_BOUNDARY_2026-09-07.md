# ResearchOS Architecture Decision Record — Learning vs Knowledge Boundary

**Date:** 2026-09-07  
**Status:** Accepted  
**Scope:** Experiment learning, cognitive learning, durable knowledge memory  
**Decision:** Keep the existing `LearningRecord` concepts separate by domain; do not create a new root `researchos/learning.py` at this stage.

---

## 1. Problem

ResearchOS currently contains two classes named `LearningRecord`:

- `researchos/experiments/learning.py` — lessons extracted from a validated experiment.
- `researchos/objects/cognitive.py` — a record of trader cognitive learning progress.

The repository also contains `researchos/objects/knowledge.py`, where `Knowledge` is the durable semantic memory object.

A previous architecture diagram referenced a future `researchos/learning.py`. Creating that file now would introduce a third learning abstraction before the responsibilities of the existing objects are resolved.

## 2. Evidence From The Current Repository

The experiment-layer `LearningRecord` explicitly models:

`Experiment → ExperimentRun → ExperimentValidation → LearningRecord`

and stores experiment-specific findings, observed patterns, recommendations, confidence, and a learning trace.

The cognitive-layer `LearningRecord` is part of the Cognitive object model and is therefore a different domain concept.

`Knowledge` is already the durable market-memory object and carries semantic fields plus `source_references` and `knowledge_trace`.

## 3. Decision

### 3.1 Experiment LearningRecord

Keep `researchos/experiments/learning.py` as the experiment-process learning object.

Its responsibility is:

- summarize what an experiment taught;
- retain experiment/validation/hypothesis/run references;
- capture patterns and recommendations;
- preserve an auditable learning trace.

It is **not** the durable market knowledge store.

### 3.2 Cognitive LearningRecord

Keep `researchos/objects/cognitive.py::LearningRecord` as the cognitive-domain object.

It must not be reused as the experiment-learning object merely to remove a duplicate class name.

### 3.3 Knowledge

`researchos/objects/knowledge.py::Knowledge` remains the canonical durable semantic memory object for validated market knowledge.

The canonical evidence boundary is:

```text
Experiment
   ↓
Run
   ↓
Result
   ↓
Validation
   ↓
Finding
   ↓
Knowledge
```

A `LearningRecord` may describe the lesson extracted during the experiment workflow, but it does not replace the validated `Finding` gate for durable Knowledge.

### 3.4 No new root learning.py yet

Do **not** create `researchos/learning.py` merely because an old architecture diagram references it.

A new package-level learning layer should only be introduced after a concrete responsibility is identified that cannot be expressed by:

- experiment learning;
- cognitive learning;
- durable Knowledge memory.

## 4. Why This Decision Is Safer

This preserves the current public APIs and avoids a premature third abstraction.

It also prevents a dangerous architectural shortcut where an internally generated lesson could become durable knowledge without a validated evidence lineage.

The system therefore distinguishes:

```text
LearningRecord = what an experiment/process learned
Knowledge      = what the system is justified in remembering
Finding        = validated empirical evidence supporting that memory
```

## 5. Required Future Work

Before changing the learning model further, audit these paths together:

1. `researchos/experiments/learning.py`
2. `researchos/objects/cognitive.py`
3. `researchos/objects/knowledge.py`
4. `researchos/storage/repository.py`
5. `researchos/evidence/knowledge_certification.py`
6. validators and tests for both LearningRecord implementations

The next implementation milestone is **not** another learning class. It is to make the existing boundaries explicit in tests and documentation, then verify whether experiment learning should optionally reference the canonical Finding/Knowledge lineage.

## 6. Architectural Invariant

> **No LearningRecord, regardless of domain, may bypass validated evidence when its output is promoted into durable market Knowledge.**
