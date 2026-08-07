"""
Market Memory data models — deterministic objects for historical market states.

Based on the ResearchOS constitutional framework:
    - Deterministic: Same inputs produce same outputs
    - BaseObject inheritance with full lifecycle
    - Complete serialization via to_dict / from_dict
    - Hashable content for integrity verification

Objects:
    - MarketSnapshot: OHLCV + derived features at a point in time
    - MarketRegime: Classified market regime with confidence
    - MacroState: Macroeconomic conditions snapshot
    - HistoricalScenario: Complete market scenario for comparison
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.timestamp import parse_timestamp


class MarketSnapshot(BaseObject):
    """
    A snapshot of OHLCV market data with derived features at a point in time.

    Supports XAUUSD and other assets with:
        - OHLCV: Open, High, Low, Close, Volume
        - timeframe: Bar/candle timeframe
        - volatility: Derived volatility measure
        - trend_state: Identified trend direction
        - market_regime: Classified regime at this point

    Attributes:
        asset: Asset identifier (e.g., "XAUUSD")
        timestamp: UTC timestamp of the snapshot
        timeframe: Bar/candle timeframe (e.g., "1h", "4h", "1d")
        open: Opening price
        high: Highest price
        low: Lowest price
        close: Closing price
        volume: Trading volume
        volatility: Derived volatility measure (e.g., ATR, std dev)
        trend_state: Identified trend direction ("Bullish", "Bearish", "Neutral", "Ranging")
        market_regime: Classified regime ("Trending", "Ranging", "Volatile", "Quiet")
        indicators: Dictionary of computed indicator values
        confidence: Confidence in this snapshot (0.0-1.0)
    """

    def __init__(
        self,
        asset: str,
        timestamp: datetime,
        timeframe: str = "",
        open: float = 0.0,
        high: float = 0.0,
        low: float = 0.0,
        close: float = 0.0,
        volume: float = 0.0,
        volatility: float = 0.0,
        trend_state: str = "",
        market_regime: str = "",
        indicators: Optional[Dict[str, float]] = None,
        confidence: float = 0.0,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"MarketSnapshot|{asset}|{timestamp.isoformat()}|{timeframe}|{close}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.asset = asset
        self.timestamp = timestamp
        self.timeframe = timeframe
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.volatility = volatility
        self.trend_state = trend_state
        self.market_regime = market_regime
        self.indicators: Dict[str, float] = indicators or {}
        self.confidence = confidence

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timestamp": self.timestamp.isoformat(),
            "timeframe": self.timeframe,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "volatility": self.volatility,
            "trend_state": self.trend_state,
            "market_regime": self.market_regime,
            "indicators": dict(sorted(self.indicators.items())),
            "confidence": self.confidence,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "asset": self.asset,
            "timestamp": self.timestamp.isoformat(),
            "timeframe": self.timeframe,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "volatility": self.volatility,
            "trend_state": self.trend_state,
            "market_regime": self.market_regime,
            "indicators": self.indicators,
            "confidence": self.confidence,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MarketSnapshot":
        obj = super().from_dict(data)
        obj.asset = data["asset"]
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.timeframe = data.get("timeframe", "")
        obj.open = data.get("open", 0.0)
        obj.high = data.get("high", 0.0)
        obj.low = data.get("low", 0.0)
        obj.close = data.get("close", 0.0)
        obj.volume = data.get("volume", 0.0)
        obj.volatility = data.get("volatility", 0.0)
        obj.trend_state = data.get("trend_state", "")
        obj.market_regime = data.get("market_regime", "")
        obj.indicators = dict(data.get("indicators", {}))
        obj.confidence = data.get("confidence", 0.0)
        return obj


class MarketRegime(BaseObject):
    """
    A classified market regime with confidence assessment.

    Encapsulates the broader market environment classification:
        - Regime type: Trending, Ranging, Volatile, Quiet, Crisis, Risk-On, Risk-Off
        - Confidence in the classification
        - Supporting evidence from snapshots

    Attributes:
        regime: The identified regime name
        asset: Asset identifier
        timestamp: UTC timestamp of the classification
        confidence: Confidence in this classification (0.0-1.0)
        snapshot_ids: IDs of supporting MarketSnapshot objects
        volatility_level: Measured volatility level
        trend_strength: Strength of trend if applicable (0.0-1.0)
        duration_bars: Estimated duration in bars
        notes: Additional context notes
    """

    def __init__(
        self,
        regime: str,
        asset: str,
        timestamp: datetime,
        confidence: float = 0.0,
        snapshot_ids: Optional[List[str]] = None,
        volatility_level: float = 0.0,
        trend_strength: float = 0.0,
        duration_bars: int = 0,
        notes: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"MarketRegime|{regime}|{asset}|{timestamp.isoformat()}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.regime = regime
        self.asset = asset
        self.timestamp = timestamp
        self.confidence = confidence
        self.snapshot_ids: List[str] = snapshot_ids or []
        self.volatility_level = volatility_level
        self.trend_strength = trend_strength
        self.duration_bars = duration_bars
        self.notes = notes

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "regime": self.regime,
            "asset": self.asset,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "snapshot_ids": sorted(self.snapshot_ids),
            "volatility_level": self.volatility_level,
            "trend_strength": self.trend_strength,
            "duration_bars": self.duration_bars,
            "notes": self.notes,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "regime": self.regime,
            "asset": self.asset,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "snapshot_ids": self.snapshot_ids,
            "volatility_level": self.volatility_level,
            "trend_strength": self.trend_strength,
            "duration_bars": self.duration_bars,
            "notes": self.notes,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MarketRegime":
        obj = super().from_dict(data)
        obj.regime = data["regime"]
        obj.asset = data["asset"]
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.confidence = data.get("confidence", 0.0)
        obj.snapshot_ids = list(data.get("snapshot_ids", []))
        obj.volatility_level = data.get("volatility_level", 0.0)
        obj.trend_strength = data.get("trend_strength", 0.0)
        obj.duration_bars = data.get("duration_bars", 0)
        obj.notes = data.get("notes", "")
        return obj


class MacroState(BaseObject):
    """
    A snapshot of macroeconomic conditions relevant to trading.

    Encapsulates:
        - DXY: US Dollar Index value
        - real_yield: US Real Yield value
        - cpi: Consumer Price Index value
        - fed_event: Recent Fed event description
        - nfp: Non-Farm Payrolls value
        - geopolitical_events: List of active geopolitical events
        - overall_assessment: Summary assessment ("Bullish", "Bearish", "Neutral")

    Attributes:
        timestamp: UTC timestamp of the snapshot
        geography: Geographic scope
        dxy: US Dollar Index value
        real_yield: US Real Yield value
        cpi: Consumer Price Index value
        fed_event: Recent Fed event description
        nfp: Non-Farm Payrolls value
        geopolitical_events: List of active geopolitical events
        overall_assessment: Summary assessment
        confidence: Confidence in this assessment (0.0-1.0)
    """

    def __init__(
        self,
        timestamp: datetime,
        geography: str = "US",
        dxy: float = 0.0,
        real_yield: float = 0.0,
        cpi: float = 0.0,
        fed_event: str = "",
        nfp: float = 0.0,
        geopolitical_events: Optional[List[str]] = None,
        overall_assessment: str = "",
        confidence: float = 0.0,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"MacroState|{geography}|{timestamp.isoformat()}|{dxy}|{cpi}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.timestamp = timestamp
        self.geography = geography
        self.dxy = dxy
        self.real_yield = real_yield
        self.cpi = cpi
        self.fed_event = fed_event
        self.nfp = nfp
        self.geopolitical_events: List[str] = geopolitical_events or []
        self.overall_assessment = overall_assessment
        self.confidence = confidence

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "geography": self.geography,
            "dxy": self.dxy,
            "real_yield": self.real_yield,
            "cpi": self.cpi,
            "fed_event": self.fed_event,
            "nfp": self.nfp,
            "geopolitical_events": sorted(self.geopolitical_events),
            "overall_assessment": self.overall_assessment,
            "confidence": self.confidence,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "timestamp": self.timestamp.isoformat(),
            "geography": self.geography,
            "dxy": self.dxy,
            "real_yield": self.real_yield,
            "cpi": self.cpi,
            "fed_event": self.fed_event,
            "nfp": self.nfp,
            "geopolitical_events": self.geopolitical_events,
            "overall_assessment": self.overall_assessment,
            "confidence": self.confidence,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MacroState":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.geography = data.get("geography", "US")
        obj.dxy = data.get("dxy", 0.0)
        obj.real_yield = data.get("real_yield", 0.0)
        obj.cpi = data.get("cpi", 0.0)
        obj.fed_event = data.get("fed_event", "")
        obj.nfp = data.get("nfp", 0.0)
        obj.geopolitical_events = list(data.get("geopolitical_events", []))
        obj.overall_assessment = data.get("overall_assessment", "")
        obj.confidence = data.get("confidence", 0.0)
        return obj


class HistoricalScenario(BaseObject):
    """
    A complete historical market scenario for comparison with current conditions.

    Bundles together:
        - A MarketSnapshot or range of snapshots
        - A MarketRegime classification
        - MacroState context (by reference)
        - Outcome information (what happened next)
        - Similarity score for comparison

    Attributes:
        name: Human-readable name for this scenario
        description: Detailed description
        start_time: When the scenario began
        end_time: When the scenario ended
        snapshot_ids: IDs of related MarketSnapshot objects
        regime_id: ID of the MarketRegime
        macro_id: ID of the MacroState
        outcome: What happened after this scenario
        price_outcome: Price change outcome (e.g., "+2.5%")
        volatility_outcome: Volatility change outcome
        max_favorable_movement: Maximum favorable excursion
        max_adverse_movement: Maximum adverse excursion
        tags: Categorization tags
        dataset_source: Source dataset identifier
        similarity_score: Computed similarity to another scenario (0.0-1.0)
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        snapshot_ids: Optional[List[str]] = None,
        regime_id: str = "",
        macro_id: str = "",
        outcome: str = "",
        price_outcome: float = 0.0,
        volatility_outcome: float = 0.0,
        max_favorable_movement: float = 0.0,
        max_adverse_movement: float = 0.0,
        tags: Optional[List[str]] = None,
        dataset_source: str = "",
        similarity_score: float = 0.0,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"HistoricalScenario|{name}|{description[:50]}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.name = name
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.snapshot_ids: List[str] = snapshot_ids or []
        self.regime_id = regime_id
        self.macro_id = macro_id
        self.outcome = outcome
        self.price_outcome = price_outcome
        self.volatility_outcome = volatility_outcome
        self.max_favorable_movement = max_favorable_movement
        self.max_adverse_movement = max_adverse_movement
        self.tags: List[str] = tags or []
        self.dataset_source = dataset_source
        self.similarity_score = similarity_score

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else "",
            "end_time": self.end_time.isoformat() if self.end_time else "",
            "snapshot_ids": sorted(self.snapshot_ids),
            "regime_id": self.regime_id,
            "macro_id": self.macro_id,
            "outcome": self.outcome,
            "price_outcome": self.price_outcome,
            "volatility_outcome": self.volatility_outcome,
            "max_favorable_movement": self.max_favorable_movement,
            "max_adverse_movement": self.max_adverse_movement,
            "tags": sorted(self.tags),
            "dataset_source": self.dataset_source,
            "similarity_score": self.similarity_score,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "name": self.name,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "snapshot_ids": self.snapshot_ids,
            "regime_id": self.regime_id,
            "macro_id": self.macro_id,
            "outcome": self.outcome,
            "price_outcome": self.price_outcome,
            "volatility_outcome": self.volatility_outcome,
            "max_favorable_movement": self.max_favorable_movement,
            "max_adverse_movement": self.max_adverse_movement,
            "tags": self.tags,
            "dataset_source": self.dataset_source,
            "similarity_score": self.similarity_score,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "HistoricalScenario":
        obj = super().from_dict(data)
        obj.name = data["name"]
        obj.description = data.get("description", "")
        obj.start_time = parse_timestamp(data["start_time"]) if data.get("start_time") else None
        obj.end_time = parse_timestamp(data["end_time"]) if data.get("end_time") else None
        obj.snapshot_ids = list(data.get("snapshot_ids", []))
        obj.regime_id = data.get("regime_id", "")
        obj.macro_id = data.get("macro_id", "")
        obj.outcome = data.get("outcome", "")
        obj.price_outcome = data.get("price_outcome", data.get("outcome_price_change", 0.0))
        obj.volatility_outcome = data.get("volatility_outcome", 0.0)
        obj.max_favorable_movement = data.get("max_favorable_movement", 0.0)
        obj.max_adverse_movement = data.get("max_adverse_movement", 0.0)
        obj.tags = list(data.get("tags", []))
        obj.dataset_source = data.get("dataset_source", "")
        obj.similarity_score = data.get("similarity_score", 0.0)
        return obj
