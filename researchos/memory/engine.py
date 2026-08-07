"""MarketMemoryEngine — service for recording and querying market memory.

This engine provides the high-level API for the Market Memory Layer.
It wraps a RepositoryInterface and provides deterministic methods for:
- Recording market events (BOS, CHOCH, liquidity sweeps, etc.)
- Managing trading session data
- Tracking volatility regimes
- Storing news references
- Recording outcomes with full traceability

Every method produces deterministic objects that integrate with the
existing audit chain and serialization framework.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from researchos.core.base_object import BaseObject
from researchos.objects.market_memory import (
    LiquidityEvent,
    MarketOutcome,
    MarketSession,
    MarketStructure,
    NewsReference,
    VolatilityState,
)
from researchos.objects.process import AuditEntry
from researchos.repository.interface import RepositoryInterface


class MarketMemoryEngine:
    """Service for recording and querying market memory.

    Usage:
        engine = MarketMemoryEngine(repository)
        bos = engine.record_structure_break("BOS", "EURUSD", "H1", ts, 1.1050)
        session = engine.record_session("London", "EURUSD", "2024-06-01", ...)
    """

    def __init__(self, repository: RepositoryInterface):
        self.repo = repository

    # ------------------------------------------------------------------
    # Structure breaks (BOS / CHOCH)
    # ------------------------------------------------------------------

    def record_structure_break(
        self,
        structure_type: str,
        asset: str,
        timeframe: str,
        timestamp: datetime,
        direction: str = "bullish",
        price_level: float = 0.0,
        confirmed: bool = False,
        previous_structure_id: str = "",
        notes: str = "",
    ) -> MarketStructure:
        """Record a market structure break (BOS or CHOCH)."""
        ms = MarketStructure(
            structure_type=structure_type,
            asset=asset,
            timeframe=timeframe,
            timestamp=timestamp,
            direction=direction,
            price_level=price_level,
            confirmed=confirmed,
            previous_structure_id=previous_structure_id,
            notes=notes,
        )
        self.repo.save(ms)
        self._audit("STRUCTURE_BREAK", ms.id, f"{structure_type} {direction} on {asset} at {price_level}")
        return ms

    def confirm_structure_break(self, structure_id: str, confirmation_price: float) -> MarketStructure:
        """Confirm a previously recorded structure break."""
        obj = self.repo.get(structure_id)
        if obj is None:
            raise ValueError(f"MarketStructure not found: {structure_id}")
        if not isinstance(obj, MarketStructure):
            raise TypeError(f"Object {structure_id} is not a MarketStructure")
        obj.confirm(confirmation_price)
        self.repo.save(obj)
        self._audit("STRUCTURE_CONFIRMED", obj.id, f"Confirmed at {confirmation_price}")
        return obj

    # ------------------------------------------------------------------
    # Liquidity events
    # ------------------------------------------------------------------

    def record_liquidity_event(
        self,
        event_type: str,
        asset: str,
        timeframe: str,
        timestamp: datetime,
        direction: str = "bearish",
        price_level: float = 0.0,
        swept_levels: Optional[List[float]] = None,
        notes: str = "",
    ) -> LiquidityEvent:
        """Record a liquidity event (sweep, stop run, manipulation)."""
        le = LiquidityEvent(
            event_type=event_type,
            asset=asset,
            timeframe=timeframe,
            timestamp=timestamp,
            direction=direction,
            price_level=price_level,
            swept_levels=swept_levels,
            notes=notes,
        )
        self.repo.save(le)
        self._audit("LIQUIDITY_EVENT", le.id, f"{event_type} {direction} on {asset} at {price_level}")
        return le

    def resolve_liquidity_event(self, event_id: str, outcome: str) -> LiquidityEvent:
        """Resolve a liquidity event with the actual outcome."""
        obj = self.repo.get(event_id)
        if obj is None:
            raise ValueError(f"LiquidityEvent not found: {event_id}")
        if not isinstance(obj, LiquidityEvent):
            raise TypeError(f"Object {event_id} is not a LiquidityEvent")
        obj.resolve(outcome)
        self.repo.save(obj)
        self._audit("LIQUIDITY_RESOLVED", obj.id, f"Resolved: {outcome}")
        return obj

    # ------------------------------------------------------------------
    # Market sessions
    # ------------------------------------------------------------------

    def record_session(
        self,
        session_name: str,
        asset: str,
        date: str,
        start_time: datetime,
        end_time: datetime,
        open: float = 0.0,
        high: float = 0.0,
        low: float = 0.0,
        close: float = 0.0,
        direction: str = "neutral",
        volume_ratio: float = 1.0,
        range_atr_ratio: float = 0.0,
        notes: str = "",
    ) -> MarketSession:
        """Record a trading session summary."""
        ms = MarketSession(
            session_name=session_name,
            asset=asset,
            date=date,
            start_time=start_time,
            end_time=end_time,
            open=open,
            high=high,
            low=low,
            close=close,
            direction=direction,
            volume_ratio=volume_ratio,
            range_atr_ratio=range_atr_ratio,
            notes=notes,
        )
        self.repo.save(ms)
        self._audit("SESSION_RECORDED", ms.id, f"{session_name} session on {asset} ({date})")
        return ms

    # ------------------------------------------------------------------
    # Volatility state
    # ------------------------------------------------------------------

    def record_volatility_state(
        self,
        asset: str,
        timeframe: str,
        timestamp: datetime,
        atr_value: float = 0.0,
        atr_percentile: float = 0.5,
        volatility_regime: str = "Normal",
        expanding: bool = False,
        contracting: bool = False,
        bb_width: float = 0.0,
        notes: str = "",
    ) -> VolatilityState:
        """Record a volatility state measurement."""
        vs = VolatilityState(
            asset=asset,
            timeframe=timeframe,
            timestamp=timestamp,
            atr_value=atr_value,
            atr_percentile=atr_percentile,
            volatility_regime=volatility_regime,
            expanding=expanding,
            contracting=contracting,
            bb_width=bb_width,
            notes=notes,
        )
        self.repo.save(vs)
        self._audit("VOLATILITY_STATE", vs.id, f"{volatility_regime} on {asset} ({timeframe})")
        return vs

    # ------------------------------------------------------------------
    # News references
    # ------------------------------------------------------------------

    def record_news(
        self,
        title: str,
        source: str,
        published_at: datetime,
        impact_score: float = 0.5,
        sentiment: str = "neutral",
        affected_assets: Optional[List[str]] = None,
        category: str = "Other",
        summary: str = "",
        url: str = "",
    ) -> NewsReference:
        """Record a news event reference."""
        nr = NewsReference(
            title=title,
            source=source,
            published_at=published_at,
            impact_score=impact_score,
            sentiment=sentiment,
            affected_assets=affected_assets,
            category=category,
            summary=summary,
            url=url,
        )
        self.repo.save(nr)
        self._audit("NEWS_RECORDED", nr.id, f"News: {title[:60]} [{category}]")
        return nr

    # ------------------------------------------------------------------
    # Outcomes
    # ------------------------------------------------------------------

    def record_outcome(
        self,
        event_id: str,
        event_type: str,
        asset: str,
        timestamp: datetime,
        outcome_type: str = "Pending",
        actual_move: float = 0.0,
        expected_move: float = 0.0,
        confidence: float = 0.0,
        max_favorable: float = 0.0,
        max_adverse: float = 0.0,
        duration_minutes: int = 0,
        notes: str = "",
    ) -> MarketOutcome:
        """Record the outcome of a market event."""
        mo = MarketOutcome(
            event_id=event_id,
            event_type=event_type,
            asset=asset,
            timestamp=timestamp,
            outcome_type=outcome_type,
            actual_move=actual_move,
            expected_move=expected_move,
            confidence=confidence,
            max_favorable=max_favorable,
            max_adverse=max_adverse,
            duration_minutes=duration_minutes,
            notes=notes,
        )
        self.repo.save(mo)
        self._audit("OUTCOME_RECORDED", mo.id, f"{outcome_type} for {event_type} on {asset}")
        return mo

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_events_by_asset(
        self,
        asset: str,
        object_type: Optional[str] = None,
    ) -> List[BaseObject]:
        """Get all market memory objects for an asset, optionally filtered by type.

        Scans through the repository's get_all() and filters client-side.
        For large datasets, a database-backed query would be more efficient.
        """
        all_objects = self.repo.get_all()
        result: List[BaseObject] = []
        for obj in all_objects:
            if not hasattr(obj, "asset") or obj.asset != asset:
                continue
            if object_type is not None and type(obj).__name__ != object_type:
                continue
            result.append(obj)
        return result

    def get_events_in_range(
        self,
        asset: str,
        start_time: datetime,
        end_time: datetime,
        object_type: Optional[str] = None,
    ) -> List[BaseObject]:
        """Get market memory objects within a time range.

        Objects are filtered by asset and timestamp range.
        """
        all_objects = self.repo.get_all()
        result: List[BaseObject] = []
        for obj in all_objects:
            if not hasattr(obj, "asset") or obj.asset != asset:
                continue
            if not hasattr(obj, "timestamp"):
                continue
            ts = obj.timestamp
            if isinstance(ts, str):
                continue
            if ts < start_time or ts > end_time:
                continue
            if object_type is not None and type(obj).__name__ != object_type:
                continue
            result.append(obj)
        return result

    def get_recent_events(
        self,
        asset: str,
        limit: int = 20,
        object_type: Optional[str] = None,
    ) -> List[BaseObject]:
        """Get the most recent market memory objects for an asset."""
        events = self.get_events_by_asset(asset, object_type)
        events.sort(key=lambda o: getattr(o, "timestamp", datetime(1970, 1, 1, tzinfo=timezone.utc)), reverse=True)
        return events[:limit]

    def get_structures(
        self,
        asset: str,
        structure_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[MarketStructure]:
        """Get market structure events for an asset."""
        result: List[MarketStructure] = []
        for obj in self.repo.get_all():
            if not isinstance(obj, MarketStructure):
                continue
            if obj.asset != asset:
                continue
            if structure_type is not None and obj.structure_type != structure_type:
                continue
            result.append(obj)
        result.sort(key=lambda o: o.timestamp, reverse=True)
        return result[:limit]

    def get_liquidity_events(
        self,
        asset: str,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[LiquidityEvent]:
        """Get liquidity events for an asset."""
        result: List[LiquidityEvent] = []
        for obj in self.repo.get_all():
            if not isinstance(obj, LiquidityEvent):
                continue
            if obj.asset != asset:
                continue
            if event_type is not None and obj.event_type != event_type:
                continue
            result.append(obj)
        result.sort(key=lambda o: o.timestamp, reverse=True)
        return result[:limit]

    def get_sessions(
        self,
        asset: str,
        session_name: Optional[str] = None,
        limit: int = 50,
    ) -> List[MarketSession]:
        """Get trading sessions for an asset."""
        result: List[MarketSession] = []
        for obj in self.repo.get_all():
            if not isinstance(obj, MarketSession):
                continue
            if obj.asset != asset:
                continue
            if session_name is not None and obj.session_name != session_name:
                continue
            result.append(obj)
        result.sort(key=lambda o: o.date, reverse=True)
        return result[:limit]

    def get_volatility_history(
        self,
        asset: str,
        timeframe: str = "H1",
        limit: int = 100,
    ) -> List[VolatilityState]:
        """Get volatility history for an asset/timeframe."""
        result: List[VolatilityState] = []
        for obj in self.repo.get_all():
            if not isinstance(obj, VolatilityState):
                continue
            if obj.asset != asset or obj.timeframe != timeframe:
                continue
            result.append(obj)
        result.sort(key=lambda o: o.timestamp, reverse=True)
        return result[:limit]

    def count_by_type(self, object_type: str) -> int:
        """Count market memory objects by type."""
        count = 0
        type_map = {
            "MarketStructure": MarketStructure,
            "LiquidityEvent": LiquidityEvent,
            "MarketSession": MarketSession,
            "VolatilityState": VolatilityState,
            "NewsReference": NewsReference,
            "MarketOutcome": MarketOutcome,
        }
        cls = type_map.get(object_type)
        if cls is None:
            return 0
        for obj in self.repo.get_all():
            if isinstance(obj, cls):
                count += 1
        return count

    def get_outcomes_for_event(self, event_id: str) -> List[MarketOutcome]:
        """Get all outcomes for a specific event."""
        result: List[MarketOutcome] = []
        for obj in self.repo.get_all():
            if not isinstance(obj, MarketOutcome):
                continue
            if obj.event_id == event_id:
                result.append(obj)
        return result

    # ------------------------------------------------------------------
    # Audit helper
    # ------------------------------------------------------------------

    def _audit(self, action: str, object_id: str, reason: str) -> None:
        """Record an audit entry for a market memory action."""
        entry = AuditEntry(
            actor="market_memory_engine",
            action=action,
            object_id=object_id,
            object_type="MarketMemory",
        )
        self.repo.save(entry)
