"""
Dataset Builder — export / serialization.

Pure standard-library serialization helpers for ``ResearchDataset``.

    * ``to_dict``  — plain dictionary representation.
    * ``to_json``  — deterministic JSON string (``sort_keys=True``).
    * ``to_csv``   — CSV string using the ``csv`` module.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List

from .dataset_contracts import ResearchDataset


def to_dict(dataset: ResearchDataset) -> Dict[str, Any]:
    """Return a plain dictionary representation of ``dataset``."""
    return {
        "feature_names": list(dataset.feature_names),
        "features": [list(row) for row in dataset.features],
        "labels": list(dataset.labels),
        "metadata": dict(dataset.metadata),
        "sample_count": dataset.sample_count,
        "feature_count": dataset.feature_count,
        "label_name": dataset.label_name,
        "created_at": dataset.created_at,
        "version": dataset.version,
    }


def to_json(dataset: ResearchDataset) -> str:
    """Return a deterministic JSON string for ``dataset``."""
    return json.dumps(to_dict(dataset), sort_keys=True)


def to_csv(dataset: ResearchDataset) -> str:
    """Return a CSV string for ``dataset``.

    The header row is ``feature_names`` followed by ``label_name``.  Each
    following row contains the feature values and the corresponding label.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    header: List[Any] = list(dataset.feature_names) + [dataset.label_name]
    writer.writerow(header)
    for i, row in enumerate(dataset.features):
        writer.writerow(list(row) + [dataset.labels[i]])
    return buffer.getvalue()


__all__ = ["to_csv", "to_dict", "to_json"]
