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

# ResearchOS Macro Intelligence Layer — Data Quality Engine Architecture

**Version:** 1.0.0-frozen
**Date:** 2026-08-03
**Status:** ARCHITECTURALLY FROZEN — Ready for Implementation
**Classification:** Internal — Quantitative Platform

---

## Table of Contents

1. [Quality Engine Overview](#1-quality-engine-overview)
2. [Validation Pipeline Architecture](#2-validation-pipeline-architecture)
3. [Quality Score Engine](#3-quality-score-engine)
4. [Quarantine System](#4-quarantine-system)
5. [Alert System Contract](#5-alert-system-contract)
6. [Quality Dashboard](#6-quality-dashboard)
7. [Compliance & Audit](#7-compliance--audit)
8. [Implementation Roadmap](#8-implementation-roadmap)

---

## 1. Quality Engine Overview

### 1.1 Purpose

The Data Quality Engine ensures that all macroeconomic data ingested into the Macro Intelligence Layer meets strict quality standards before being stored or consumed. It operates as a gatekeeper — no data enters the system without passing validation.

### 1.2 Design Principles

| Principle | Enforcement |
|-----------|-------------|
| **Zero Silent Failures** | Every validation failure is logged and recorded |
| **Immutable Evidence** | Validated data becomes immutable evidence |
| **Fail-Open, Fail-Logged** | Data is quarantined, never silently dropped |
| **Score Transparency** | All quality scores are computed and stored |
| **Recovery Workflow** | Quarantined data has clear path to recovery |

### 1.3 Quality Engine Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA QUALITY ENGINE                           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Validation Pipeline                           │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────┐│  │
│  │  │ Schema  │→│ Range   │→│ Fresh   │→│ Revis   │→│ Cross││  │
│  │  │ Validator│  Validator│ Validator│ Validator│ SRC  ││  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Quality Score Engine                          │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │  │ Source      │ ┆ Completeness│ ┆ Freshness   │        │  │
│  │  │ Reliability │ │   Score     │ │   Score     │        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  │  ┌─────────────┐ ┌─────────────┐                        │  │
│  │  │ Anomaly     │ │ Composite   │                        │  │
│  │  │ Score       │ │   Score     │                        │  │
│  │  └─────────────┘ └─────────────┘                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│              ┌───────────────┼───────────────┐                  │
│              │               │               │                  │
│              ▼               ▼               ▼                  │
│  ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   PASS → Store  │ │ WARN → Log  │ │ FAIL →      │           │
│  │   (Evidence)    │ │ (Warning)   │ │ Quarantine  │           │
│  └─────────────────┘ └─────────────┘ └─────────────┘           │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Alert System                                  │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │  │   Warning   │ │   Critical  │ │ Source      │        │  │
│  │  │   Alerts    │ │   Alerts    │ │ Outage      │        │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 Quality Gates

```
Raw Record
    │
    ▼
┌─────────────────────────────────────────┐
│        VALIDATION GATE                  │
│                                         │
│  Schema ✓ → Range ✓ → Fresh ✓ → Rev ✓ → Cross ✓  │
│                                         │
│  ANY FAIL → QUARANTINE                  │
│  ALL PASS → CONTINUE                    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│        QUALITY SCORING GATE             │
│                                         │
│  Source Reliability × Completeness      │
│  × Freshness × Anomaly                  │
│                                         │
│  Score < 0.3 → QUARANTINE              │
│  Score 0.3-0.7 → WARN + STORE          │
│  Score > 0.7 → STORE                   │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│        STORAGE GATE                     │
│                                         │
│  Evidence Object Created                │
│  Immutable Storage Written              │
│  Audit Log Updated                      │
└─────────────────────────────────────────┘
```

---

## 2. Validation Pipeline Architecture

### 2.1 Pipeline Interface

**Version:** `pipeline/v1`
**Module:** `macro_intelligence.validation.pipeline`
**Status:** Frozen

```python
class ValidationPipeline(ABC):
    """
    Abstract validation pipeline that runs validators in sequence.

    Pipeline stages:
    1. Schema Validation
    2. Range Validation
    3. Freshness Validation
    4. Revision Validation
    5. Cross-source Reconciliation
    """

    def __init__(self, validators: list[BaseValidator]):
        self.validators = validators
        self._stage_order = [
            "schema",
            "range",
            "freshness",
            "revision",
            "cross_source",
        ]

    def validate(
        self,
        record: RawRecord,
        series: NormalizedSeries,
        evidence: EvidenceObject,
    ) -> ValidationResult:
        """
        Run complete validation pipeline.

        Args:
            record: Raw record from adapter
            series: Normalized series data
            evidence: Evidence object to validate

        Returns:
            ValidationResult with pass/fail status
        """
        results = []

        for stage in self._stage_order:
            validator = self._get_validator(stage)
            if not validator:
                continue

            stage_result = validator.validate(series, evidence)
            results.append(stage_result)

            # Short-circuit on critical failure
            if not stage_result.is_valid and stage_result.is_critical:
                return ValidationResult(
                    is_valid=False,
                    is_critical=True,
                    stages=results,
                    error=f"Critical failure in {stage}: {stage_result.errors}",
                    action="QUARANTINE",
                )

        all_valid = all(r.is_valid for r in results)
        any_warnings = any(r.warnings for r in results)

        return ValidationResult(
            is_valid=all_valid,
            is_critical=False,
            stages=results,
            warnings=[w for r in results for w in r.warnings],
            action="STORE" if all_valid else "WARN",
        )

    def _get_validator(self, stage: str) -> BaseValidator | None:
        """Get validator by stage name."""
        for validator in self.validators:
            if validator.stage == stage:
                return validator
        return None
```

### 2.2 Stage 1: Schema Validator

**Version:** `validator/schema/v1`
**Module:** `macro_intelligence.validation.schema`
**Status:** Frozen

#### 2.2.1 Purpose

Ensures all data conforms to the NormalizedSeries schema and required fields are present.

#### 2.2.2 Validation Rules

| Rule ID | Field | Condition | Severity |
|---------|-------|-----------|----------|
| SCHEMA-001 | series_id | Must match pattern `^SER_\d{8}_\d+$` | CRITICAL |
| SCHEMA-002 | source | Must be non-empty, max 64 chars | CRITICAL |
| SCHEMA-003 | timestamp | Must be UTC datetime | CRITICAL |
| SCHEMA-004 | observation_period | Must be valid date | CRITICAL |
| SCHEMA-005 | value | Must be float or null | WARNING |
| SCHEMA-006 | unit | Must be in allowed units enum | CRITICAL |
| SCHEMA-007 | frequency | Must be in FrequencyEnum | CRITICAL |
| SCHEMA-008 | quality_score | Must be 0.0-1.0 | CRITICAL |
| SCHEMA-009 | metadata | Must be JSON-serializable | WARNING |
| SCHEMA-010 | revision_id | Must match pattern if present | WARNING |

#### 2.2.3 Validator Implementation

```python
class SchemaValidator(BaseValidator):
    """
    Validates data against NormalizedSeries schema.
    """

    STAGE = "schema"

    # Allowed values
    ALLOWED_UNITS = {
        "index",
        "percent",
        "percent_ann",
        "basis_points",
        "thousands",
        "millions",
        "billions",
        "text",
    }
    ALLOWED_FREQUENCIES = {f.value for f in FrequencyEnum}
    SERIES_ID_PATTERN = re.compile(r"^SER_\d{8}_\d+$")
    REVISION_ID_PATTERN = re.compile(r"^REV_\d{8}_\d+$")

    def validate(
        self,
        series: NormalizedSeries,
        evidence: EvidenceObject,
    ) -> StageResult:
        """
        Validate series against schema.

        Returns:
            StageResult with pass/fail status
        """
        errors = []
        warnings = []

        # SCHEMA-001: series_id format
        if not self.SERIES_ID_PATTERN.match(series.series_id):
            errors.append(
                ValidationError(
                    rule_id="SCHEMA-001",
                    field="series_id",
                    value=series.series_id,
                    message=f"Invalid series_id format: {series.series_id}",
                    severity=Severity.CRITICAL,
                )
            )

        # SCHEMA-002: source non-empty
        if not series.source or len(series.source) > 64:
            errors.append(
                ValidationError(
                    rule_id="SCHEMA-002",
                    field="source",
                    value=series.source,
                    message=f"Source must be non-empty and max 64 chars",
                    severity=Severity.CRITICAL,
                )
            )

        # SCHEMA-003: timestamp is UTC
        if series.timestamp.tzinfo != UTC:
            errors.append(
                ValidationError(
                    rule_id="SCHEMA-003",
                    field="timestamp",
                    value=str(series.timestamp),
                    message="timestamp must be UTC",
                    severity=Severity.CRITICAL,
                )
            )

        # SCHEMA-004: observation_period is valid date
        if not isinstance(series.observation_period, date):
            errors.append(
                ValidationError(
                    rule_id="SCHEMA-004",
                    field="observation_period",
                    value=str(series.observation_period),
                    message="observation_period must be a date",
                    severity=Severity.CRITICAL,
                )
            )

        # SCHEMA-005: value is float or null
        if series.value is not None and not isinstance(series.value, (int, float)):
            warnings.append(
                ValidationError(
                    rule_id="SCHEMA-005",
                    field="value",
                    value=str(series.value),
                    message=f"Value type mismatch: {type(series.value)}",
                    severity=Severity.WARNING,
                )
            )

        # SCHEMA-006: unit is valid
        if series.unit not in self.ALLOWED_UNITS:
            errors.append(
                ValidationError(
                    rule_id="SCHEMA-006",
                    field="unit",
                    value=series.unit,
                    message=f"Invalid unit: {series.unit}",
                    severity=Severity.CRITICAL,
                )
            )

        # SCHEMA-007: frequency is valid
        if series.frequency.value not in self.ALLOWED_FREQUENCIES:
            errors.append(
                ValidationError(
                    rule_id="SCHEMA-007",
                    field="frequency",
                    value=series.frequency.value,
                    message=f"Invalid frequency: {series.frequency.value}",
                    severity=Severity.CRITICAL,
                )
            )

        # SCHEMA-008: quality_score range
        if not (0.0 <= series.quality_score <= 1.0):
            errors.append(
                ValidationError(
                    rule_id="SCHEMA-008",
                    field="quality_score",
                    value=series.quality_score,
                    message="quality_score must be between 0.0 and 1.0",
                    severity=Severity.CRITICAL,
                )
            )

        # SCHEMA-009: metadata serializable
        try:
            json.dumps(series.metadata)
        except (TypeError, ValueError) as e:
            warnings.append(
                ValidationError(
                    rule_id="SCHEMA-009",
                    field="metadata",
                    value=str(e),
                    message="metadata is not JSON-serializable",
                    severity=Severity.WARNING,
                )
            )

        # SCHEMA-010: revision_id format
        if series.revision_id and not self.REVISION_ID_PATTERN.match(series.revision_id):
            warnings.append(
                ValidationError(
                    rule_id="SCHEMA-010",
                    field="revision_id",
                    value=series.revision_id,
                    message=f"Invalid revision_id format: {series.revision_id}",
                    severity=Severity.WARNING,
                )
            )

        return StageResult(
            stage=self.STAGE,
            is_valid=len([e for e in errors if e.severity == Severity.CRITICAL]) == 0,
            is_critical=len(errors) > 0,
            errors=[e.to_dict() for e in errors],
            warnings=[w.to_dict() for w in warnings],
        )
```

### 2.3 Stage 2: Range Validator

**Version:** `validator/range/v1`
**Module:** `macro_intelligence.validation.range`
**Status:** Frozen

#### 2.3.1 Purpose

Validates that data values are within plausible ranges for each series type.

#### 2.3.2 Validation Rules

| Rule ID | Series | Min Value | Max Value | Severity |
|---------|--------|-----------|-----------|----------|
| RANGE-001 | DXY | 80.0 | 160.0 | CRITICAL |
| RANGE-002 | US2Y | -5.0 | 20.0 | CRITICAL |
| RANGE-003 | US5Y | -5.0 | 20.0 | CRITICAL |
| RANGE-004 | US10Y | -5.0 | 20.0 | CRITICAL |
| RANGE-005 | US30Y | -5.0 | 20.0 | CRITICAL |
| RANGE-006 | REAL_10Y | -10.0 | 15.0 | CRITICAL |
| RANGE-007 | CPI_YOY | -10.0 | 50.0 | CRITICAL |
| RANGE-008 | CPI_CORE_YOY | -5.0 | 40.0 | CRITICAL |
| RANGE-009 | PPI_YOY | -10.0 | 50.0 | CRITICAL |
| RANGE-010 | PPI_CORE_YOY | -10.0 | 50.0 | CRITICAL |
| RANGE-011 | PCE_YOY | -10.0 | 50.0 | CRITICAL |
| RANGE-012 | PCE_CORE_YOY | -10.0 | 50.0 | CRITICAL |
| RANGE-013 | NFP_CHANGE | -200.0 | 1000.0 | CRITICAL |
| RANGE-014 | UNRATE | 0.0 | 50.0 | CRITICAL |
| RANGE-015 | JOLTS_TOTAL | 0.0 | 12000.0 | CRITICAL |
| RANGE-016 | PMI_MFG | 20.0 | 80.0 | CRITICAL |
| RANGE-017 | PMI_SVC | 20.0 | 80.0 | CRITICAL |
| RANGE-018 | VIX | 10.0 | 200.0 | CRITICAL |
| RANGE-019 | MOVE | 50.0 | 500.0 | CRITICAL |

#### 2.3.3 Anomaly Detection

```python
class RangeValidator(BaseValidator):
    """
    Validates data values are within plausible ranges.
    """

    STAGE = "range"

    # Range definitions
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

    # Anomaly thresholds (n-sigma)
    ANOMALY_SIGMA = 3.0

    def validate(
        self,
        series: NormalizedSeries,
        evidence: EvidenceObject,
    ) -> StageResult:
        """
        Validate series value is within plausible range.
        """
        errors = []
        warnings = []

        if series.value is None:
            return StageResult(
                stage=self.STAGE,
                is_valid=True,
                is_critical=False,
                warnings=["Value is null (missing data)"],
            )

        # Check range
        valid_range = self.RANGES.get(series.series_id)
        if valid_range:
            min_val, max_val = valid_range
            if series.value < min_val:
                errors.append(
                    ValidationError(
                        rule_id=f"RANGE-{series.series_id}",
                        field="value",
                        value=series.value,
                        message=f"Value {series.value} below minimum {min_val}",
                        severity=Severity.CRITICAL,
                    )
                )
            elif series.value > max_val:
                errors.append(
                    ValidationError(
                        rule_id=f"RANGE-{series.series_id}",
                        field="value",
                        value=series.value,
                        message=f"Value {series.value} above maximum {max_val}",
                        severity=Severity.CRITICAL,
                    )
                )

        # Check for anomalies (sudden jumps)
        anomaly_result = self._check_anomaly(series)
        if anomaly_result:
            warnings.append(anomaly_result)

        return StageResult(
            stage=self.STAGE,
            is_valid=len([e for e in errors if e.severity == Severity.CRITICAL]) == 0,
            is_critical=len(errors) > 0,
            errors=[e.to_dict() for e in errors],
            warnings=[w.to_dict() for w in warnings],
        )

    def _check_anomaly(self, series: NormalizedSeries) -> dict | None:
        """
        Check for anomalous values using historical statistics.
        """
        # Get historical values for this series
        history = self._get_history(series.series_id, lookback_days=90)

        if len(history) < 10:
            return None

        # Calculate statistics
        values = [h.value for h in history if h.value is not None]
        if not values:
            return None

        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5

        if std == 0:
            return None

        # Check if current value is anomalous
        z_score = abs(series.value - mean) / std
        if z_score > self.ANOMALY_SIGMA:
            return ValidationError(
                rule_id="ANOMALY-001",
                field="value",
                value=series.value,
                message=f"Anomalous value: z-score={z_score:.2f} (threshold={self.ANOMALY_SIGMA})",
                severity=Severity.WARNING,
            ).to_dict()

        return None
```

### 2.4 Stage 3: Freshness Validator

**Version:** `validator/freshness/v1`
**Module:** `macro_intelligence.validation.freshness`
**Status:** Frozen

#### 2.4.1 Purpose

Validates that data is not stale and has been released within expected timeframes.

#### 2.4.2 Validation Rules

| Rule ID | Series | Max Staleness | Severity |
|---------|--------|---------------|----------|
| FRESH-001 | DXY | 1 day | CRITICAL |
| FRESH-002 | US10Y | 1 day | CRITICAL |
| FRESH-003 | VIX | 1 day | CRITICAL |
| FRESH-004 | CPI_YOY | 3 days after release | WARNING |
| FRESH-005 | NFP_CHANGE | 3 days after release | WARNING |
| FRESH-006 | GDP_YOY | 7 days after release | WARNING |
| FRESH-007 | All monthly | 15 days after month end | WARNING |

#### 2.4.3 Validator Implementation

```python
class FreshnessValidator(BaseValidator):
    """
    Validates data freshness against expected release schedules.
    """

    STAGE = "freshness"

    # Max staleness by series type (in days)
    MAX_STALENESS: dict[str, int] = {
        "DXY": 1,
        "US2Y": 1,
        "US5Y": 1,
        "US10Y": 1,
        "US30Y": 1,
        "REAL_10Y": 1,
        "VIX": 1,
        "MOVE": 1,
        "CPI_YOY": 3,
        "CPI_CORE_YOY": 3,
        "PPI_YOY": 3,
        "PPI_CORE_YOY": 3,
        "PCE_YOY": 3,
        "PCE_CORE_YOY": 3,
        "NFP_CHANGE": 3,
        "UNRATE": 3,
        "JOLTS_TOTAL": 7,
        "GDP_YOY": 7,
        "GDP_MOM": 7,
        "PMI_MFG": 7,
        "PMI_SVC": 7,
    }

    # Release schedules (day of month/quarter)
    RELEASE_SCHEDULE = {
        "CPI_YOY": {"monthly": 10, "time": "08:30"},
        "NFP_CHANGE": {"monthly": 1, "time": "08:30"},
        "GDP_YOY": {"quarterly": [25, 26, 27], "time": "08:30"},
        "PMI_MFG": {"monthly": 1, "time": "10:00"},
    }

    def validate(
        self,
        series: NormalizedSeries,
        evidence: EvidenceObject,
    ) -> StageResult:
        """
        Validate data freshness.
        """
        errors = []
        warnings = []

        # Check staleness
        staleness_days = self._calculate_staleness(series)
        max_stale = self.MAX_STALENESS.get(series.series_id, 7)

        if staleness_days > max_stale:
            errors.append(
                ValidationError(
                    rule_id="FRESH-001",
                    field="observation_period",
                    value=str(series.observation_period),
                    message=f"Data is stale: {staleness_days} days old (max: {max_stale})",
                    severity=Severity.CRITICAL,
                )
            )

        # Check release schedule compliance
        schedule_result = self._check_schedule(series, evidence)
        if schedule_result:
            warnings.append(schedule_result)

        return StageResult(
            stage=self.STAGE,
            is_valid=len(errors) == 0,
            is_critical=len([e for e in errors if e.severity == Severity.CRITICAL]) > 0,
            errors=[e.to_dict() for e in errors],
            warnings=[w.to_dict() for w in warnings],
        )

    def _calculate_staleness(self, series: NormalizedSeries) -> int:
        """Calculate days since observation period."""
        if series.observation_period:
            return (datetime.utcnow().date() - series.observation_period).days
        return 0

    def _check_schedule(
        self,
        series: NormalizedSeries,
        evidence: EvidenceObject,
    ) -> dict | None:
        """Check if data was released according to schedule."""
        schedule = self.RELEASE_SCHEDULE.get(series.series_id)
        if not schedule:
            return None

        # Check if release_time is within expected window
        if evidence.release_time:
            expected_date = self._get_expected_release_date(
                series.observation_period,
                schedule,
            )
            if expected_date:
                days_diff = abs((evidence.release_time.date() - expected_date).days)
                if days_diff > 2:
                    return ValidationError(
                        rule_id="FRESH-002",
                        field="release_time",
                        value=str(evidence.release_time),
                        message=f"Release delayed by {days_diff} days from expected",
                        severity=Severity.WARNING,
                    ).to_dict()

        return None
```

### 2.5 Stage 4: Revision Validator

**Version:** `validator/revision/v1`
**Module:** `macro_intelligence.validation.revision`
**Status:** Frozen

#### 2.5.1 Purpose

Validates revision chains and ensures historical integrity.

#### 2.5.2 Validation Rules

| Rule ID | Condition | Severity |
|---------|-----------|----------|
| REV-001 | Revision chain must be contiguous | CRITICAL |
| REV-002 | Revision timestamps must be ascending | CRITICAL |
| REV-003 | Revision value must differ from previous | WARNING |
| REV-004 | Original evidence must exist | CRITICAL |
| REV-005 | No circular references | CRITICAL |

#### 2.5.3 Validator Implementation

```python
class RevisionValidator(BaseValidator):
    """
    Validates revision chains for data integrity.
    """

    STAGE = "revision"

    def validate(
        self,
        series: NormalizedSeries,
        evidence: EvidenceObject,
    ) -> StageResult:
        """
        Validate revision chain integrity.
        """
        errors = []
        warnings = []

        # If no revision, nothing to validate
        if not evidence.revision:
            return StageResult(
                stage=self.STAGE,
                is_valid=True,
                is_critical=False,
            )

        # REV-001: Check revision chain continuity
        chain_result = self._validate_chain_continuity(evidence)
        if chain_result:
            errors.append(chain_result)

        # REV-002: Check timestamp ordering
        order_result = self._validate_timestamp_order(evidence)
        if order_result:
            errors.append(order_result)

        # REV-003: Check value change
        change_result = self._validate_value_change(evidence)
        if change_result:
            warnings.append(change_result)

        # REV-004: Check original evidence exists
        original_result = self._validate_original_exists(evidence)
        if original_result:
            errors.append(original_result)

        # REV-005: Check for circular references
        circular_result = self._check_circular_references(evidence)
        if circular_result:
            errors.append(circular_result)

        return StageResult(
            stage=self.STAGE,
            is_valid=len([e for e in errors if e.severity == Severity.CRITICAL]) == 0,
            is_critical=len(errors) > 0,
            errors=[e.to_dict() for e in errors],
            warnings=[w.to_dict() for w in warnings],
        )

    def _validate_chain_continuity(
        self,
        evidence: EvidenceObject,
    ) -> ValidationError | None:
        """Check that revision chain is contiguous."""
        chain = self._get_revision_chain(evidence.evidence_id)

        for i, rev in enumerate(chain):
            if i > 0:
                expected_num = chain[i - 1].revision_number + 1
                if rev.revision_number != expected_num:
                    return ValidationError(
                        rule_id="REV-001",
                        field="revision_chain",
                        value=str([r.revision_number for r in chain]),
                        message=f"Non-contiguous revision numbers: expected {expected_num}, got {rev.revision_number}",
                        severity=Severity.CRITICAL,
                    )
        return None

    def _validate_timestamp_order(
        self,
        evidence: EvidenceObject,
    ) -> ValidationError | None:
        """Check that revision timestamps are ascending."""
        chain = self._get_revision_chain(evidence.evidence_id)

        for i in range(1, len(chain)):
            if chain[i].revision_time <= chain[i - 1].revision_time:
                return ValidationError(
                    rule_id="REV-002",
                    field="revision_time",
                    value=str(chain[i].revision_time),
                    message="Revision timestamps not in ascending order",
                    severity=Severity.CRITICAL,
                )
        return None

    def _validate_value_change(
        self,
        evidence: EvidenceObject,
    ) -> ValidationError | None:
        """Check that revision value differs from original."""
        if evidence.revision and evidence.value == evidence.revision.original_value:
            return ValidationError(
                rule_id="REV-003",
                field="value",
                value=str(evidence.value),
                message="Revision value identical to original (no change)",
                severity=Severity.WARNING,
            )
        return None

    def _validate_original_exists(
        self,
        evidence: EvidenceObject,
    ) -> ValidationError | None:
        """Check that original evidence exists."""
        if evidence.revision:
            original = self._get_evidence(evidence.revision.original_evidence_id)
            if not original:
                return ValidationError(
                    rule_id="REV-004",
                    field="original_evidence_id",
                    value=evidence.revision.original_evidence_id,
                    message="Original evidence not found",
                    severity=Severity.CRITICAL,
                )
        return None

    def _check_circular_references(
        self,
        evidence: EvidenceObject,
    ) -> ValidationError | None:
        """Check for circular references in revision chain."""
        visited = set()
        current = evidence

        while current.revision:
            if current.evidence_id in visited:
                return ValidationError(
                    rule_id="REV-005",
                    field="revision_chain",
                    value=current.evidence_id,
                    message="Circular reference detected in revision chain",
                    severity=Severity.CRITICAL,
                )
            visited.add(current.evidence_id)
            current = self._get_evidence(current.revision.original_evidence_id)
            if not current:
                break

        return None
```

### 2.6 Stage 5: Cross-Source Reconciliation Validator

**Version:** `validator/cross_source/v1`
**Module:** `macro_intelligence.validation.cross_source`
**Status:** Frozen

#### 2.6.1 Purpose

Validates data consistency across multiple sources for the same series.

#### 2.6.2 Validation Rules

| Rule ID | Series Pairs | Tolerance | Severity |
|---------|-------------|-----------|----------|
| CROSS-001 | CPI (BLS vs FRED) | 0.1% | WARNING |
| CROSS-002 | Unemployment (BLS vs FRED) | 0.05% | WARNING |
| CROSS-003 | Treasury Yields (Treasury vs FRED) | 1 bp | WARNING |
| CROSS-004 | PPI (BLS vs FRED) | 0.1% | WARNING |

#### 2.6.3 Validator Implementation

```python
class CrossSourceValidator(BaseValidator):
    """
    Validates data consistency across multiple sources.
    """

    STAGE = "cross_source"

    # Tolerance levels for reconciliation
    TOLERANCES: dict[str, float] = {
        "CPI_YOY": 0.1,
        "UNRATE": 0.05,
        "US10Y": 0.01,  # 1 basis point
        "PPI_YOY": 0.1,
    }

    # Source pairs to compare
    COMPARISON_PAIRS = [
        ("CPI_YOY", ["bls", "fred"]),
        ("UNRATE", ["bls", "fred"]),
        ("US10Y", ["treasury", "fred"]),
        ("PPI_YOY", ["bls", "fred"]),
    ]

    def validate(
        self,
        series: NormalizedSeries,
        evidence: EvidenceObject,
    ) -> StageResult:
        """
        Validate cross-source consistency.
        """
        errors = []
        warnings = []

        # Only reconcile for series with multiple sources
        comparison = next(
            (c for c in self.COMPARISON_PAIRS if c[0] == series.series_id),
            None,
        )

        if not comparison:
            return StageResult(
                stage=self.STAGE,
                is_valid=True,
                is_critical=False,
            )

        series_id, source_list = comparison
        tolerance = self.TOLERANCES.get(series_id, 0.1)

        # Get values from all sources
        values = {}
        for source in source_list:
            source_evidence = self._get_evidence_for_series(
                series_id,
                source,
                evidence.observation_time.date(),
            )
            if source_evidence and source_evidence.value is not None:
                values[source] = source_evidence.value

        # Reconcile if we have multiple sources
        if len(values) >= 2:
            reconciliation_result = self._reconcile(values, tolerance)
            if reconciliation_result:
                warnings.append(reconciliation_result)

        return StageResult(
            stage=self.STAGE,
            is_valid=True,  # Cross-source issues are warnings, not failures
            is_critical=False,
            warnings=[w.to_dict() for w in warnings] if isinstance(warnings[0], ValidationError) else warnings,
        )

    def _reconcile(
        self,
        values: dict[str, float],
        tolerance: float,
    ) -> ValidationError | None:
        """
        Reconcile values from multiple sources.
        """
        if len(values) < 2:
            return None

        # Calculate average
        avg = sum(values.values()) / len(values)

        # Check each source against average
        for source, value in values.items():
            diff = abs(value - avg)
            if diff > tolerance:
                return ValidationError(
                    rule_id="CROSS-001",
                    field=f"{source}_value",
                    value=str(value),
                    message=f"Source {source} differs from average by {diff:.4f} (tolerance: {tolerance})",
                    severity=Severity.WARNING,
                )

        return None
```

---

## 3. Quality Score Engine

### 3.1 Score Engine Architecture

**Version:** `score/v1`
**Module:** `macro_intelligence.quality.score`
**Status:** Frozen

### 3.2 Score Components

```python
@dataclass(frozen=True)
class QualityScores:
    """
    Composite quality scores for a data observation.
    """

    source_reliability: float  # 0.0-1.0
    completeness: float  # 0.0-1.0
    freshness: float  # 0.0-1.0
    anomaly: float  # 0.0-1.0
    composite: float  # 0.0-1.0 (weighted average)

    def to_dict(self) -> dict:
        return {
            "source_reliability": round(self.source_reliability, 3),
            "completeness": round(self.completeness, 3),
            "freshness": round(self.freshness, 3),
            "anomaly": round(self.anomaly, 3),
            "composite": round(self.composite, 3),
        }


class QualityScoreEngine:
    """
    Computes quality scores for validated data.
    """

    # Weight defaults
    WEIGHTS = {
        "source_reliability": 0.3,
        "completeness": 0.2,
        "freshness": 0.2,
        "anomaly": 0.3,
    }

    def compute_scores(
        self,
        series: NormalizedSeries,
        evidence: EvidenceObject,
        validation_result: ValidationResult,
    ) -> QualityScores:
        """
        Compute quality scores for a data observation.

        Returns:
            QualityScores with all component scores
        """
        source_reliability = self._compute_source_reliability(evidence.source)
        completeness = self._compute_completeness(series, evidence)
        freshness = self._compute_freshness(series, evidence)
        anomaly = self._compute_anomaly_score(series, validation_result)

        composite = self._compute_composite(
            source_reliability,
            completeness,
            freshness,
            anomaly,
        )

        return QualityScores(
            source_reliability=source_reliability,
            completeness=completeness,
            freshness=freshness,
            anomaly=anomaly,
            composite=composite,
        )

    def _compute_source_reliability(self, source: str) -> float:
        """
        Compute source reliability score.

        Based on:
        - Source type reputation
        - Historical accuracy
        - Data timeliness
        """
        source_scores = {
            "fred": 0.95,
            "bls": 0.95,
            "treasury": 0.98,
            "cboe": 0.90,
            "cftc": 0.85,
            "federal_reserve": 0.92,
            "ism": 0.88,
        }
        return source_scores.get(source, 0.70)

    def _compute_completeness(
        self,
        series: NormalizedSeries,
        evidence: EvidenceObject,
    ) -> float:
        """
        Compute completeness score.

        Based on:
        - Required fields present
        - No missing values
        - Full provenance
        """
        score = 1.0
        deductions = 0.1

        # Check required fields
        if not series.series_id:
            score -= deductions
        if not series.source:
            score -= deductions
        if not series.timestamp:
            score -= deductions
        if series.value is None:
            score -= deductions * 2  # Missing value is bigger deduction

        # Check provenance
        if not evidence.provenance.original_source:
            score -= deductions
        if not evidence.provenance.ingestion_pipeline:
            score -= deductions

        return max(0.0, score)

    def _compute_freshness(
        self,
        series: NormalizedSeries,
        evidence: EvidenceObject,
    ) -> float:
        """
        Compute freshness score.

        Based on:
        - Time since observation period
        - Time since release
        """
        if series.value is None:
            return 0.0

        # Days since observation
        obs_days_old = (datetime.utcnow().date() - series.observation_period).days

        # Score decreases with age
        if obs_days_old <= 1:
            return 1.0
        elif obs_days_old <= 7:
            return 0.9
        elif obs_days_old <= 30:
            return 0.7
        elif obs_days_old <= 90:
            return 0.5
        else:
            return 0.3

    def _compute_anomaly_score(
        self,
        series: NormalizedSeries,
        validation_result: ValidationResult,
    ) -> float:
        """
        Compute anomaly score based on validation warnings.
        """
        score = 1.0
        deductions = 0.2

        # Check for anomalies in validation
        for stage_result in validation_result.stages:
            for warning in stage_result.warnings:
                if "anomaly" in warning.get("message", "").lower():
                    score -= deductions

        return max(0.0, score)

    def _compute_composite(
        self,
        source_reliability: float,
        completeness: float,
        freshness: float,
        anomaly: float,
    ) -> float:
        """
        Compute weighted composite score.
        """
        weights = self.WEIGHTS
        composite = source_reliability * weights["source_reliability"] + completeness * weights["completeness"] + freshness * weights["freshness"] + anomaly * weights["anomaly"]
        return round(composite, 3)
```

### 3.3 Quality Score Interpretation

| Composite Score | Rating | Action |
|----------------|--------|--------|
| 0.9 - 1.0 | Excellent | Store immediately |
| 0.7 - 0.9 | Good | Store with logging |
| 0.5 - 0.7 | Fair | Store with warning |
| 0.3 - 0.5 | Poor | Quarantine for review |
| 0.0 - 0.3 | Critical | Reject and alert |

---

## 4. Quarantine System

### 4.1 Quarantine Record Schema

**Version:** `quarantine/v1`
**Module:** `macro_intelligence.quarantine.record`
**Status:** Frozen

```python
@dataclass(frozen=True)
class QuarantineRecord:
    """
    Record of quarantined data with full context.
    """

    quarantine_id: str  # QUAR_{timestamp}_{hash}
    series_id: str
    evidence_id: str
    original_record: dict  # Original NormalizedSeries
    validation_failures: list[dict]  # Failed validation stages
    quality_score: float  # Composite quality score
    quarantined_at: datetime  # When quarantined
    quarantined_by: str  # System or user
    reason: str  # Human-readable reason
    metadata: dict  # Additional context
    status: QuarantineStatus = QuarantineStatus.PENDING

    def to_dict(self) -> dict:
        return {
            "quarantine_id": self.quarantine_id,
            "series_id": self.series_id,
            "evidence_id": self.evidence_id,
            "original_record": self.original_record,
            "validation_failures": self.validation_failures,
            "quality_score": self.quality_score,
            "quarantined_at": self.quarantined_at.isoformat(),
            "quarantined_by": self.quarantined_by,
            "reason": self.reason,
            "metadata": self.metadata,
            "status": self.status.value,
        }


class QuarantineStatus(Enum):
    PENDING = "pending"  # Awaiting review
    UNDER_REVIEW = "under_review"  # Being investigated
    RELEASED = "released"  # Approved for storage
    REJECTED = "rejected"  # Confirmed invalid
    ARCHIVED = "archived"  # Older quarantine records
```

### 4.2 Quarantine Manager

**Version:** `quarantine/manager/v1`
**Module:** `macro_intelligence.quarantine.manager`
**Status:** Frozen

```python
class QuarantineManager:
    """
    Manages quarantined data with full workflow support.
    """

    def __init__(self, storage: BaseStore):
        self.storage = storage
        self._lock = threading.Lock()

    def quarantine(
        self,
        series: NormalizedSeries,
        evidence: EvidenceObject,
        validation_result: ValidationResult,
        quality_scores: QualityScores,
    ) -> QuarantineRecord:
        """
        Quarantine invalid data with full context.

        Returns:
            QuarantineRecord with unique ID
        """
        with self._lock:
            quarantine_id = self._generate_id()

            record = QuarantineRecord(
                quarantine_id=quarantine_id,
                series_id=series.series_id,
                evidence_id=evidence.evidence_id,
                original_record=series.to_dict(),
                validation_failures=[
                    {
                        "stage": stage.stage,
                        "errors": stage.errors,
                        "warnings": stage.warnings,
                    }
                    for stage in validation_result.stages
                    if not stage.is_valid
                ],
                quality_score=quality_scores.composite,
                quarantined_at=datetime.utcnow(),
                quarantined_by="system",
                reason=self._generate_reason(validation_result),
                metadata={
                    "source": evidence.source,
                    "observation_period": str(series.observation_period),
                    "value": series.value,
                },
            )

            # Store quarantine record
            self.storage.write_quarantine(quarantine_id, record)

            # Log to audit
            self._audit_quarantine(quarantine_id, series.series_id)

            # Trigger alert if critical
            if quality_scores.composite < 0.3:
                self._alert_critical(quarantine_id, record)

            return record

    def release(
        self,
        quarantine_id: str,
        reviewer: str,
        notes: str = "",
    ) -> bool:
        """
        Release quarantined data for storage.

        Returns:
            True if successfully released
        """
        with self._lock:
            record = self.storage.read_quarantine(quarantine_id)
            if not record:
                return False

            # Update status
            record.status = QuarantineStatus.RELEASED
            record.metadata["released_by"] = reviewer
            record.metadata["release_notes"] = notes
            record.metadata["released_at"] = datetime.utcnow().isoformat()

            # Re-validate before release
            if not self._revalidate(record):
                record.status = QuarantineStatus.REJECTED
                self.storage.write_quarantine(quarantine_id, record)
                return False

            # Move to storage
            series = NormalizedSeries.from_dict(record.original_record)
            self.storage.write_series(series)

            # Update quarantine record
            self.storage.write_quarantine(quarantine_id, record)

            # Log
            self._audit_release(quarantine_id, reviewer)

            return True

    def reject(
        self,
        quarantine_id: str,
        reviewer: str,
        reason: str,
    ) -> bool:
        """
        Permanently reject quarantined data.

        Returns:
            True if successfully rejected
        """
        with self._lock:
            record = self.storage.read_quarantine(quarantine_id)
            if not record:
                return False

            record.status = QuarantineStatus.REJECTED
            record.metadata["rejected_by"] = reviewer
            record.metadata["rejection_reason"] = reason
            record.metadata["rejected_at"] = datetime.utcnow().isoformat()

            self.storage.write_quarantine(quarantine_id, record)
            self._audit_reject(quarantine_id, reviewer, reason)

            return True

    def _revalidate(self, record: QuarantineRecord) -> bool:
        """Re-validate quarantined data."""
        series = NormalizedSeries.from_dict(record.original_record)
        pipeline = ValidationPipeline(
            validators=[
                SchemaValidator(),
                RangeValidator(),
                FreshnessValidator(),
                RevisionValidator(),
                CrossSourceValidator(),
            ]
        )
        result = pipeline.validate(series, None)
        return result.is_valid

    def _generate_id(self) -> str:
        """Generate unique quarantine ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique = uuid.uuid4().hex[:8]
        return f"QUAR_{timestamp}_{unique}"

    def _generate_reason(self, result: ValidationResult) -> str:
        """Generate human-readable quarantine reason."""
        critical_errors = []
        for stage in result.stages:
            for error in stage.errors:
                if error.get("severity") == "CRITICAL":
                    critical_errors.append(error.get("message"))

        if critical_errors:
            return "; ".join(critical_errors[:3])
        return "Quality score below threshold"
```

### 4.3 Quarantine Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   QUARANTINE │────►│  PENDING    │────►│  REVIEW     │
│   CREATED    │     │  QUEUE      │     │             │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                              ┌────────────────┼────────────────┐
                              │                │                │
                              ▼                ▼                ▼
                        ┌──────────┐   ┌──────────┐   ┌──────────┐
                        │ RELEASED │   │ REJECTED │   │ ARCHIVED │
                        │ (stored) │   │ (logged) │   │ (>90d)   │
                        └──────────┘   └──────────┘   └──────────┘
```

---

## 5. Alert System Contract

### 5.1 Alert Schema

**Version:** `alert/v1`
**Module:** `macro_intelligence.alerts.contract`
**Status:** Frozen

```python
@dataclass(frozen=True)
class Alert:
    """
    Standardized alert object for quality issues.
    """

    alert_id: str  # ALRT_{timestamp}_{hash}
    alert_type: AlertType  # WARNING, CRITICAL, OUTAGE
    severity: Severity  # LOW, MEDIUM, HIGH, CRITICAL
    source_type: str  # Which source triggered
    series_id: str | None  # Which series (if applicable)
    title: str  # Brief title
    description: str  # Detailed description
    metadata: dict  # Additional context
    triggered_at: datetime  # When alert was created
    acknowledged: bool = False
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "source_type": self.source_type,
            "series_id": self.series_id,
            "title": self.title,
            "description": self.description,
            "metadata": self.metadata,
            "triggered_at": self.triggered_at.isoformat(),
            "acknowledged": self.acknowledged,
        }


class AlertType(Enum):
    WARNING = "warning"  # Non-critical issue
    CRITICAL = "critical"  # Serious data quality issue
    SOURCE_OUTAGE = "source_outage"  # Source unavailable


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

### 5.2 Alert Manager

**Version:** `alert/manager/v1`
**Module:** `macro_intelligence.alerts.manager`
**Status:** Frozen

```python
class AlertManager:
    """
    Manages alerts for data quality issues.
    """

    def __init__(self, storage: BaseStore, notifier: AlertNotifier):
        self.storage = storage
        self.notifier = notifier
        self._alerts: dict[str, Alert] = {}
        self._lock = threading.Lock()

    def create_alert(
        self,
        alert_type: AlertType,
        severity: Severity,
        source_type: str,
        series_id: str | None,
        title: str,
        description: str,
        metadata: dict | None = None,
    ) -> Alert:
        """
        Create and store a new alert.

        Returns:
            Created Alert object
        """
        alert_id = self._generate_alert_id()

        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            source_type=source_type,
            series_id=series_id,
            title=title,
            description=description,
            metadata=metadata or {},
            triggered_at=datetime.utcnow(),
        )

        with self._lock:
            self._alerts[alert_id] = alert
            self.storage.write_alert(alert_id, alert)

        # Notify based on severity
        if severity in (Severity.HIGH, Severity.CRITICAL):
            self.notifier.notify(alert)

        return alert

    def acknowledge(self, alert_id: str, user: str) -> bool:
        """
        Acknowledge an alert.

        Returns:
            True if successful
        """
        with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert:
                return False

            alert.acknowledged = True
            alert.acknowledged_by = user
            alert.acknowledged_at = datetime.utcnow()

            self.storage.write_alert(alert_id, alert)
            return True

    def get_unacknowledged(self, severity: Severity | None = None) -> list[Alert]:
        """
        Get unacknowledged alerts, optionally filtered by severity.
        """
        with self._lock:
            alerts = list(self._alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity and not a.acknowledged]
        else:
            alerts = [a for a in alerts if not a.acknowledged]

        return sorted(alerts, key=lambda a: a.triggered_at, reverse=True)

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique = uuid.uuid4().hex[:8]
        return f"ALRT_{timestamp}_{unique}"
```

### 5.3 Alert Triggers

| Trigger Condition | Alert Type | Severity | Action |
|------------------|------------|----------|--------|
| Validation failure (critical) | CRITICAL | HIGH | Quarantine + Notify |
| Quality score < 0.3 | CRITICAL | HIGH | Quarantine + Notify |
| Source health degraded | WARNING | MEDIUM | Log + Monitor |
| Source health unhealthy | SOURCE_OUTAGE | CRITICAL | Alert + Retry Backoff |
| 5+ consecutive failures | SOURCE_OUTAGE | CRITICAL | Circuit Breaker + Alert |
| Rapid failure rate (>5/min) | SOURCE_OUTAGE | CRITICAL | Alert + Emergency Backoff |
| Stale data detected | WARNING | MEDIUM | Log + Alert |
| Cross-source mismatch | WARNING | LOW | Log + Flag |

---

## 6. Quality Dashboard

### 6.1 Dashboard Metrics

```python
@dataclass
class QualityMetrics:
    """
    Aggregated quality metrics for dashboard display.
    """

    # Volume metrics
    total_records: int
    validated_records: int
    quarantined_records: int
    rejected_records: int

    # Quality scores
    avg_source_reliability: float
    avg_completeness: float
    avg_freshness: float
    avg_anomaly: float
    avg_composite: float

    # Validation stats
    schema_failures: int
    range_failures: int
    freshness_failures: int
    revision_failures: int
    cross_source_failures: int

    # Alert stats
    open_warnings: int
    open_criticals: int
    source_outages: int

    # Timestamp
    last_updated: datetime

    def to_dict(self) -> dict:
        return {
            "total_records": self.total_records,
            "validated_records": self.validated_records,
            "quarantined_records": self.quarantined_records,
            "rejected_records": self.rejected_records,
            "avg_source_reliability": round(self.avg_source_reliability, 3),
            "avg_completeness": round(self.avg_completeness, 3),
            "avg_freshness": round(self.avg_freshness, 3),
            "avg_anomaly": round(self.avg_anomaly, 3),
            "avg_composite": round(self.avg_composite, 3),
            "schema_failures": self.schema_failures,
            "range_failures": self.range_failures,
            "freshness_failures": self.freshness_failures,
            "revision_failures": self.revision_failures,
            "cross_source_failures": self.cross_source_failures,
            "open_warnings": self.open_warnings,
            "open_criticals": self.open_criticals,
            "source_outages": self.source_outages,
            "last_updated": self.last_updated.isoformat(),
        }
```

### 6.2 Dashboard Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/quality/metrics` | GET | Get current quality metrics |
| `/quality/quarantine` | GET | List quarantined records |
| `/quality/quarantine/{id}` | GET | Get quarantine record details |
| `/quality/quarantine/{id}/release` | POST | Release quarantine record |
| `/quality/quarantine/{id}/reject` | POST | Reject quarantine record |
| `/quality/alerts` | GET | Get open alerts |
| `/quality/alerts/{id}/acknowledge` | POST | Acknowledge alert |
| `/quality/sources` | GET | Get source health status |

---

## 7. Compliance & Audit

### 7.1 Audit Log Format

```jsonl
# Quality audit log format
{"action": "validate", "series_id": "US10Y", "timestamp": "2026-08-03T12:00:00Z", "result": "PASS", "quality_score": 0.95, "validation_stages": ["schema", "range", "freshness"]}
{"action": "quarantine", "series_id": "CPI_YOY", "timestamp": "2026-08-03T12:05:00Z", "quarantine_id": "QUAR_20260803_001", "reason": "Value 55.2 exceeds max 50.0", "quality_score": 0.25}
{"action": "release", "series_id": "CPI_YOY", "timestamp": "2026-08-03T12:10:00Z", "quarantine_id": "QUAR_20260803_001", "reviewer": "analyst_01", "result": "APPROVED"}
{"action": "alert", "alert_id": "ALRT_20260803_001", "timestamp": "2026-08-03T12:15:00Z", "type": "SOURCE_OUTAGE", "source": "fred", "severity": "CRITICAL"}
```

### 7.2 Audit Retention

| Data Type | Retention Period | Storage Format |
|-----------|-----------------|----------------|
| Audit logs | Indefinite | JSONL (compressed) |
| Quarantine records | 90 days | JSON + Parquet |
| Alert history | 1 year | JSON |
| Quality metrics | 5 years | Parquet |

### 7.3 Compliance Checks

```python
class ComplianceChecker:
    """
    Ensures data quality practices meet compliance requirements.
    """

    def verify_data_integrity(self) -> ComplianceResult:
        """
        Verify all stored data passes quality checks.
        """
        return ComplianceResult(
            is_compliant=self._check_all_stored_data(),
            violations=self._find_violations(),
            last_check=datetime.utcnow(),
        )

    def verify_audit_trail(self) -> ComplianceResult:
        """
        Verify audit trail is complete and unbroken.
        """
        return ComplianceResult(
            is_compliant=self._check_audit_completeness(),
            violations=self._find_audit_gaps(),
            last_check=datetime.utcnow(),
        )

    def verify_quarantine_workflow(self) -> ComplianceResult:
        """
        Verify quarantine workflow compliance.
        """
        return ComplianceResult(
            is_compliant=self._check_quarantine_procedures(),
            violations=self._find_quarantine_violations(),
            last_check=datetime.utcnow(),
        )
```

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1)

- [ ] Implement BaseValidator interface
- [ ] Create SchemaValidator
- [ ] Create RangeValidator
- [ ] Set up test fixtures

### Phase 2: Core Pipeline (Week 2)

- [ ] Implement ValidationPipeline
- [ ] Create FreshnessValidator
- [ ] Create RevisionValidator
- [ ] Create CrossSourceValidator
- [ ] Integration testing

### Phase 3: Quality Scoring (Week 3)

- [ ] Implement QualityScoreEngine
- [ ] Define score weights and thresholds
- [ ] Create QualityMetrics aggregation
- [ ] Dashboard API endpoints

### Phase 4: Quarantine System (Week 4)

- [ ] Implement QuarantineManager
- [ ] Create quarantine storage
- [ ] Implement release/reject workflow
- [ ] Audit logging

### Phase 5: Alert System (Week 5)

- [ ] Implement AlertManager
- [ ] Create alert triggers
- [ ] Integrate with notification system
- [ ] Alert acknowledgment workflow

### Phase 6: Hardening (Week 6)

- [ ] Performance testing
- [ ] Compliance verification
- [ ] Documentation
- [ ] Production deployment

---

## Final Declaration

---

**Macro Intelligence Layer Data Quality Engine Architecture is architecturally frozen and ready for implementation.**

All quality contracts are versioned, immutable, and audit-ready. The architecture ensures:
- Zero silent data corruption
- Complete validation pipeline with 5 stages
- Transparent quality scoring with 4 components
- Robust quarantine system with full workflow
- Comprehensive alert system for all severity levels

**Next Step:** Begin Phase 1 implementation — create the BaseValidator interface and SchemaValidator.

---

*Document Version: 1.0.0-frozen*
*Last Updated: 2026-08-03*
*Classification: Internal — Quantitative Platform Architecture*
