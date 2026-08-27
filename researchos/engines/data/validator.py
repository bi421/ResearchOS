"""
DatasetValidator â€” validate market data integrity and quality.

Based on Article XVII: Object Model â€” Data Layer.

The DatasetValidator performs comprehensive validation of market data
including schema checks, data type validation, range checks, gap
detection, missing candle detection, duplicate detection, and
outlier identification.

Guarantees:
    - Deterministic: Same data â†’ same validation results
    - Auditable: Full validation report with all findings
    - Configurable: Validation strictness can be adjusted
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from researchos.engines.data.candle import Candle
from researchos.engines.data.contracts import Timeframe, ValidationReport


class GapDetector:
    """
    Detect gaps in time-series market data.

    A gap is defined as a time interval between consecutive records
    that exceeds the expected interval by a configurable tolerance.
    """

    def __init__(self, tolerance_factor: float = 2.0):
        """
        Args:
            tolerance_factor: Factor above expected interval to classify as gap.
                              Default 2.0 means any gap > 2x expected is reported.
        """
        self.tolerance_factor = tolerance_factor

    def detect(self, records: List[Any], timeframe: str) -> List[Dict[str, Any]]:
        """
        Detect gaps in a list of time-series records.

        Args:
            records: List of records with a 'timestamp' attribute.
            timeframe: The expected timeframe (e.g., "1h", "1d").

        Returns:
            List of gap dicts with 'start', 'end', 'expected_time', and 'gap_seconds'.
        """
        if len(records) < 2:
            return []

        try:
            expected_seconds = Timeframe.from_string(timeframe).to_seconds()
        except ValueError:
            expected_seconds = 3600  # default to 1h

        if expected_seconds == 0:
            return []  # No expected interval for tick data

        gaps: List[Dict[str, Any]] = []
        tolerance = expected_seconds * self.tolerance_factor

        for i in range(1, len(records)):
            prev = records[i - 1]
            curr = records[i]

            if not hasattr(prev, "timestamp") or not hasattr(curr, "timestamp"):
                continue

            delta = (curr.timestamp - prev.timestamp).total_seconds()

            if delta > tolerance:
                expected_count = round(delta / expected_seconds) - 1
                gaps.append(
                    {
                        "start": prev.timestamp.isoformat(),
                        "end": curr.timestamp.isoformat(),
                        "gap_seconds": delta,
                        "expected_seconds": expected_seconds,
                        "expected_missing": expected_count,
                        "index": i,
                    }
                )

        return gaps


class MissingCandleDetector:
    """
    Detect missing candles in a time-series based on expected intervals.

    Unlike GapDetector which finds large gaps, this detector identifies
    individual missing periods at the expected interval granularity.
    """

    def __init__(self, tolerance_seconds: int = 60):
        """
        Args:
            tolerance_seconds: Allowed tolerance when matching expected timestamps.
        """
        self.tolerance_seconds = tolerance_seconds

    def detect(self, records: List[Any], timeframe: str) -> List[datetime]:
        """
        Detect missing timestamps in a list of time-series records.

        Args:
            records: Chronologically sorted records with 'timestamp' attribute.
            timeframe: The expected timeframe.

        Returns:
            List of missing datetime objects.
        """
        if len(records) < 2:
            return []

        try:
            expected_seconds = Timeframe.from_string(timeframe).to_seconds()
        except ValueError:
            return []

        if expected_seconds == 0:
            return []

        missing: List[datetime] = []
        for i in range(1, len(records)):
            prev = records[i - 1]
            curr = records[i]

            if not hasattr(prev, "timestamp") or not hasattr(curr, "timestamp"):
                continue

            current = prev.timestamp + timedelta(seconds=expected_seconds)
            while current < curr.timestamp - timedelta(seconds=self.tolerance_seconds):
                missing.append(current)
                current += timedelta(seconds=expected_seconds)

        return missing


class DuplicateDetector:
    """
    Detect duplicate records in market data.

    Duplicates are records with identical timestamps (within tolerance)
    for the same symbol.
    """

    def __init__(self, tolerance_seconds: int = 0):
        """
        Args:
            tolerance_seconds: Tolerance for considering timestamps as duplicates.
        """
        self.tolerance_seconds = tolerance_seconds

    def detect(self, records: List[Any]) -> List[Tuple[int, int, str]]:
        """
        Detect duplicate records.

        Args:
            records: List of records with 'timestamp' and 'symbol' attributes.

        Returns:
            List of (index1, index2, reason) tuples identifying duplicates.
        """
        duplicates: List[Tuple[int, int, str]] = []
        seen: Dict[str, int] = {}

        for i, record in enumerate(records):
            key = self._record_key(record)
            if key in seen:
                duplicates.append((seen[key], i, f"Duplicate key: {key}"))
            else:
                seen[key] = i

        return duplicates

    def _record_key(self, record: Any) -> str:
        """Generate a unique key for duplicate detection."""
        ts = record.timestamp.isoformat() if hasattr(record, "timestamp") else ""
        symbol = getattr(record, "symbol", "")
        return f"{symbol}|{ts}"


class OutlierDetector:
    """
    Detect outlier records using statistical methods.

    Uses z-score and IQR methods to identify price and volume outliers.
    """

    def __init__(self, z_score_threshold: float = 3.0, iqr_multiplier: float = 1.5):
        self.z_score_threshold = z_score_threshold
        self.iqr_multiplier = iqr_multiplier

    def detect_price_outliers(self, records: List[Candle]) -> List[int]:
        """
        Detect price outliers using z-score method.

        Args:
            records: List of Candle objects.

        Returns:
            List of indices of outlier records.
        """
        if len(records) < 4:
            return []

        prices = [c.close for c in records]
        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        std = variance**0.5

        if std == 0:
            return []

        outliers: List[int] = []
        for i, p in enumerate(prices):
            z = abs(p - mean) / std
            if z > self.z_score_threshold:
                outliers.append(i)

        return outliers

    def detect_volume_outliers(self, records: List[Candle]) -> List[int]:
        """
        Detect volume outliers using IQR method.

        Args:
            records: List of Candle objects.

        Returns:
            List of indices of outlier records.
        """
        if len(records) < 4:
            return []

        volumes = [c.volume for c in records]
        sorted_v = sorted(volumes)
        q1 = sorted_v[len(sorted_v) // 4]
        q3 = sorted_v[3 * len(sorted_v) // 4]
        iqr = q3 - q1

        if iqr == 0:
            return []

        lower = q1 - self.iqr_multiplier * iqr
        upper = q3 + self.iqr_multiplier * iqr

        outliers: List[int] = []
        for i, v in enumerate(volumes):
            if v < lower or v > upper:
                outliers.append(i)

        return outliers


class DatasetValidator:
    """
    Comprehensive validator for market datasets.

    Combines gap detection, missing candle detection, duplicate detection,
    and outlier detection into a single validation pipeline.
    """

    def __init__(
        self,
        gap_tolerance: float = 2.0,
        duplicate_tolerance: int = 0,
        z_score_threshold: float = 3.0,
    ):
        self.gap_detector = GapDetector(tolerance_factor=gap_tolerance)
        self.missing_detector = MissingCandleDetector()
        self.duplicate_detector = DuplicateDetector(tolerance_seconds=duplicate_tolerance)
        self.outlier_detector = OutlierDetector(z_score_threshold=z_score_threshold)

    def validate(
        self,
        records: List[Any],
        timeframe: str,
        symbol: str = "",
    ) -> ValidationReport:
        """
        Validate a list of data records.

        Args:
            records: List of records to validate.
            timeframe: The expected timeframe.
            symbol: Optional symbol for reporting.

        Returns:
            ValidationReport with all findings.
        """
        report = ValidationReport()
        report.total_records = len(records)

        # Sort records chronologically
        sorted_records = sorted(
            records,
            key=lambda r: r.timestamp if hasattr(r, "timestamp") else datetime.min,
        )

        # Basic validation
        valid = 0
        invalid = 0
        for record in sorted_records:
            if self._validate_record(record):
                valid += 1
            else:
                invalid += 1

        report.valid_records = valid
        report.invalid_records = invalid

        # Gap detection
        gaps = self.gap_detector.detect(sorted_records, timeframe)
        report.gaps_found = len(gaps)
        for gap in gaps:
            report.warnings.append(
                f"Gap at index {gap['index']}: {gap['gap_seconds']}s "
                f"({gap['expected_missing']} expected records)"
            )

        # Missing candle detection
        missing = self.missing_detector.detect(sorted_records, timeframe)
        report.missing_candles = len(missing)

        # Duplicate detection
        duplicates = self.duplicate_detector.detect(sorted_records)
        report.duplicates_found = len(duplicates)
        for idx1, idx2, reason in duplicates[:10]:
            report.errors.append(f"Duplicate at indices {idx1}, {idx2}: {reason}")

        # Outlier detection (candles only)
        if sorted_records and isinstance(sorted_records[0], Candle):
            candles = [r for r in sorted_records if isinstance(r, Candle)]
            price_outliers = self.outlier_detector.detect_price_outliers(candles)
            volume_outliers = self.outlier_detector.detect_volume_outliers(candles)
            report.outlier_records = len(set(price_outliers + volume_outliers))

        return report

    def _validate_record(self, record: Any) -> bool:
        """Validate a single data record."""
        # Check for timestamp
        if not hasattr(record, "timestamp") or record.timestamp is None:
            return False

        # Check for non-negative prices
        if hasattr(record, "price") and record.price < 0:
            return False

        # Check OHLCV consistency for candles
        if isinstance(record, Candle):
            if record.open <= 0 or record.high <= 0 or record.low <= 0 or record.close <= 0:
                return False
            if record.high < record.low:
                return False
            if record.high < record.open or record.high < record.close:
                return False
            if record.low > record.open or record.low > record.close:
                return False
            if record.volume < 0:
                return False

        return True
