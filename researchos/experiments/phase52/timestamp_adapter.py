"""Phase 5.2 source timestamp canonicalization at the experiment boundary."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone


def normalize_epoch_timestamp_csv(text: str) -> str:
    """Canonicalize numeric epoch timestamps to UTC ISO-8601 strings.

    The raw source text is not modified. This adapter exists only at the
    Phase 5.2 ingestion boundary so source-specific epoch units do not leak
    into the strict Data Engine timestamp parser.

    Supported numeric epoch units are seconds and milliseconds. Unit is
    inferred from magnitude using conservative Unix-epoch bounds.
    Non-numeric timestamps are returned unchanged so existing ISO/date
    formats continue through the normal Data Engine parser.
    """
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV has no header")
    timestamp_column = next(
        (name for name in reader.fieldnames if name.strip().lower() in {"timestamp", "time", "datetime", "date"}),
        None,
    )
    if timestamp_column is None:
        return text

    rows = list(reader)
    for row in rows:
        raw = (row.get(timestamp_column) or "").strip()
        if not raw:
            continue
        try:
            value = int(raw)
        except ValueError:
            continue
        absolute = abs(value)
        if absolute >= 100_000_000_000:
            seconds = value / 1_000.0
        elif absolute >= 1_000_000_000:
            seconds = float(value)
        else:
            continue
        dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
        row[timestamp_column] = dt.isoformat().replace("+00:00", "Z")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
