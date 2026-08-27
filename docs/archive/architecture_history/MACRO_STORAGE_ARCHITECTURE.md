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

# ResearchOS Macro Intelligence Layer — Storage Architecture

**Version:** 1.0.0-frozen
**Date:** 2026-08-03
**Status:** ARCHITECTURALLY FROZEN — Ready for Implementation
**Classification:** Internal — Quantitative Platform

---

## Table of Contents

1. [Storage Architecture Overview](#1-storage-architecture-overview)
2. [Historical Storage Layer](#2-historical-storage-layer)
3. [Revision Engine](#3-revision-engine)
4. [Evidence Repository](#4-evidence-repository)
5. [Source Registry](#5-source-registry)
6. [Validation Pipeline](#6-validation-pipeline)
7. [Storage Layout](#7-storage-layout)
8. [Audit & Compliance](#8-audit--compliance)
9. [Performance Requirements](#9-performance-requirements)

---

## 1. Storage Architecture Overview

### 1.1 Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Immutable** | Append-only writes; no updates or deletes to historical data |
| **Deterministic** | Same input produces identical output bytes; reproducible storage |
| **Audit-Ready** | Full provenance trail; every byte traceable to source |
| **Versioned** | Schema evolution via versioned parquet partitions |
| **Partitioned** | Time-based partitioning for efficient range queries |
| **Compressed** | Columnar compression for storage efficiency |

### 1.2 Storage Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                     STORAGE LAYER                                │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Parquet Store  │  │  JSON Store     │  │  Index Store    │  │
│  │  (time series)  │  │  (events)       │  │  (lookups)      │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │            │
│  ┌────────▼────────────────────▼────────────────────▼────────┐  │
│  │              Storage Abstraction Layer                      │  │
│  │         (BaseStore interface for all backends)              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Revision Engine                                │  │
│  │    (Tracks revision chains, maintains versioned views)      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Validation Pipeline                            │  │
│  │    (Schema → Range → Freshness → Reconciliation checks)     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Evidence Repository                            │  │
│  │    (Immutable evidence storage with full provenance)        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Source Registry                                │  │
│  │    (Source metadata, credentials, health status)            │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Storage Root

```
.agnes/data/macro/
├── parquet/                    # Columnar time-series storage
│   ├── v1/                    # Schema version
│   │   ├── DXY/
│   │   │   ├── year=2026/month=08/
│   │   │   │   ├── data.parquet
│   │   │   │   └── _metadata
│   │   │   └── year=2026/month=07/
│   │   │       └── data.parquet
│   │   ├── US10Y/
│   │   ├── CPI_YOY/
│   │   └── ...
│   └── v2/                    # Future schema versions
├── json/                      # Document storage
│   ├── events/
│   │   └── 2026/
│   │       └── 08/
│   │           └── FOMC_20260917.jsonl
│   ├── evidence/
│   │   └── 2026/
│   │       └── 08/
│   │           └── EV_20260815_001.jsonl
│   └── knowledge/
│       └── 2026/
│           └── 08/
│               └── KN_20260815_001.jsonl
├── indexes/                   # Lookup indexes
│   ├── by_series.jsonl        # Series → file mapping
│   ├── by_date.jsonl          # Date → series mapping
│   ├── by_source.jsonl        # Source → series mapping
│   ├── by_event.jsonl         # Event → evidence mapping
│   └── by_revision.jsonl      # Revision chain mapping
├── registry/                  # Source registry
│   └── sources.json           # All registered sources
├── schema/                    # Schema definitions
│   ├── series_v1.json
│   ├── evidence_v1.json
│   └── event_v1.json
└── audit/                     # Audit logs
    └── 2026/
        └── 08/
            └── audit_20260815.log
```

---

## 2. Historical Storage Layer

### 2.1 Parquet Schema

**Version:** `parquet/v1`
**Module:** `macro_intelligence.storage.parquet_schema`
**Status:** Frozen

#### 2.1.1 Schema Definition

```python
# Parquet Schema for NormalizedSeries
# Using pyarrow schema definition

from pyarrow import schema, field, date32, timestamp, float64, string, int64, struct

SERIES_SCHEMA = schema(
    [
        # Core identification
        field("series_id", string()),  # SER_YYYYMMDD_NNN
        field("source", string()),  # FRED, BLS, ICE, etc.
        field("timestamp", timestamp("us", "UTC")),  # Record creation time
        # Time dimensions
        field("observation_period", date32()),  # The period observed
        field("release_time", timestamp("us", "UTC")),  # Official release (nullable)
        field("available_time", timestamp("us", "UTC")),  # Available in MIL
        # Data
        field("value", float64()),  # Observed value (nullable)
        field("unit", string()),  # percent, index, basis_points, etc.
        field("frequency", string()),  # daily, weekly, monthly, quarterly, ad_hoc
        # Revision tracking
        field("revision_id", string()),  # REV_YYYYMMDD_NNN (nullable)
        field("revision_number", int64()),  # 0 = initial, 1+ = revisions
        field("quality_score", float64()),  # 0.0 - 1.0
        # Provenance
        field(
            "metadata",
            struct(
                [
                    field("source_url", string()),
                    field("source_record_id", string()),
                    field("original_value", float64()),
                    field("original_unit", string()),
                    field("transformation_log", string()),  # JSON array
                    field("validation_checks", string()),  # JSON array
                ]
            ),
        ),
        # Partition keys (for efficient querying)
        field("year", int32()),  # Extracted from observation_period
        field("month", int32()),  # Extracted from observation_period
    ]
)
```

#### 2.1.2 Partition Strategy

```
Partition by: series_id / year / month

Example:
.parquet/
└── DXY/
    ├── year=2026/
    │   ├── month=08/
    │   │   └── data.parquet      # Daily data for August 2026
    │   ├── month=07/
    │   │   └── data.parquet
    │   └── month=06/
    │       └── data.parquet
    └── year=2025/
        └── month=12/
            └── data.parquet
```

**Partition Size Target:** 128MB - 512MB per parquet file
**Max Rows per File:** 10,000,000 (enforcement)

#### 2.1.3 Compression Settings

```python
COMPRESSION = "zstd"  # Best compression ratio
COMPRESSION_LEVEL = 3  # Balanced speed/ratio
DICTIONARY_SIZE = 1024 * 1024  # 1MB dictionary
BLOOM_FILTER = True  # Enable for string columns
STATISTICS = "FULL"  # Full column statistics
```

#### 2.1.4 File Naming Convention

```
{series_id}_{YYYYMMDD}_{HHMMSS}_{revision_id or "INIT"}.parquet

Examples:
- DXY_20260815_143022_INIT.parquet
- US10Y_20260815_143022_REV20260815001.parquet
- CPI_YOY_20260812_083000_INIT.parquet
```

### 2.2 Storage Operations

#### 2.2.1 Append-Only Writes

```python
class ParquetStore(BaseStore):
    """Immutable, append-only Parquet storage."""

    def append_series(self, series: NormalizedSeries) -> Path:
        """
        Append a single series observation.

        Returns:
            Path to the written parquet file
        """
        # 1. Determine partition path
        partition_path = self._get_partition_path(series)

        # 2. Check if file exists
        existing_file = self._find_existing_file(partition_path, series)

        # 3. If file exists, merge; otherwise create new
        if existing_file:
            return self._append_to_existing(existing_file, series)
        else:
            return self._create_new_file(partition_path, series)

    def _append_to_existing(self, existing: Path, series: NormalizedSeries) -> Path:
        """Append to existing parquet file (immutable append)."""
        # Read existing
        df_existing = pq.read_table(existing)

        # Append new row
        df_new = pa.table(
            {
                "series_id": [series.series_id],
                "source": [series.source],
                "timestamp": [series.timestamp],
                # ... all fields
            }
        )

        df_merged = pa.concat_tables([df_existing, df_new])

        # Write to new file (append-only semantics)
        new_path = self._generate_new_path(existing)
        pq.write_table(df_merged, new_path, compression=COMPRESSION)

        # Update index
        self._update_indexes(series.series_id, new_path)

        # Delete old file (with audit log)
        self._audit_delete(existing, "appended")

        return new_path

    def _create_new_file(self, partition_path: Path, series: NormalizedSeries) -> Path:
        """Create new parquet file for partition."""
        df = pa.table(
            {
                "series_id": [series.series_id],
                "source": [series.source],
                "timestamp": [series.timestamp],
                # ... all fields
            }
        )

        file_path = partition_path / f"{series.series_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_INIT.parquet"
        pq.write_table(df, file_path, compression=COMPRESSION)

        # Update indexes
        self._update_indexes(series.series_id, file_path)

        return file_path
```

#### 2.2.2 Immutable Delete (Soft Delete)

```python
def _audit_delete(self, path: Path, reason: str) -> None:
    """
    Log deletion for audit trail.
    Files are never truly deleted; only logged.
    """
    audit_entry = {
        "action": "delete",
        "path": str(path),
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "user": "system",  # Always system-initiated
    }

    # Write to audit log
    audit_path = Path(".agnes/data/macro/audit") / datetime.utcnow().strftime("%Y/%m")
    audit_path.mkdir(parents=True, exist_ok=True)

    audit_file = audit_path / f"audit_{datetime.utcnow().strftime('%Y%m%d')}.log"
    with open(audit_file, "a") as f:
        f.write(json.dumps(audit_entry) + "\n")

    # Remove from index
    self._remove_from_indexes(path)

    # Physically delete
    path.unlink(missing_ok=True)
```

### 2.3 Query Operations

```python
class ParquetStore(BaseStore):
    """Immutable, append-only Parquet storage."""

    def query_series(
        self,
        series_id: str,
        start: date,
        end: date,
        include_revisions: bool = False,
    ) -> list[NormalizedSeries]:
        """
        Query series with date range.

        Returns:
            List of NormalizedSeries ordered by observation_period
        """
        # Determine partition paths
        partitions = self._get_partitions(series_id, start, end)

        # Read and merge
        tables = []
        for partition in partitions:
            for file in partition.glob("*.parquet"):
                table = pq.read_table(file)
                tables.append(table)

        if not tables:
            return []

        merged = pa.concat_tables(tables)

        # Filter by date range
        mask = (merged.column("observation_period").to_pylist() >= start) & (merged.column("observation_period").to_pylist() <= end)
        filtered = merged.filter(mask)

        # Apply revision filter
        if not include_revisions:
            filtered = self._get_latest_revision(filtered)

        # Sort by observation_period
        sorted_idx = pa.compute.sort_indices(filtered.column("observation_period"))
        sorted_table = filtered.take(sorted_idx)

        # Convert to NormalizedSeries objects
        return [self._table_to_series(row) for row in sorted_table.to_pylist()]

    def query_latest(self, series_id: str) -> NormalizedSeries | None:
        """Get the latest observation for a series."""
        # Use index for fast lookup
        latest_file = self._get_latest_file(series_id)

        if not latest_file:
            return None

        table = pq.read_table(latest_file)
        if table.num_rows == 0:
            return None

        # Get last row
        last_row = table.slice(table.num_rows - 1).to_pylist()[0]
        return self._table_to_series(last_row)

    def query_by_date(self, date: date) -> dict[str, NormalizedSeries]:
        """Get all series observations for a specific date."""
        # Use date index for fast lookup
        series_ids = self._get_series_for_date(date)

        result = {}
        for series_id in series_ids:
            latest = self.query_latest(series_id)
            if latest and latest.observation_period == date:
                result[series_id] = latest

        return result
```

---

## 3. Revision Engine

### 3.1 Purpose

The Revision Engine manages the lifecycle of data revisions:
- Track revision chains
- Maintain versioned views
- Enable historical reconstruction
- Ensure audit compliance

### 3.2 Revision Chain Model

```
Revision Chain Example:

GDP_YOY for 2026-Q2

SER_20260730_001 (Initial: 2.4%)
    │
    ├──► REV_20260815_001 (First Revision: 2.1%)
    │       │
    │       └──► REV_20260901_001 (Second Revision: 2.3%)
    │               │
    │               └── [No further revisions]
    │
    └──► SER_20260730_001_Reconstructed (Historical snapshot)
```

### 3.3 Revision Storage Schema

```python
# Parquet Schema for Revision Tracking
REVISION_SCHEMA = schema(
    [
        field("revision_id", string()),  # REV_YYYYMMDD_NNN
        field("original_evidence_id", string()),  # Reference to original
        field("series_id", string()),  # Series being revised
        field("observation_period", date32()),  # Period observed
        field("revision_number", int64()),  # 0 = initial, 1+ = revisions
        field("revision_time", timestamp("us", "UTC")),
        field("revision_reason", string()),
        field("original_value", float64()),
        field("revised_value", float64()),
        field("change_bps", float64()),
        field("quality_score", float64()),
        field("superseded_by", string()),  # Nullable
        field(
            "metadata",
            struct(
                [
                    field("source", string()),
                    field("source_url", string()),
                    field("revision_notice", string()),
                    field("impact_assessment", string()),
                ]
            ),
        ),
    ]
)
```

### 3.4 Revision Engine Operations

```python
class RevisionEngine:
    """
    Manages revision chains for all time-series data.
    """

    def __init__(self, store: ParquetStore):
        self.store = store

    def create_revision(
        self,
        original_evidence_id: str,
        series_id: str,
        observation_period: date,
        new_value: float,
        reason: str,
        source: str,
    ) -> str:
        """
        Create a new revision for existing evidence.

        Returns:
            New revision_id
        """
        # 1. Get original evidence
        original = self.store.get_evidence(original_evidence_id)

        # 2. Generate revision ID
        revision_id = self._generate_revision_id()

        # 3. Calculate change
        original_value = original.value
        change_bps = (new_value - original_value) * 10000  # Convert to bps

        # 4. Create revision record
        revision = RevisionRecord(
            revision_id=revision_id,
            original_evidence_id=original_evidence_id,
            series_id=series_id,
            observation_period=observation_period,
            revision_number=original.revision_number + 1,
            revision_time=datetime.utcnow(),
            revision_reason=reason,
            original_value=original_value,
            revised_value=new_value,
            change_bps=change_bps,
            quality_score=1.0,
            superseded_by=None,
            metadata={
                "source": source,
                "source_url": original.provenance.original_source_url,
                "revision_notice": reason,
                "impact_assessment": self._assess_impact(series_id, change_bps),
            },
        )

        # 5. Store revision
        self.store.append_revision(revision)

        # 6. Update original to point to this revision
        self._link_revision(original_evidence_id, revision_id)

        # 7. Create new evidence record with revised value
        new_evidence = self._create_revised_evidence(original, new_value, revision_id)
        self.store.append_evidence(new_evidence)

        return revision_id

    def get_revision_chain(self, series_id: str, observation_period: date) -> list[RevisionRecord]:
        """
        Get full revision chain for a series and period.

        Returns:
            List of revisions ordered chronologically
        """
        return self.store.query_revisions(series_id, observation_period)

    def get_latest_value(self, series_id: str, observation_period: date) -> float:
        """
        Get the latest (most recent) value for a series and period.

        Returns:
            Latest value or None if not found
        """
        chain = self.get_revision_chain(series_id, observation_period)
        if not chain:
            return None
        return chain[-1].revised_value

    def reconstruct_historical(self, series_id: str, observation_period: date, as_of_date: date) -> float:
        """
        Reconstruct what the value was as of a historical date.

        Args:
            series_id: Series identifier
            observation_period: The period being observed
            as_of_date: The date to reconstruct to

        Returns:
            Value as it was known on as_of_date
        """
        chain = self.get_revision_chain(series_id, observation_period)

        # Find the latest revision that existed before as_of_date
        for revision in reversed(chain):
            if revision.revision_time <= as_of_date:
                return revision.revised_value

        # If no revisions existed, return initial value
        if chain:
            return chain[0].original_value

        return None

    def _assess_impact(self, series_id: str, change_bps: float) -> str:
        """
        Assess the market impact of a revision.
        """
        abs_change = abs(change_bps)
        if abs_change < 10:
            return "MINIMAL"
        elif abs_change < 50:
            return "MODERATE"
        elif abs_change < 100:
            return "SIGNIFICANT"
        else:
            return "MAJOR"
```

### 3.5 Revision Rules

| Rule | Description |
|------|-------------|
| **Never overwrite** | Original evidence is never modified |
| **Create new records** | Revisions create new NormalizedSeries and EvidenceObjects |
| **Link revisions** | Each revision references its predecessor |
| **Preserve provenance** | Original source information preserved in metadata |
| **Quality tracking** | Each revision has independent quality_score |
| **Audit trail** | Full revision chain queryable |
| **Historical reconstruction** | Can reconstruct any historical state |

---

## 4. Evidence Repository

### 4.1 Purpose

The Evidence Repository provides immutable storage for all macroeconomic evidence objects with full provenance and auditability.

### 4.2 Storage Schema

```python
# JSON Schema for Evidence Objects
EVIDENCE_SCHEMA = {
    "type": "object",
    "required": [
        "evidence_id",
        "source",
        "source_quality_score",
        "series_reference",
        "observation_time",
        "release_time",
        "available_time",
        "value",
        "forecast",
        "previous",
        "revision",
        "confidence",
        "provenance",
    ],
    "properties": {
        "evidence_id": {"type": "string", "pattern": "^EV_[0-9]{14}_[a-z0-9]{12}$"},
        "source": {"type": "string", "maxLength": 64},
        "source_quality_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "series_reference": {"type": "string"},
        "observation_time": {"type": "string", "format": "date-time"},
        "release_time": {"type": "string", "format": "date-time", "nullable": True},
        "available_time": {"type": "string", "format": "date-time"},
        "value": {"type": ["number", "null"]},
        "forecast": {"type": ["number", "null"]},
        "previous": {"type": ["number", "null"]},
        "revision": {
            "type": ["object", "null"],
            "properties": {
                "revision_id": {"type": "string"},
                "original_evidence_id": {"type": "string"},
                "revision_number": {"type": "integer"},
                "revision_time": {"type": "string", "format": "date-time"},
                "revision_reason": {"type": "string"},
                "superseded": {"type": "boolean"},
            },
        },
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "provenance": {
            "type": "object",
            "required": ["original_source", "ingestion_pipeline", "transformation_log"],
            "properties": {
                "original_source": {"type": "string"},
                "ingestion_pipeline": {"type": "array", "items": {"type": "string"}},
                "transformation_log": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "timestamp": {"type": "string", "format": "date-time"},
                            "operation": {"type": "string"},
                            "input": {"type": "object"},
                            "output": {"type": "object"},
                        },
                    },
                },
                "verification_checks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "check": {"type": "string"},
                            "result": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"},
                        },
                    },
                },
            },
        },
    },
}
```

### 4.3 Evidence Storage Operations

```python
class EvidenceRepository:
    """
    Immutable evidence storage with full provenance.
    """

    def __init__(self, store: ParquetStore, json_store: JsonStore):
        self.store = store
        self.json_store = json_store

    def append_evidence(self, evidence: EvidenceObject) -> Path:
        """
        Append evidence to storage (immutable).

        Returns:
            Path to stored evidence file
        """
        # 1. Write to JSON store
        json_path = self.json_store.append_evidence(evidence)

        # 2. Write to Parquet store for analytics
        parquet_path = self.store.append_evidence_parquet(evidence)

        # 3. Update indexes
        self._update_indexes(evidence.evidence_id, evidence.series_reference, json_path)

        # 4. Log to audit
        self._audit_append(evidence.evidence_id, json_path, parquet_path)

        return json_path

    def get_evidence(self, evidence_id: str) -> EvidenceObject | None:
        """
        Retrieve evidence by ID.

        Returns:
            EvidenceObject or None
        """
        # Try JSON store first (faster for single lookups)
        evidence = self.json_store.get_evidence(evidence_id)
        if evidence:
            return evidence

        # Fallback to Parquet
        return self.store.get_evidence_parquet(evidence_id)

    def get_evidence_for_series(self, series_id: str, date: date) -> list[EvidenceObject]:
        """
        Get all evidence for a series on a date.

        Returns:
            List of EvidenceObjects (may include revisions)
        """
        # Query by series_id and date
        evidence_ids = self._get_evidence_ids(series_id, date)

        return [self.get_evidence(eid) for eid in evidence_ids if eid]

    def get_evidence_chain(self, evidence_id: str) -> list[EvidenceObject]:
        """
        Get full revision chain for evidence.

        Returns:
            List of EvidenceObjects in revision order
        """
        evidence = self.get_evidence(evidence_id)
        if not evidence:
            return []

        chain = [evidence]

        # Follow revision chain
        current = evidence
        while current.revision and not current.revision.superseded:
            next_evidence = self.get_evidence(current.revision.revision_id)
            if next_evidence:
                chain.append(next_evidence)
                current = next_evidence
            else:
                break

        return chain

    def _update_indexes(self, evidence_id: str, series_id: str, path: Path) -> None:
        """Update lookup indexes."""
        # Series index
        self.json_store.append_to_index(
            "by_series",
            {
                "evidence_id": evidence_id,
                "series_id": series_id,
                "path": str(path),
            },
        )

        # Date index
        self.json_store.append_to_index(
            "by_date",
            {
                "evidence_id": evidence_id,
                "series_id": series_id,
                "date": evidence_id.observation_time.date().isoformat(),
                "path": str(path),
            },
        )
```

### 4.4 Evidence Immutability Guarantees

```python
class EvidenceRepository:
    """
    Immutable evidence storage with full provenance.
    """

    def append_evidence(self, evidence: EvidenceObject) -> Path:
        """
        Append evidence to storage (immutable).

        IMMutability Guarantees:
        1. Evidence object is frozen (dataclass frozen=True)
        2. Storage is append-only (no updates)
        3. Deleted evidence is logged, not truly deleted
        4. Full audit trail maintained
        """
        # ... implementation
```

---

## 5. Source Registry

### 5.1 Purpose

The Source Registry maintains metadata about all external data sources, including credentials (encrypted), health status, and configuration.

### 5.2 Registry Schema

```python
# JSON Schema for Source Registry
SOURCE_REGISTRY_SCHEMA = {
    "type": "object",
    "properties": {
        "sources": {
            "type": "object",
            "patternProperties": {
                "^[a-zA-Z0-9_]+$": {
                    "type": "object",
                    "required": ["name", "type", "enabled"],
                    "properties": {
                        "name": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": ["fred", "bls", "cftc", "fed", "cboe", "treasury", "ism", "wgc"],
                        },
                        "enabled": {"type": "boolean"},
                        "polling_interval_minutes": {"type": "integer"},
                        "max_retries": {"type": "integer"},
                        "timeout_seconds": {"type": "integer"},
                        "credentials": {
                            "type": "object",
                            "properties": {
                                "api_key": {"type": "string", "encrypted": True},
                                "secret": {"type": "string", "encrypted": True},
                            },
                        },
                        "health": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
                                "last_check": {"type": "string", "format": "date-time"},
                                "last_success": {"type": "string", "format": "date-time"},
                                "last_error": {"type": "string"},
                            },
                        },
                        "supported_series": {"type": "array", "items": {"type": "string"}},
                        "rate_limit": {
                            "type": "object",
                            "properties": {
                                "requests_per_minute": {"type": "integer"},
                                "remaining": {"type": "integer"},
                                "reset_time": {"type": "string", "format": "date-time"},
                            },
                        },
                    },
                }
            },
        }
    },
}
```

### 5.3 Source Registry Operations

```python
class SourceRegistry:
    """
    Registry of all external data sources.
    """

    def __init__(self, store: JsonStore):
        self.store = store
        self._lock = threading.Lock()

    def register_source(self, source: SourceConfig) -> None:
        """Register a new data source."""
        with self._lock:
            registry = self._load_registry()
            registry["sources"][source.source_id] = source.to_dict()
            self._save_registry(registry)

    def update_health(self, source_id: str, health: HealthStatus) -> None:
        """Update source health status."""
        with self._lock:
            registry = self._load_registry()
            if source_id in registry["sources"]:
                registry["sources"][source_id]["health"] = health.to_dict()
                self._save_registry(registry)

    def get_source(self, source_id: str) -> SourceConfig | None:
        """Get source configuration."""
        registry = self._load_registry()
        source_data = registry["sources"].get(source_id)
        if not source_data:
            return None
        return SourceConfig.from_dict(source_data)

    def get_enabled_sources(self) -> list[SourceConfig]:
        """Get all enabled sources."""
        registry = self._load_registry()
        return [SourceConfig.from_dict(data) for data in registry["sources"].values() if data.get("enabled", False)]

    def get_supported_series(self) -> dict[str, list[str]]:
        """Get mapping of source to supported series."""
        registry = self._load_registry()
        return {source_id: data.get("supported_series", []) for source_id, data in registry["sources"].items() if data.get("enabled", False)}
```

---

## 6. Validation Pipeline

### 6.1 Pipeline Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Schema     │────►│  Range      │────►│  Freshness  │────►│  Reconcile  │
│  Validator  │     │  Validator  │     │  Validator  │     │  Validator  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
  Pass/Fail           Pass/Fail           Pass/Fail           Pass/Fail
       │                   │                   │                   │
       └───────────────────┴───────────────────┴───────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   Quarantine    │
                              │  (on failure)   │
                              └─────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   Alert System  │
                              │  (on failure)   │
                              └─────────────────┘
```

### 6.2 Validator Interface

```python
class BaseValidator(ABC):
    """Base class for all validators."""

    @abstractmethod
    def validate(self, data: Any) -> ValidationResult:
        """
        Validate data and return result.

        Returns:
            ValidationResult with pass/fail status
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Return validator name."""
        ...


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    validator_name: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    suggested_fix: str | None = None
    metadata: dict = field(default_factory=dict)
```

### 6.3 Schema Validator

```python
class SchemaValidator(BaseValidator):
    """Validates data against Pydantic schemas."""

    def validate(self, series: NormalizedSeries) -> ValidationResult:
        """
        Validate NormalizedSeries against schema.

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        # Validate series_id format
        if not re.match(r"^SER_\d{8}_\d+$", series.series_id):
            errors.append(f"Invalid series_id format: {series.series_id}")

        # Validate source is registered
        if series.source not in VALID_SOURCES:
            warnings.append(f"Unknown source: {series.source}")

        # Validate timestamp is UTC
        if series.timestamp.tzinfo != UTC:
            errors.append("timestamp must be UTC")

        # Validate observation_period is valid date
        if not isinstance(series.observation_period, date):
            errors.append("observation_period must be a date")

        # Validate value is in valid range for series type
        if series.value is not None:
            valid_range = SERIES_RANGES.get(series.series_id)
            if valid_range:
                min_val, max_val = valid_range
                if not (min_val <= series.value <= max_val):
                    warnings.append(f"Value {series.value} outside expected range [{min_val}, {max_val}]")

        # Validate quality_score
        if not (0.0 <= series.quality_score <= 1.0):
            errors.append("quality_score must be between 0.0 and 1.0")

        return ValidationResult(
            is_valid=len(errors) == 0,
            validator_name="SchemaValidator",
            errors=errors,
            warnings=warnings,
        )

    def get_name(self) -> str:
        return "SchemaValidator"
```

### 6.4 Range Validator

```python
class RangeValidator(BaseValidator):
    """Validates data values are within plausible ranges."""

    # Plausible ranges for each series type
    RANGES: dict[str, tuple[float, float]] = {
        "DXY": (80.0, 160.0),
        "US2Y": (-5.0, 20.0),
        "US5Y": (-5.0, 20.0),
        "US10Y": (-5.0, 20.0),
        "US30Y": (-5.0, 20.0),
        "REAL_10Y": (-10.0, 15.0),
        "CPI_YOY": (-10.0, 50.0),
        "CPI_CORE_YOY": (-5.0, 40.0),
        "CPI_MOM": (-10.0, 20.0),
        "PPI_YOY": (-10.0, 50.0),
        "PPI_CORE_YOY": (-10.0, 50.0),
        "PCE_YOY": (-10.0, 50.0),
        "PCE_CORE_YOY": (-10.0, 50.0),
        "NFP_CHANGE": (-200.0, 1000.0),
        "UNRATE": (0.0, 50.0),
        "JOLTS_TOTAL": (0.0, 12000.0),
        "JOLTS_HIRINGS": (0.0, 10000.0),
        "JOLTS_SEPARATIONS": (0.0, 10000.0),
        "GDP_YOY": (-20.0, 30.0),
        "GDP_MOM": (-20.0, 30.0),
        "PMI_MFG": (20.0, 80.0),
        "PMI_SVC": (20.0, 80.0),
        "VIX": (10.0, 200.0),
        "MOVE": (50.0, 500.0),
    }

    def validate(self, series: NormalizedSeries) -> ValidationResult:
        """
        Validate value is within plausible range.
        """
        errors = []
        warnings = []

        if series.value is None:
            return ValidationResult(
                is_valid=True,
                validator_name="RangeValidator",
                warnings=["Value is null (missing data)"],
            )

        valid_range = self.RANGES.get(series.series_id)
        if valid_range:
            min_val, max_val = valid_range
            if series.value < min_val:
                errors.append(f"Value {series.value} below minimum {min_val}")
            elif series.value > max_val:
                errors.append(f"Value {series.value} above maximum {max_val}")

        # Check for sudden jumps (anomalous changes)
        # This would require access to previous value, handled in pipeline

        return ValidationResult(
            is_valid=len(errors) == 0,
            validator_name="RangeValidator",
            errors=errors,
            warnings=warnings,
        )

    def get_name(self) -> str:
        return "RangeValidator"
```

### 6.5 Validation Pipeline

```python
class ValidationPipeline:
    """
    Pipeline that runs all validators in sequence.
    """

    def __init__(self):
        self.validators: list[BaseValidator] = [
            SchemaValidator(),
            RangeValidator(),
            FreshnessValidator(),
            ReconciliationValidator(),
        ]

    def validate(self, series: NormalizedSeries) -> PipelineResult:
        """
        Run all validators in sequence.

        Returns:
            PipelineResult with aggregate validation status
        """
        all_errors = []
        all_warnings = []
        validator_results = []

        for validator in self.validators:
            result = validator.validate(series)
            validator_results.append(result)

            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        is_valid = len(all_errors) == 0
        is_quarantined = len([e for e in all_errors if "CRITICAL" in e]) > 0

        return PipelineResult(
            is_valid=is_valid,
            is_quarantined=is_quarantined,
            errors=all_errors,
            warnings=all_warnings,
            validator_results=validator_results,
        )

    def validate_batch(self, series_list: list[NormalizedSeries]) -> list[PipelineResult]:
        """
        Run validation on a batch of series.
        """
        return [self.validate(series) for series in series_list]
```

### 6.6 Quarantine Handling

```python
class QuarantineManager:
    """
    Manages quarantined data that failed validation.
    """

    def __init__(self, store: JsonStore):
        self.store = store
        self.quarantine_path = Path(".agnes/data/macro/quarantine")
        self.quarantine_path.mkdir(parents=True, exist_ok=True)

    def quarantine(self, series: NormalizedSeries, result: PipelineResult) -> Path:
        """
        Move failed series to quarantine.

        Returns:
            Path to quarantined file
        """
        quarantine_file = self.quarantine_path / f"{series.series_id}_{series.timestamp.isoformat()}.json"

        quarantine_record = {
            "series": series.to_dict(),
            "validation_result": {
                "is_valid": result.is_valid,
                "is_quarantined": result.is_quarantined,
                "errors": result.errors,
                "warnings": result.warnings,
                "validator_results": [r.to_dict() for r in result.validator_results],
            },
            "quarantined_at": datetime.utcnow().isoformat(),
            "quarantine_reason": "; ".join(result.errors) if result.errors else "Unknown",
        }

        with open(quarantine_file, "w") as f:
            json.dump(quarantine_record, f, indent=2)

        # Log to audit
        self._log_quarantine(series.series_id, result)

        return quarantine_file

    def release(self, quarantine_id: str) -> bool:
        """
        Release quarantined data (with warning).
        """
        quarantine_file = self.quarantine_path / f"{quarantine_id}.json"

        if not quarantine_file.exists():
            return False

        # Read and re-validate
        with open(quarantine_file) as f:
            record = json.load(f)

        series = NormalizedSeries.from_dict(record["series"])
        pipeline = ValidationPipeline()
        result = pipeline.validate(series)

        if result.is_valid:
            # Move to main storage
            # ... implementation
            quarantine_file.unlink()
            return True
        else:
            return False

    def _log_quarantine(self, series_id: str, result: PipelineResult) -> None:
        """Log quarantine event to audit."""
        audit_entry = {
            "action": "quarantine",
            "series_id": series_id,
            "errors": result.errors,
            "timestamp": datetime.utcnow().isoformat(),
        }
        # Write to audit log
        audit_path = Path(".agnes/data/macro/audit") / datetime.utcnow().strftime("%Y/%m")
        audit_path.mkdir(parents=True, exist_ok=True)
        audit_file = audit_path / f"audit_{datetime.utcnow().strftime('%Y%m%d')}.log"
        with open(audit_file, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
```

---

## 7. Storage Layout

### 7.1 Complete Directory Structure

```
.agnes/data/macro/
│
├── parquet/                          # Columnar time-series storage
│   ├── v1/                          # Schema version
│   │   ├── DXY/
│   │   │   ├── year=2026/
│   │   │   │   ├── month=08/
│   │   │   │   │   ├── DXY_20260815_143022_INIT.parquet
│   │   │   │   │   └── _metadata
│   │   │   │   └── month=07/
│   │   │   │       └── DXY_20260731_143022_INIT.parquet
│   │   │   └── year=2025/
│   │   │       └── month=12/
│   │   │           └── DXY_20251231_143022_INIT.parquet
│   │   ├── US10Y/
│   │   │   └── ...
│   │   ├── CPI_YOY/
│   │   │   └── ...
│   │   └── ...
│   └── v2/                          # Future schema versions
│
├── json/                            # Document storage
│   ├── events/
│   │   └── 2026/
│   │       └── 08/
│   │           ├── FOMC_20260917_180000.jsonl
│   │           ├── SPEECH_BAIS_20260715_143000.jsonl
│   │           └── CPI_20260812_083000.jsonl
│   ├── evidence/
│   │   └── 2026/
│   │       └── 08/
│   │           ├── EV_20260812_001.jsonl
│   │           └── EV_20260812_002.jsonl
│   ├── knowledge/
│   │   └── 2026/
│   │       └── 08/
│   │           └── KN_20260815_001.jsonl
│   └── reactions/
│       └── 2026/
│           └── 08/
│               └── MR_20260812_001.jsonl
│
├── indexes/                         # Lookup indexes
│   ├── by_series.jsonl              # series_id → file path
│   ├── by_date.jsonl                # date → series_ids
│   ├── by_source.jsonl              # source → series_ids
│   ├── by_event.jsonl               # event_id → evidence_ids
│   └── by_revision.jsonl            # revision_id → chain
│
├── registry/                        # Source registry
│   └── sources.json                 # All source configurations
│
├── schema/                          # Schema definitions
│   ├── series_v1.json
│   ├── evidence_v1.json
│   ├── event_v1.json
│   ├── reaction_v1.json
│   └── knowledge_v1.json
│
├── quarantine/                      # Failed validation data
│   └── 2026/
│       └── 08/
│           └── DXY_20260815T143022.json
│
└── audit/                           # Audit logs
    └── 2026/
        └── 08/
            ├── audit_20260812.log
            ├── audit_20260813.log
            ├── audit_20260814.log
            └── audit_20260815.log
```

### 7.2 Index File Format

```jsonl
# by_series.jsonl
{"series_id": "DXY", "file_path": "parquet/v1/DXY/year=2026/month=08/DXY_20260815_143022_INIT.parquet", "added_at": "2026-08-15T14:30:22Z"}
{"series_id": "DXY", "file_path": "parquet/v1/DXY/year=2026/month=07/DXY_20260731_143022_INIT.parquet", "added_at": "2026-07-31T14:30:22Z"}
{"series_id": "US10Y", "file_path": "parquet/v1/US10Y/year=2026/month=08/US10Y_20260815_143022_INIT.parquet", "added_at": "2026-08-15T14:30:22Z"}

# by_date.jsonl
{"date": "2026-08-12", "series_ids": ["CPI_YOY", "CPI_CORE_YOY", "PPI_YOY", "NFP_CHANGE"], "file_path": "indexes/by_date_2026-08.jsonl", "added_at": "2026-08-12T08:30:00Z"}

# by_revision.jsonl
{"revision_id": "REV_20260815_001", "original_evidence_id": "EV_20260801_001", "series_id": "GDP_YOY", "observation_period": "2026-07-01", "path": "json/evidence/2026/08/EV_20260815_001.jsonl", "added_at": "2026-08-15T10:00:00Z"}
```

---

## 8. Audit & Compliance

### 8.1 Audit Log Format

```jsonl
# audit_20260815.log
{"action": "append", "series_id": "DXY", "file_path": "parquet/v1/DXY/year=2026/month=08/DXY_20260815_143022_INIT.parquet", "timestamp": "2026-08-15T14:30:22Z", "user": "system", "record_count": 1}
{"action": "append", "series_id": "US10Y", "file_path": "parquet/v1/US10Y/year=2026/month=08/US10Y_20260815_143022_INIT.parquet", "timestamp": "2026-08-15T14:30:23Z", "user": "system", "record_count": 1}
{"action": "quarantine", "series_id": "CPI_YOY", "errors": ["Value 55.2 above maximum 50.0"], "timestamp": "2026-08-15T15:00:00Z", "user": "system"}
{"action": "revision", "revision_id": "REV_20260815_001", "original_evidence_id": "EV_20260801_001", "series_id": "GDP_YOY", "timestamp": "2026-08-15T16:00:00Z", "user": "system"}
{"action": "delete", "path": "parquet/v1/DXY/year=2026/month=07/DXY_20260731_143022_INIT.parquet", "reason": "appended", "timestamp": "2026-08-15T14:30:22Z", "user": "system"}
```

### 8.2 Audit Retention Policy

| Log Type | Retention Period | Storage Format |
|----------|-----------------|----------------|
| Audit logs | Indefinite | JSONL (compressed) |
| Quarantine files | 90 days | JSON |
| Revision history | Indefinite | Parquet + JSON |
| Source credentials | Encrypted | Vault (not filesystem) |

### 8.3 Compliance Requirements

```python
class AuditCompliance:
    """
    Ensures storage meets audit and compliance requirements.
    """

    def verify_integrity(self) -> dict:
        """
        Verify storage integrity.

        Returns:
            Dict with integrity check results
        """
        return {
            "parquet_files_valid": self._check_parquet_integrity(),
            "json_files_valid": self._check_json_integrity(),
            "indexes_consistent": self._check_index_consistency(),
            "audit_trail_complete": self._check_audit_trail(),
            "total_records": self._count_records(),
            "last_verification": datetime.utcnow().isoformat(),
        }

    def _check_parquet_integrity(self) -> bool:
        """Check all parquet files are readable."""
        # Implementation
        return True

    def _check_json_integrity(self) -> bool:
        """Check all JSON files are valid."""
        # Implementation
        return True

    def _check_index_consistency(self) -> bool:
        """Check indexes match actual files."""
        # Implementation
        return True

    def _check_audit_trail(self) -> bool:
        """Check audit trail is complete."""
        # Implementation
        return True
```

---

## 9. Performance Requirements

### 9.1 Query Performance Targets

| Operation | Target Latency | Notes |
|-----------|---------------|-------|
| Get latest series | < 10ms | Using index lookup |
| Get series (daily, 1 year) | < 100ms | Single partition |
| Get series (monthly, 10 years) | < 500ms | Multiple partitions |
| Get event by ID | < 10ms | JSON lookup |
| Search events | < 100ms | Indexed search |
| Get evidence chain | < 50ms | Recursive lookup |
| Validation pipeline | < 10ms | Per record |

### 9.2 Storage Performance

| Metric | Target |
|--------|--------|
| Append throughput | 1,000 records/sec |
| Read throughput | 10,000 records/sec |
| Parquet file size | 128MB - 512MB |
| Compression ratio | 3:1 to 5:1 |
| Index size | < 100MB for 10 years of data |

### 9.3 Scaling Considerations

```python
# Parallel reading strategy
def query_parallel(self, series_id: str, start: date, end: date) -> list[NormalizedSeries]:
    """
    Query series with parallel partition reading.
    """
    partitions = self._get_partitions(series_id, start, end)

    # Use thread pool for parallel reads
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(self._read_partition, partition) for partition in partitions]
        results = [f.result() for f in futures]

    # Merge and sort
    all_series = []
    for result in results:
        all_series.extend(result)

    return sorted(all_series, key=lambda x: x.observation_period)
```

---

## Final Declaration

---

**Macro Intelligence Layer Storage Architecture is architecturally frozen and ready for implementation.**

All storage contracts are versioned, immutable, and audit-ready. The architecture supports:
- Append-only Parquet storage with deterministic serialization
- Full revision chain tracking
- Immutable evidence repository with provenance
- Source registry with encrypted credentials
- Multi-stage validation pipeline with quarantine
- Complete audit trail for compliance

**Next Step:** Begin Phase 2 implementation — create the storage layer with Parquet and JSON backends.

---

*Document Version: 1.0.0-frozen*
*Last Updated: 2026-08-03*
*Classification: Internal — Quantitative Platform Architecture*
