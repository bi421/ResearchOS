# Phase 2–3: Data → Research Boundary V1

## Objective

Establish an explicit API-first boundary between the Data Block and the Research Block, and make research lineage traceable to the exact validated dataset identity.

## Architecture

```text
Raw source
   ↓
Data loader
   ↓
HistoricalDataset
   ↓
DatasetValidator
   ↓
ValidatedDatasetRef   ← data-boundary.v1
   ↓
ResearchInput         ← research-boundary.v1
   ↓
Research / Experiment
   ↓
EvidenceCollection
   ↓
ProbabilityAssessment
   ↓
ResearchEvidenceLink
```

## Phase 2 — Research boundary

`ResearchInput` is the canonical input contract for a research run. It requires:

- research ID
- falsifiable research question
- methodology version
- validated dataset reference

`ResearchEvidenceLink` records the lineage from a research run to the complete dataset identity, evidence collection, and probability assessment hash. Both `dataset_content_hash` and `dataset_hash` are preserved so downstream evidence cannot silently detach from the validated dataset identity.

The Research Block therefore does not receive an unvalidated `HistoricalDataset` as its architectural input.

## Phase 3 — Data boundary

`ValidatedDatasetRef` is the data-facing contract. It carries dataset identity and validation evidence without exposing mutable records across the boundary.

Required identity:

- dataset ID
- dataset content hash
- dataset hash
- symbol
- timeframe
- data type
- record count
- validation quality score
- validation errors/warnings

A reference can only be created when `HistoricalDataset.status == VALIDATED`, both dataset hashes exist, the validation report has no errors, its record count matches the dataset, and its quality score is positive.

## Invariants

1. Unvalidated data cannot cross the Data → Research boundary.
2. Dataset content identity is preserved using `dataset_content_hash`.
3. Complete dataset identity is preserved using both `dataset_content_hash` and `dataset_hash`.
4. Research is bound to a specific dataset identity, not merely a symbol/timeframe label.
5. Contracts are immutable (`frozen=True`).
6. Contracts support deterministic dictionary serialization for process/language boundaries.
7. Raw dataset records remain owned by the Data Block.
8. No broker, order, autonomous execution, ML, LLM, or hidden trading logic is introduced.

## Verification

`researchos/tests/test_data_research_boundary.py` covers:

- validated dataset reference creation
- rejection of unvalidated datasets
- rejection of incomplete dataset identity
- rejection of validation errors and record-count mismatches
- ResearchInput serialization round-trip
- rejection of invalid validation evidence
- research/evidence lineage round-trip
- required dataset-hash preservation in evidence lineage
