"""
Fundamental Research Engine — contracts, enums, and dataclass models.

Research models for macro events, interest rates, inflation, employment,
GDP, central bank decisions, CPI/PPI/PMI, treasury yields, dollar index,
gold macro factors, commodity relationships, bond markets, economic
calendar abstraction, and news-event normalization.

No online API integration — deterministic architecture and models only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MacroIndicator(str, Enum):
    INTEREST_RATE = "interest_rate"
    INFLATION = "inflation"
    CPI = "cpi"
    PPI = "ppi"
    PMI = "pmi"
    EMPLOYMENT = "employment"
    GDP = "gdp"
    TREASURY_YIELD = "treasury_yield"
    DOLLAR_INDEX = "dollar_index"
    CENTRAL_BANK_RATE = "central_bank_rate"
    REAL_YIELD = "real_yield"
    BOND_SPREAD = "bond_spread"


class EventSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CentralBank(str, Enum):
    FED = "Fed"
    ECB = "ECB"
    BOE = "BoE"
    BOJ = "BoJ"
    SNB = "SNB"
    RBA = "RBA"
    BOJ2 = "BOJ"


@dataclass(frozen=True)
class MacroDataPoint:
    """A single macro data release or observation."""

    indicator: MacroIndicator
    value: float
    previous: float = 0.0
    forecast: float = 0.0
    country: str = "US"
    date: str = ""
    source: str = ""

    @property
    def surprise(self) -> float:
        return self.value - self.forecast

    @property
    def mom_change(self) -> float:
        return self.value - self.previous

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator": self.indicator.value,
            "value": self.value,
            "previous": self.previous,
            "forecast": self.forecast,
            "surprise": self.surprise,
            "mom_change": self.mom_change,
            "country": self.country,
            "date": self.date,
            "source": self.source,
        }


@dataclass(frozen=True)
class EconomicCalendarEvent:
    """A scheduled economic calendar entry."""

    event_id: str
    name: str
    country: str = "US"
    time: str = ""
    severity: EventSeverity = EventSeverity.MEDIUM
    indicator: Optional[MacroIndicator] = None
    forecast: float = 0.0
    previous: float = 0.0
    currency: str = "USD"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "name": self.name,
            "country": self.country,
            "time": self.time,
            "severity": self.severity.value,
            "indicator": self.indicator.value if self.indicator else None,
            "forecast": self.forecast,
            "previous": self.previous,
            "currency": self.currency,
        }


@dataclass(frozen=True)
class CommodityBasket:
    """Commodity price series for cross-asset research."""

    oil: List[float] = field(default_factory=list)
    silver: List[float] = field(default_factory=list)
    copper: List[float] = field(default_factory=list)
    gold: List[float] = field(default_factory=list)
    name: str = "global_commodities"

    def validate(self) -> None:
        lengths = {len(self.oil), len(self.silver), len(self.copper), len(self.gold)}
        if len(lengths) > 1:
            raise ValueError(f"All commodity series must have equal length, got {lengths}")


@dataclass(frozen=True)
class NewsEvent:
    """A normalized news event."""

    headline: str
    source: str = ""
    timestamp: str = ""
    sentiment: float = 0.0
    topic: str = ""
    normalized_text: str = ""
    severity: EventSeverity = EventSeverity.MEDIUM

    def to_dict(self) -> Dict[str, Any]:
        return {
            "headline": self.headline,
            "source": self.source,
            "timestamp": self.timestamp,
            "sentiment": self.sentiment,
            "topic": self.topic,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class MacroFactorModel:
    """A fitted deterministic macro factor model."""

    factor_name: str = ""
    coefficients: Dict[str, float] = field(default_factory=dict)
    intercept: float = 0.0
    r_squared: float = 0.0

    def predict(self, features: Dict[str, float]) -> float:
        return self.intercept + sum(
            self.coefficients[k] * features.get(k, 0.0) for k in self.coefficients
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_name": self.factor_name,
            "coefficients": dict(sorted(self.coefficients.items())),
            "intercept": self.intercept,
            "r_squared": self.r_squared,
        }
