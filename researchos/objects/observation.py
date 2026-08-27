from __future__ import annotations

from datetime import datetime
from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_observation_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now


class Observation(BaseObject):
    """
    Atomic factual observation.

    The value field is intentionally preserved exactly because it is part
    of identity, hashing, validation and serialization.
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
        quality_flags: list[str] | None = None,
        retrieval_time: datetime | None = None,
        retrieval_method: str = "",
        validated: bool = False,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if isinstance(timestamp, str):
            timestamp = parse_timestamp(timestamp)

        if id is None:
            id = generate_observation_id(
                source,
                timestamp.isoformat(),
                value,
            )

        super().__init__(
            id=id,
            ontology_tags=ontology_tags,
        )

        self.source = source
        self.timestamp = timestamp
        self.value = value
        self.unit = unit
        self.frequency = frequency
        self.geography = geography
        self.asset_class = asset_class
        self.quality_flags = list(quality_flags or [])
        self.retrieval_time = retrieval_time
        self.retrieval_method = retrieval_method
        self.validated = bool(validated)

    def validate(
        self,
        reference_time: datetime | None = None,
    ) -> bool:
        if not self.source:
            raise ValueError("Observation source cannot be empty")

        if self.value is None:
            return False

        check_time = reference_time or utc_now()

        if self.timestamp > check_time:
            return False

        if not isinstance(
            self.value,
            (int, float, str, bool),
        ):
            return False

        self.validated = True

        try:
            self.lifecycle.transition(
                LifecycleStage.VALIDATED,
                reason="Observation validated",
            )
        except Exception:
            pass

        self._hash = None
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
            "retrieval_time": (self.retrieval_time.isoformat() if self.retrieval_time else ""),
            "retrieval_method": self.retrieval_method,
            "validated": self.validated,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        data = super().to_dict()

        data.update(
            {
                "source": self.source,
                "timestamp": self.timestamp.isoformat(),
                "value": self.value,
                "unit": self.unit,
                "frequency": self.frequency,
                "geography": self.geography,
                "asset_class": self.asset_class,
                "quality_flags": list(self.quality_flags),
                "retrieval_time": (self.retrieval_time.isoformat() if self.retrieval_time else None),
                "retrieval_method": self.retrieval_method,
                "validated": self.validated,
            }
        )

        return data

    @classmethod
    def from_dict(cls, data: dict) -> Observation:
        obj = super().from_dict(data)

        obj.source = data["source"]
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.value = data["value"]
        obj.unit = data.get("unit", "")
        obj.frequency = data.get("frequency", "")
        obj.geography = data.get("geography", "")
        obj.asset_class = data.get("asset_class", "")
        obj.quality_flags = list(data.get("quality_flags", []))

        retrieval_time = data.get("retrieval_time")
        obj.retrieval_time = parse_timestamp(retrieval_time) if retrieval_time else None

        obj.retrieval_method = data.get(
            "retrieval_method",
            "",
        )
        obj.validated = bool(data.get("validated", False))

        return obj


class MarketState(BaseObject):
    def __init__(
        self,
        timestamp: datetime,
        asset: str,
        regime: str = "",
        trend: str = "",
        volatility: float = 0.0,
        liquidity: str = "",
        sentiment: float = 0.0,
        observations: list[str] | None = None,
        confidence: float = 0.0,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        super().__init__(
            id=id,
            ontology_tags=ontology_tags,
        )

        self.timestamp = timestamp
        self.asset = asset
        self.regime = regime
        self.trend = trend
        self.volatility = volatility
        self.liquidity = liquidity
        self.sentiment = sentiment
        self.observations = list(observations or [])
        self.confidence = confidence

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

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "asset": self.asset,
                "regime": self.regime,
                "trend": self.trend,
                "volatility": self.volatility,
                "liquidity": self.liquidity,
                "sentiment": self.sentiment,
                "observations": list(self.observations),
                "confidence": self.confidence,
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: dict) -> MarketState:
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


class MacroState(BaseObject):
    def __init__(
        self,
        timestamp: datetime,
        geography: str,
        regime: str = "",
        inflation: float = 0.0,
        growth: float = 0.0,
        policy_stance: str = "",
        risk_factors: list[str] | None = None,
        observations: list[str] | None = None,
        confidence: float = 0.0,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        super().__init__(
            id=id,
            ontology_tags=ontology_tags,
        )

        self.timestamp = timestamp
        self.geography = geography
        self.regime = regime
        self.inflation = inflation
        self.growth = growth
        self.policy_stance = policy_stance
        self.risk_factors = list(risk_factors or [])
        self.observations = list(observations or [])
        self.confidence = confidence

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

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update(
            {
                "timestamp": self.timestamp.isoformat(),
                "geography": self.geography,
                "regime": self.regime,
                "inflation": self.inflation,
                "growth": self.growth,
                "policy_stance": self.policy_stance,
                "risk_factors": list(self.risk_factors),
                "observations": list(self.observations),
                "confidence": self.confidence,
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: dict) -> MacroState:
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
