"""Market Memory objects — persistent historical knowledge of market behavior.

Every object in this module represents a discrete, verifiable observation
about market structure, liquidity, volatility, or news. These form the
long-term market memory that supports explainable research conclusions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp


# ---------------------------------------------------------------------------
# MarketEvent — base container for all market event types
# ---------------------------------------------------------------------------

class MarketEvent(BaseObject):
    """A discrete, timestamped event in market structure.

    Attributes:
        event_type: Type identifier (e.g. "BOS", "CHOCH", "LiquiditySweep")
        asset: Asset symbol
        timeframe: Timeframe context (e.g. "M15", "H1", "D1")
        timestamp: When the event occurred
        direction: "bullish", "bearish", or "neutral"
        price_level: The price level at which the event occurred
        description: Human-readable description
        category: Event category (e.g. "Structure", "Liquidity", "Volatility")
        reference_ids: Related object IDs
        metadata: Free-form metadata dict
    """

    def __init__(
        self,
        event_type: str,
        asset: str,
        timeframe: str,
        timestamp: datetime,
        direction: str = "neutral",
        price_level: float = 0.0,
        description: str = "",
        category: str = "",
        reference_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"MarketEvent|{event_type}|{asset}|{timeframe}|{timestamp.isoformat()}|{price_level}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.event_type = event_type
        self.asset = asset
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.direction = direction
        self.price_level = price_level
        self.description = description
        self.category = category
        self.reference_ids: List[str] = reference_ids or []
        self.metadata: Dict[str, Any] = metadata or {}

        self.lifecycle.transition(
            LifecycleStage.DETECTED,
            reason=f"Market event detected: {event_type} on {asset} at {timestamp.isoformat()}",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction,
            "price_level": self.price_level,
            "description": self.description,
            "category": self.category,
            "reference_ids": sorted(self.reference_ids),
            "metadata": dict(sorted(self.metadata.items())) if self.metadata else {},
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "event_type": self.event_type,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction,
            "price_level": self.price_level,
            "description": self.description,
            "category": self.category,
            "reference_ids": self.reference_ids,
            "metadata": self.metadata,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MarketEvent":
        obj = super().from_dict(data)
        obj.event_type = data["event_type"]
        obj.asset = data["asset"]
        obj.timeframe = data.get("timeframe", "")
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.direction = data.get("direction", "neutral")
        obj.price_level = data.get("price_level", 0.0)
        obj.description = data.get("description", "")
        obj.category = data.get("category", "")
        obj.reference_ids = list(data.get("reference_ids", []))
        obj.metadata = dict(data.get("metadata", {}))
        return obj


# ---------------------------------------------------------------------------
# MarketStructure — Break of Structure / Change of Character
# ---------------------------------------------------------------------------

class MarketStructure(BaseObject):
    """A market structure break: BOS (Break of Structure) or CHOCH (Change of Character).

    Attributes:
        structure_type: "BOS" or "CHOCH"
        asset: Asset symbol
        timeframe: Timeframe context
        timestamp: When the structure break occurred
        direction: "bullish" or "bearish"
        price_level: The price level confirming the break
        confirmed: Whether the break was subsequently confirmed
        previous_structure_id: ID of the prior structure level
        confirmation_price: Price at confirmation (if confirmed)
        notes: Analytical notes
    """

    def __init__(
        self,
        structure_type: str,
        asset: str,
        timeframe: str,
        timestamp: datetime,
        direction: str = "bullish",
        price_level: float = 0.0,
        confirmed: bool = False,
        previous_structure_id: str = "",
        confirmation_price: float = 0.0,
        notes: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"MarketStructure|{structure_type}|{asset}|{timeframe}|{timestamp.isoformat()}|{price_level}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.structure_type = structure_type
        self.asset = asset
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.direction = direction
        self.price_level = price_level
        self.confirmed = confirmed
        self.previous_structure_id = previous_structure_id
        self.confirmation_price = confirmation_price
        self.notes = notes

        self.lifecycle.transition(
            LifecycleStage.DETECTED,
            reason=f"Market structure {structure_type} detected: {direction} break at {price_level}",
        )

    def confirm(self, confirmation_price: float) -> None:
        """Confirm the structure break at the given price."""
        self.confirmed = True
        self.confirmation_price = confirmation_price
        self.lifecycle.transition(
            LifecycleStage.VERIFIED,
            reason=f"Structure break confirmed at {confirmation_price}",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "structure_type": self.structure_type,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction,
            "price_level": self.price_level,
            "confirmed": self.confirmed,
            "previous_structure_id": self.previous_structure_id,
            "confirmation_price": self.confirmation_price,
            "notes": self.notes,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "structure_type": self.structure_type,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction,
            "price_level": self.price_level,
            "confirmed": self.confirmed,
            "previous_structure_id": self.previous_structure_id,
            "confirmation_price": self.confirmation_price,
            "notes": self.notes,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MarketStructure":
        obj = super().from_dict(data)
        obj.structure_type = data["structure_type"]
        obj.asset = data["asset"]
        obj.timeframe = data.get("timeframe", "")
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.direction = data.get("direction", "bullish")
        obj.price_level = data.get("price_level", 0.0)
        obj.confirmed = data.get("confirmed", False)
        obj.previous_structure_id = data.get("previous_structure_id", "")
        obj.confirmation_price = data.get("confirmation_price", 0.0)
        obj.notes = data.get("notes", "")
        return obj


# ---------------------------------------------------------------------------
# LiquidityEvent — Liquidity sweeps, stop runs, manipulations
# ---------------------------------------------------------------------------

class LiquidityEvent(BaseObject):
    """A liquidity-related market event: sweep, stop run, or manipulation.

    Attributes:
        event_type: "Sweep", "StopRun", "LiquidityGrab", "Manipulation"
        asset: Asset symbol
        timeframe: Timeframe context
        timestamp: When the event occurred
        direction: "bullish" or "bearish"
        price_level: The price level targeted
        swept_levels: Price levels that were swept
        outcome: "Hit", "Missed", or "Pending"
        reference_id: Related object ID (e.g. linked structure)
        notes: Analytical notes
    """

    def __init__(
        self,
        event_type: str,
        asset: str,
        timeframe: str,
        timestamp: datetime,
        direction: str = "bearish",
        price_level: float = 0.0,
        swept_levels: Optional[List[float]] = None,
        outcome: str = "Pending",
        reference_id: str = "",
        notes: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"LiquidityEvent|{event_type}|{asset}|{timeframe}|{timestamp.isoformat()}|{price_level}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.event_type = event_type
        self.asset = asset
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.direction = direction
        self.price_level = price_level
        self.swept_levels: List[float] = swept_levels or []
        self.outcome = outcome
        self.reference_id = reference_id
        self.notes = notes

        self.lifecycle.transition(
            LifecycleStage.DETECTED,
            reason=f"Liquidity event detected: {event_type} on {asset} at {price_level}",
        )

    def resolve(self, outcome: str) -> None:
        """Resolve the liquidity event with the actual outcome."""
        self.outcome = outcome
        self.lifecycle.transition(
            LifecycleStage.RESOLVED,
            reason=f"Liquidity event resolved: {outcome}",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction,
            "price_level": self.price_level,
            "swept_levels": sorted(self.swept_levels),
            "outcome": self.outcome,
            "reference_id": self.reference_id,
            "notes": self.notes,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "event_type": self.event_type,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction,
            "price_level": self.price_level,
            "swept_levels": self.swept_levels,
            "outcome": self.outcome,
            "reference_id": self.reference_id,
            "notes": self.notes,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "LiquidityEvent":
        obj = super().from_dict(data)
        obj.event_type = data["event_type"]
        obj.asset = data["asset"]
        obj.timeframe = data.get("timeframe", "")
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.direction = data.get("direction", "bearish")
        obj.price_level = data.get("price_level", 0.0)
        obj.swept_levels = [float(x) for x in data.get("swept_levels", [])]
        obj.outcome = data.get("outcome", "Pending")
        obj.reference_id = data.get("reference_id", "")
        obj.notes = data.get("notes", "")
        return obj


# ---------------------------------------------------------------------------
# MarketSession — Trading session summary
# ---------------------------------------------------------------------------

class MarketSession(BaseObject):
    """A trading session summary (London, New York, Asia, etc.).

    Attributes:
        session_name: "London", "NewYork", "Asia", "LondonClose", "NewYorkClose"
        asset: Asset symbol
        date: Session date string (YYYY-MM-DD)
        start_time: Session start timestamp
        end_time: Session end timestamp
        open: Session open price
        high: Session high price
        low: Session low price
        close: Session close price
        direction: "bullish", "bearish", or "neutral"
        volume_ratio: Volume relative to average (1.0 = average)
        range_atr_ratio: Range as multiple of ATR
        notes: Analytical notes
    """

    def __init__(
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
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"MarketSession|{session_name}|{asset}|{date}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.session_name = session_name
        self.asset = asset
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.direction = direction
        self.volume_ratio = volume_ratio
        self.range_atr_ratio = range_atr_ratio
        self.notes = notes

        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=f"Market session recorded: {session_name} on {asset} ({date})",
        )

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    def _to_hashable_dict(self) -> dict:
        return {
            "session_name": self.session_name,
            "asset": self.asset,
            "date": self.date,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "direction": self.direction,
            "volume_ratio": self.volume_ratio,
            "range_atr_ratio": self.range_atr_ratio,
            "notes": self.notes,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "session_name": self.session_name,
            "asset": self.asset,
            "date": self.date,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "direction": self.direction,
            "volume_ratio": self.volume_ratio,
            "range_atr_ratio": self.range_atr_ratio,
            "notes": self.notes,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MarketSession":
        obj = super().from_dict(data)
        obj.session_name = data["session_name"]
        obj.asset = data["asset"]
        obj.date = data["date"]
        obj.start_time = parse_timestamp(data["start_time"])
        obj.end_time = parse_timestamp(data["end_time"])
        obj.open = data.get("open", 0.0)
        obj.high = data.get("high", 0.0)
        obj.low = data.get("low", 0.0)
        obj.close = data.get("close", 0.0)
        obj.direction = data.get("direction", "neutral")
        obj.volume_ratio = data.get("volume_ratio", 1.0)
        obj.range_atr_ratio = data.get("range_atr_ratio", 0.0)
        obj.notes = data.get("notes", "")
        return obj


# ---------------------------------------------------------------------------
# VolatilityState — Volatility regime measurement
# ---------------------------------------------------------------------------

class VolatilityState(BaseObject):
    """A volatility regime measurement at a point in time.

    Attributes:
        asset: Asset symbol
        timeframe: Timeframe context
        timestamp: Measurement time
        atr_value: Current ATR value
        atr_percentile: ATR percentile vs history (0.0-1.0)
        volatility_regime: "Low", "Normal", "High", or "Extreme"
        expanding: Whether volatility is expanding
        contracting: Whether volatility is contracting
        bb_width: Bollinger Band width relative to middle band
        notes: Analytical notes
    """

    def __init__(
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
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"VolatilityState|{asset}|{timeframe}|{timestamp.isoformat()}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.asset = asset
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.atr_value = atr_value
        self.atr_percentile = atr_percentile
        self.volatility_regime = volatility_regime
        self.expanding = expanding
        self.contracting = contracting
        self.bb_width = bb_width
        self.notes = notes

        self.lifecycle.transition(
            LifecycleStage.ANALYZED,
            reason=f"Volatility state recorded: {volatility_regime} regime on {asset}",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "atr_value": self.atr_value,
            "atr_percentile": self.atr_percentile,
            "volatility_regime": self.volatility_regime,
            "expanding": self.expanding,
            "contracting": self.contracting,
            "bb_width": self.bb_width,
            "notes": self.notes,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "asset": self.asset,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "atr_value": self.atr_value,
            "atr_percentile": self.atr_percentile,
            "volatility_regime": self.volatility_regime,
            "expanding": self.expanding,
            "contracting": self.contracting,
            "bb_width": self.bb_width,
            "notes": self.notes,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "VolatilityState":
        obj = super().from_dict(data)
        obj.asset = data["asset"]
        obj.timeframe = data.get("timeframe", "")
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.atr_value = data.get("atr_value", 0.0)
        obj.atr_percentile = data.get("atr_percentile", 0.5)
        obj.volatility_regime = data.get("volatility_regime", "Normal")
        obj.expanding = data.get("expanding", False)
        obj.contracting = data.get("contracting", False)
        obj.bb_width = data.get("bb_width", 0.0)
        obj.notes = data.get("notes", "")
        return obj


# ---------------------------------------------------------------------------
# NewsReference — News event reference with impact assessment
# ---------------------------------------------------------------------------

class NewsReference(BaseObject):
    """A news event reference with impact and sentiment assessment.

    Attributes:
        title: News headline
        source: News source identifier
        published_at: Publication timestamp
        impact_score: Estimated market impact (0.0-1.0)
        sentiment: "positive", "negative", or "neutral"
        affected_assets: List of affected asset symbols
        category: "Economic", "Earnings", "Geopolitical", "CentralBank", "Other"
        summary: Brief summary
        url: Source URL
    """

    def __init__(
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
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"NewsReference|{title}|{source}|{published_at.isoformat()}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.title = title
        self.source = source
        self.published_at = published_at
        self.impact_score = impact_score
        self.sentiment = sentiment
        self.affected_assets: List[str] = affected_assets or []
        self.category = category
        self.summary = summary
        self.url = url

        self.lifecycle.transition(
            LifecycleStage.ACTIVE,
            reason=f"News reference recorded: {title[:50]}",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "published_at": self.published_at.isoformat(),
            "impact_score": self.impact_score,
            "sentiment": self.sentiment,
            "affected_assets": sorted(self.affected_assets),
            "category": self.category,
            "summary": self.summary,
            "url": self.url,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "title": self.title,
            "source": self.source,
            "published_at": self.published_at.isoformat(),
            "impact_score": self.impact_score,
            "sentiment": self.sentiment,
            "affected_assets": self.affected_assets,
            "category": self.category,
            "summary": self.summary,
            "url": self.url,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "NewsReference":
        obj = super().from_dict(data)
        obj.title = data["title"]
        obj.source = data.get("source", "")
        obj.published_at = parse_timestamp(data["published_at"])
        obj.impact_score = data.get("impact_score", 0.5)
        obj.sentiment = data.get("sentiment", "neutral")
        obj.affected_assets = list(data.get("affected_assets", []))
        obj.category = data.get("category", "Other")
        obj.summary = data.get("summary", "")
        obj.url = data.get("url", "")
        return obj


# ---------------------------------------------------------------------------
# MarketOutcome — Outcome tracking for market events
# ---------------------------------------------------------------------------

class MarketOutcome(BaseObject):
    """The outcome of a market event or structure break.

    Attributes:
        event_id: ID of the related MarketEvent, MarketStructure, or LiquidityEvent
        event_type: Type of the related event
        asset: Asset symbol
        timestamp: When the outcome was determined
        outcome_type: "Success", "Failure", "Partial", "Pending"
        actual_move: Actual price move following the event (pips/points)
        expected_move: Expected price move at detection time
        confidence: Confidence at detection (0.0-1.0)
        max_favorable: Maximum favorable excursion
        max_adverse: Maximum adverse excursion
        duration_minutes: How long until outcome was determined
        notes: Analytical notes
    """

    def __init__(
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
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"MarketOutcome|{event_id}|{outcome_type}|{timestamp.isoformat()}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.event_id = event_id
        self.event_type = event_type
        self.asset = asset
        self.timestamp = timestamp
        self.outcome_type = outcome_type
        self.actual_move = actual_move
        self.expected_move = expected_move
        self.confidence = confidence
        self.max_favorable = max_favorable
        self.max_adverse = max_adverse
        self.duration_minutes = duration_minutes
        self.notes = notes

        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=f"Market outcome recorded: {outcome_type} for {event_type} on {asset}",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "asset": self.asset,
            "timestamp": self.timestamp.isoformat(),
            "outcome_type": self.outcome_type,
            "actual_move": self.actual_move,
            "expected_move": self.expected_move,
            "confidence": self.confidence,
            "max_favorable": self.max_favorable,
            "max_adverse": self.max_adverse,
            "duration_minutes": self.duration_minutes,
            "notes": self.notes,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "event_id": self.event_id,
            "event_type": self.event_type,
            "asset": self.asset,
            "timestamp": self.timestamp.isoformat(),
            "outcome_type": self.outcome_type,
            "actual_move": self.actual_move,
            "expected_move": self.expected_move,
            "confidence": self.confidence,
            "max_favorable": self.max_favorable,
            "max_adverse": self.max_adverse,
            "duration_minutes": self.duration_minutes,
            "notes": self.notes,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MarketOutcome":
        obj = super().from_dict(data)
        obj.event_id = data["event_id"]
        obj.event_type = data.get("event_type", "")
        obj.asset = data.get("asset", "")
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.outcome_type = data.get("outcome_type", "Pending")
        obj.actual_move = data.get("actual_move", 0.0)
        obj.expected_move = data.get("expected_move", 0.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.max_favorable = data.get("max_favorable", 0.0)
        obj.max_adverse = data.get("max_adverse", 0.0)
        obj.duration_minutes = data.get("duration_minutes", 0)
        obj.notes = data.get("notes", "")
        return obj
