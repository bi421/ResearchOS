"""OBJECT_REGISTRY disambiguation tests (Phase B3, 2026-08-17).

Pins the storage-layer type registry against the market-memory name
collisions that were resolved by renaming:

    market_memory.MacroMarketEvent   (was MarketEvent — calendar/macro release)
    market_memory.MacroContextSnapshot (was MacroState — macro snapshot)

The registry maps serialized ``object_type`` strings to the *objects-layer*
classes.  These tests document and pin that mapping so that:

1. A market-memory event/snapshot dict can never silently rehydrate as the
   wrong (objects-layer) class through ``ResearchRepository`` without a test
   failing first.
2. The renamed classes keep their legacy serialized ``object_type`` strings
   (byte-identical serialization), and the deprecated aliases still resolve.
"""

import unittest

from researchos.market_memory import (
    MacroContextSnapshot,
    MacroMarketEvent,
    MacroState,
    MarketEvent,
)
from researchos.market_memory.events import MacroMarketEvent as EventsMacroMarketEvent
from researchos.market_memory.models import MacroContextSnapshot as ModelsMacroContextSnapshot
from researchos.objects.market_memory import MarketEvent as ObjectsMarketEvent
from researchos.objects.observation import MacroState as ObservationMacroState
from researchos.storage.repository import OBJECT_REGISTRY


class TestRegistryDisambiguation(unittest.TestCase):
    """Registry keys must map to the objects-layer classes, not market-memory ones."""

    def test_registry_market_event_maps_to_objects_layer(self):
        self.assertIs(OBJECT_REGISTRY["MarketEvent"], ObjectsMarketEvent)

    def test_registry_macro_state_maps_to_observation_layer(self):
        self.assertIs(OBJECT_REGISTRY["MacroState"], ObservationMacroState)

    def test_market_memory_classes_are_not_registered(self):
        """Renamed classes must never appear as registry values (wrong-class trap)."""
        registered = set(OBJECT_REGISTRY.values())
        self.assertNotIn(EventsMacroMarketEvent, registered)
        self.assertNotIn(ModelsMacroContextSnapshot, registered)


class TestLegacySerializationPins(unittest.TestCase):
    """Renamed classes must serialize byte-identically to their legacy forms."""

    def test_macro_market_event_serializes_with_legacy_type(self):
        from datetime import datetime, timezone

        event = MacroMarketEvent("CPI", datetime(2025, 1, 1, tzinfo=timezone.utc), description="CPI")
        self.assertEqual(event.to_dict()["object_type"], "MarketEvent")

    def test_macro_context_snapshot_serializes_with_legacy_type(self):
        from datetime import datetime, timezone

        snapshot = MacroContextSnapshot(datetime(2025, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(snapshot.to_dict()["object_type"], "MacroState")


class TestDeprecatedAliases(unittest.TestCase):
    def test_market_event_alias(self):
        self.assertIs(MarketEvent, MacroMarketEvent)

    def test_macro_state_alias(self):
        self.assertIs(MacroState, MacroContextSnapshot)


if __name__ == "__main__":
    unittest.main()
