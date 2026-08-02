"""
Deterministic identity generation for ResearchOS.

Implements deterministic UUID generation and content hashing.
Based on Article XVII: Object Model — all objects use deterministic IDs.

Determinism Guarantee:
    Given the same inputs, generate_id() always produces the same output.
    This ensures reproducibility across all ResearchOS operations.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any


def generate_id(seed: str) -> str:
    """
    Generate a deterministic UUID from a seed string.

    The UUID is deterministic (same seed → same UUID).
    A seed is required — ResearchOS does not allow random identity generation.

    Args:
        seed: Seed string for deterministic generation. Required.

    Returns:
        UUID string in standard format.

    Raises:
        ValueError: If seed is None or empty.
    """
    if not seed:
        raise ValueError(
            "generate_id() requires a deterministic seed. "
            "ResearchOS does not allow random identity generation. "
            "Provide a content-based seed string."
        )
    namespace = uuid.NAMESPACE_DNS
    return str(uuid.uuid5(namespace, seed))


def deterministic_hash(content: Any) -> str:
    """
    Compute a deterministic SHA-256 hash of any content.

    The content is serialized to JSON with sorted keys to ensure
    deterministic output regardless of dictionary ordering.

    Args:
        content: Any JSON-serializable content.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    serialized = json.dumps(content, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def generate_observation_id(
    source: str,
    timestamp: str,
    value: Any,
) -> str:
    """
    Generate a deterministic ID for an Observation.

    Based on Article XVII: Observation.id = deterministic UUID
    (source + timestamp + value hash)

    Args:
        source: Data source identifier.
        timestamp: UTC timestamp string.
        value: The observed value.

    Returns:
        Deterministic UUID string.
    """
    seed = f"{source}|{timestamp}|{value}"
    return generate_id(seed)

