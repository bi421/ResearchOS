from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTINUITY = ROOT / "reports/phase52_rebuild/context_continuity_audit.json"
EXACT_MINUTE = ROOT / "reports/phase52_rebuild/xau_exact_common_minute_forensic.json"
FEED_DIVERGENCE = ROOT / "reports/phase52_rebuild/xau_feed_divergence_forensic.json"
OUT = ROOT / "reports/phase52_rebuild/xau_source_provenance_gate.json"

MIN_COMMON_DAYS = 30
MIN_EXACT_COMMON_MINUTES = 100_000


def _load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing required evidence: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    continuity = _load(CONTINUITY)
    exact = _load(EXACT_MINUTE)
    divergence = _load(FEED_DIVERGENCE)

    xau = continuity.get("xau", {})
    overlap_days = int(xau.get("days", 0))

    common_minutes = int(
        divergence.get(
            "exact_common_utc_minutes",
            exact.get(
                "exact_common_utc_minutes",
                exact.get(
                    "common_minutes",
                    exact.get("total_common_minutes", 0),
                ),
            ),
        )
    )

    close = divergence.get("close", {})
    mean_signed = float(close.get("mean_signed_difference", 0.0))
    median_signed = float(close.get("median_signed", 0.0))
    mean_abs = float(close.get("mean_absolute", 0.0))
    median_abs = float(close.get("median_absolute", 0.0))
    positive = int(close.get("positive", 0))
    negative = int(close.get("negative", 0))
    zero = int(close.get("zero", 0))

    two_sided = positive > 0 and negative > 0
    nonzero_absolute_difference = mean_abs > 0.0 or median_abs > 0.0
    evidence_sufficient = (
        overlap_days >= MIN_COMMON_DAYS
        and common_minutes >= MIN_EXACT_COMMON_MINUTES
        and two_sided
        and nonzero_absolute_difference
    )

    if evidence_sufficient:
        source_equivalence = "NOT_ESTABLISHED"
        provenance_status = "BLOCKED"
        reason = (
            "Exact common UTC-minute prices diverge materially in both directions; "
            "the evidence does not support treating Dukascopy XAU as equivalent "
            "to the canonical MT5 XAU source."
        )
    else:
        source_equivalence = "INSUFFICIENT_EVIDENCE"
        provenance_status = "BLOCKED"
        reason = (
            "Required source-divergence evidence is incomplete; "
            "cross-source XAU context cannot be accepted."
        )

    payload = {
        "phase": "5.2",
        "status": provenance_status,
        "source_equivalence": source_equivalence,
        "decision": "DO_NOT_ACCEPT_CROSS_SOURCE_XAU_CONTEXT",
        "reason": reason,
        "evidence": {
            "overlap_days": overlap_days,
            "minimum_required_overlap_days": MIN_COMMON_DAYS,
            "exact_common_utc_minutes": common_minutes,
            "minimum_required_common_minutes": MIN_EXACT_COMMON_MINUTES,
            "close_mean_signed_difference": mean_signed,
            "close_median_signed_difference": median_signed,
            "close_mean_absolute_difference": mean_abs,
            "close_median_absolute_difference": median_abs,
            "close_positive_count": positive,
            "close_negative_count": negative,
            "close_zero_count": zero,
            "two_sided_difference": two_sided,
            "nonzero_absolute_difference": nonzero_absolute_difference,
        },
        "interpretation": {
            "constant_price_offset_supported": False,
            "same_minute_price_equivalence_supported": False,
            "independent_price_path_supported": two_sided,
            "causal_feed_or_venue_attribution_proven": False,
        },
        "scientific_guardrail": (
            "This gate does not claim which feed, venue, quote convention, "
            "or aggregation methodology caused the divergence."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("=" * 70)
    print("PHASE 5.2 — XAU SOURCE PROVENANCE GATE")
    print("=" * 70)
    print(f"OVERLAP DAYS                 : {overlap_days}")
    print(f"EXACT COMMON UTC MINUTES    : {common_minutes}")
    print(f"CLOSE MEAN SIGNED            : {mean_signed}")
    print(f"CLOSE MEDIAN SIGNED          : {median_signed}")
    print(f"CLOSE MEAN ABS               : {mean_abs}")
    print(f"CLOSE MEDIAN ABS             : {median_abs}")
    print(f"POSITIVE                     : {positive}")
    print(f"NEGATIVE                     : {negative}")
    print(f"TWO-SIDED DIFFERENCE         : {two_sided}")
    print("CONSTANT OFFSET SUPPORTED    : False")
    print(f"SOURCE EQUIVALENCE           : {source_equivalence}")
    print(f"PROVENANCE STATUS            : {provenance_status}")
    print("DECISION                     : DO_NOT_ACCEPT_CROSS_SOURCE_XAU_CONTEXT")
    print(f"OUTPUT                       : {OUT.relative_to(ROOT)}")
    print("=" * 70)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
