"""Diagnose the curated XAUUSD D1 loader hash drift."""
from __future__ import annotations

from researchos.core.identity import deterministic_hash
from researchos.data_engine.csv_loader import CsvLoader
from researchos.data_engine.candle import Candle

CURATED = "data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv"
OLD_HASH = "4ea006efd023fef17ffd3ecf7520857451d45ebd117ff82d81ab3d50f9343d04"
FIELDS_TO_TEST = [
    "quote_volume",
    "trades_count",
    "spread",
    "tick_volume",
    "real_volume",
    "is_complete",
    "ontology_tags",
]


def load() -> list[Candle]:
    return CsvLoader().load_mt5_candles(CURATED, symbol="XAUUSD", timeframe="1d")


def dump_sample(candles: list[Candle], n: int = 3) -> None:
    print(f"\n=== Loaded {len(candles)} candles ===")
    print("--- first candles ---")
    for c in candles[:n]:
        _dump_one(c)
    print("--- last candles ---")
    for c in candles[-n:]:
        _dump_one(c)


def _dump_one(c: Candle) -> None:
    print(
        f"  ts={c.timestamp.isoformat()!r} tzinfo={c.timestamp.tzinfo} "
        f"O={c.open} H={c.high} L={c.low} C={c.close} "
        f"volume={c.volume} quote_volume={c.quote_volume} "
        f"tick_volume={c.tick_volume} real_volume={c.real_volume} "
        f"spread={c.spread} trades_count={c.trades_count} "
        f"is_complete={c.is_complete} id={c.id[:12]}... hash={c.hash[:12]}..."
    )


def current_digest(candles: list[Candle]) -> str:
    return deterministic_hash([c.hash for c in candles])


def digest_without_field(candles: list[Candle], field: str) -> str:
    hashes = []
    for c in candles:
        content = c._to_hashable_dict()
        content.pop(field, None)
        hashes.append(deterministic_hash(content))
    return deterministic_hash(hashes)


def main() -> None:
    candles = load()
    dump_sample(candles)

    actual = current_digest(candles)
    print(f"\nCurrent digest:  {actual}")
    print(f"Pinned old hash: {OLD_HASH}")
    print(f"Match: {actual == OLD_HASH}")

    if actual == OLD_HASH:
        print("\nNo drift detected right now.")
        return

    print("\n=== Testing which field's absence would restore the old hash ===")
    baseline = digest_without_field(candles, "__nonexistent__")
    for field in FIELDS_TO_TEST:
        alt = digest_without_field(candles, field)
        changed = "CHANGES digest" if alt != baseline else "no effect"
        print(f"  without {field!r:16s}: {changed}")

    print("\n=== Raw CSV header + first 2 raw lines ===")
    with open(CURATED, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            print(f"  {line.rstrip()}")
            if i >= 2:
                break


if __name__ == "__main__":
    main()
