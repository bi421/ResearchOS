"""
Observation objects — the atomic units of market data.

Based on Article XVII: Object Model — Observation Layer.
Based on Article XVI: Scientific Reasoning Framework — Observation Layer.

An Observation is any raw, factual data point about market conditions
that can be objectively verified. Observations are the starting point
of the ResearchOS reasoning pipeline.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_observation_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now


class Observation(BaseObject):
    """
    The atomic unit of market data.

    A single, objectively verifiable data point about market conditions.
    Observations are immutable once created and validated.

    Attributes:
        source: Data source identifier (e.g., "MACRO:CPI_YOY")
        timestamp: UTC timestamp of the observation
        value: The raw observed value
        unit: Unit of measurement
        frequency: Data frequency
        geography: Geographic scope
        asset_class: Asset class
        quality_flags: Data quality flags
        retrieval_time: When data was retrieved
        retrieval_method: Fixed retrieval procedure identifier
        validated: Whether validation passed
    """

    def __init__(
        self,
        source: str,
        timestamp: datetime,
        value: Any,
        unit: str = "",
        frequency: str = "",
        geography: str = "",
        asset_class: str = "",
        quality_flags: Optional[List[str]] = None,
        retrieval_time: Optional[datetime] = None,
        retrieval_method: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        # Generate deterministic ID from source + timestamp + value
        if id is None:
            id = generate_observation_id(source, timestamp.isoformat(), value)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.source = source
        self.timestamp = timestamp
        self.value = value
        self.unit = unit
        self.frequency = frequency
        self.geography = geography
        self.asset_class = asset_class
        self.quality_flags: List[str] = quality_flags or []
        self.retrieval_time = retrieval_time or utc_now()
        self.retrieval_method = retrieval_method
        self.validated: bool = False

    def validate(self, reference_time: Optional[datetime] = None) -> bool:
        """
        Validate this observation against three criteria:
        1. Completeness — No missing values
        2. Timeliness — Timestamp is before the reference time
        3. Integrity — Value matches expected format and range

        Args:
            reference_time: The time to compare against for timeliness.
                            If None, uses the current time (non-deterministic).

        Returns:
            True if validation passes.
        """
        # Completeness check
        if self.value is None:
            return False

        # Timeliness check (timestamp must be before reference_time)
        check_time = reference_time or utc_now()
        if self.timestamp > check_time:
            return False

        # Integrity check (value must be a valid type)
        if not isinstance(self.value, (int, float, str, bool)):
            return False

        self.validated = True
        self.lifecycle.transition(
            LifecycleStage.VALIDATED,
            reason="Observation validated",
        )
        return True

    def _to_hashable_dict(self) -> dict:
        return {
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "unit": self.unit,
            "frequency": self.frequency,
            "geography": self.geography,
            "asset_class": self.asset_class,
            "quality_flags": sorted(self.quality_flags),
            "validated": self.validated,
            "retrieval_time": self.retrieval_time.isoformat() if self.retrieval_time else "",
            "retrieval_method": self.retrieval_method,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "unit": self.unit,
            "frequency": self.frequency,
            "geography": self.geography,
            "asset_class": self.asset_class,
            "quality_flags": self.quality_flags,
            "retrieval_time": self.retrieval_time.isoformat(),
            "retrieval_method": self.retrieval_method,
            "validated": self.validated,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Observation":
        obj = super().from_dict(data)
        obj.source = data["source"]
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.value = data["value"]
        obj.unit = data.get("unit", "")
        obj.frequency = data.get("frequency", "")
        obj.geography = data.get("geography", "")
        obj.asset_class = data.get("asset_class", "")
        obj.quality_flags = list(data.get("quality_flags", []))
        obj.retrieval_time = parse_timestamp(data["retrieval_time"]) if data.get("retrieval_time") else None
        obj.retrieval_method = data.get("retrieval_method", "")
        obj.validated = data.get("validated", False)
        return obj


class MarketState(BaseObject):
    """
    A snapshot of market conditions at a specific point in time.

    Based on Article XVII: Object Model — MarketState.

    Attributes:
        timestamp: UTC timestamp
        asset: Asset identifier
        regime: Market regime
        trend: Price trend
        volatility: Current volatility level
        liquidity: Liquidity level
        sentiment: Sentiment score (0.0-1.0)
        observations: All observations in this state
        confidence: Confidence in this state (0.0-1.0)
    """

    def __init__(
        self,
        timestamp: datetime,
        asset: str,
        regime: str = "",
        trend: str = "",
        volatility: float = 0.0,
        liquidity: str = "",
        sentiment: float = 0.0,
        observations: Optional[List[str]] = None,
        confidence: float = 0.0,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp
        self.asset = asset
        self.regime = regime
        self.trend = trend
        self.volatility = volatility
        self.liquidity = liquidity
        self.sentiment = sentiment
        self.observations: List[str] = observations or []
        self.confidence = confidence

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "timestamp": self.timestamp.isoformat(),
            "asset": self.asset,
            "regime": self.regime,
            "trend": self.trend,
            "volatility": self.volatility,
            "liquidity": self.liquidity,
            "sentiment": self.sentiment,
            "observations": self.observations,
            "confidence": self.confidence,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MarketState":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.asset = data["asset"]
        obj.regime = data.get("regime", "")
        obj.trend = data.get("trend", "")
        obj.volatility = data.get("volatility", 0.0)
        obj.liquidity = data.get("liquidity", "")
        obj.sentiment = data.get("sentiment", 0.0)
        obj.observations = list(data.get("observations", []))
        obj.confidence = data.get("confidence", 0.0)
        return obj

    def _to_hashable_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "asset": self.asset,
            "regime": self.regime,
            "trend": self.trend,
            "volatility": self.volatility,
            "liquidity": self.liquidity,
            "sentiment": self.sentiment,
            "observations": sorted(self.observations),
            "confidence": self.confidence,
            "ontology_tags": sorted(self.ontology_tags),
        }


class MacroState(BaseObject):
    """
    A snapshot of macroeconomic conditions.

    Based on Article XVII: Object Model — MacroState.

    Attributes:
        timestamp: UTC timestamp
        geography: Geographic scope
        regime: Economic regime
        inflation: Inflation rate
        growth: GDP growth rate
        policy_stance: Central bank policy stance
        risk_factors: Key macro risks
        observations: All observations in this state
        confidence: Confidence in this state (0.0-1.0)
    """

    def __init__(
        self,
        timestamp: datetime,
        geography: str,
        regime: str = "",
        inflation: float = 0.0,
        growth: float = 0.0,
        policy_stance: str = "",
        risk_factors: Optional[List[str]] = None,
        observations: Optional[List[str]] = None,
        confidence: float = 0.0,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        super().__init__(id=id, ontology_tags=ontology_tags)
        self.timestamp = timestamp
        self.geography = geography
        self.regime = regime
        self.inflation = inflation
        self.growth = growth
        self.policy_stance = policy_stance
        self.risk_factors: List[str] = risk_factors or []
        self.observations: List[str] = observations or []
        self.confidence = confidence

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "timestamp": self.timestamp.isoformat(),
            "geography": self.geography,
            "regime": self.regime,
            "inflation": self.inflation,
            "growth": self.growth,
            "policy_stance": self.policy_stance,
            "risk_factors": self.risk_factors,
            "observations": self.observations,
            "confidence": self.confidence,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "MacroState":
        obj = super().from_dict(data)
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.geography = data["geography"]
        obj.regime = data.get("regime", "")
        obj.inflation = data.get("inflation", 0.0)
        obj.growth = data.get("growth", 0.0)
        obj.policy_stance = data.get("policy_stance", "")
        obj.risk_factors = list(data.get("risk_factors", []))
        obj.observations = list(data.get("observations", []))
        obj.confidence = data.get("confidence", 0.0)
        return obj

    def _to_hashable_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "geography": self.geography,
            "regime": self.regime,
            "inflation": self.inflation,
            "growth": self.growth,
            "policy_stance": self.policy_stance,
            "risk_factors": sorted(self.risk_factors),
            "observations": sorted(self.observations),
            "confidence": self.confidence,
            "ontology_tags": sorted(self.ontology_tags),
        }
