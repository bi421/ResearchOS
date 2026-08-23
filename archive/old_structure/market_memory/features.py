"""
Feature computation for market memory objects.

Provides deterministic feature extraction from MarketSnapshot data
for pattern recognition and similarity comparison.
"""

from __future__ import annotations

from dataclasses import dataclass

from researchos.market_memory.models import MarketSnapshot


@dataclass
class FeatureSet:
    """
    A deterministic set of computed features from a MarketSnapshot.

    All features are derived from OHLCV data and are purely
    computational (no fitting, no randomness).
    """

    asset: str
    timestamp: str
    timeframe: str

    # Price-based features
    body: float  # |close - open|
    upper_wick: float  # high - max(open, close)
    lower_wick: float  # min(open, close) - low
    range_pct: float  # (high - low) / close * 100
    body_pct: float  # |close - open| / (high - low) if range > 0

    # Trend features
    is_bullish: bool
    is_bearish: bool
    close_position: float  # Where close sits in range (0=low, 1=high)

    # Volume features
    volume_ratio: float  # volume relative to typical (default 1.0)

    def to_dict(self) -> dict:
        return {
            "asset": self.asset,
            "timestamp": self.timestamp,
            "timeframe": self.timeframe,
            "body": self.body,
            "upper_wick": self.upper_wick,
            "lower_wick": self.lower_wick,
            "range_pct": self.range_pct,
            "body_pct": self.body_pct,
            "is_bullish": self.is_bullish,
            "is_bearish": self.is_bearish,
            "close_position": self.close_position,
            "volume_ratio": self.volume_ratio,
        }


def compute_features(snapshot: MarketSnapshot) -> FeatureSet:
    """
    Compute deterministic features from a MarketSnapshot.

    Args:
        snapshot: The market snapshot to analyze.

    Returns:
        A FeatureSet with all computed features.
    """
    o, h, low, c = snapshot.open, snapshot.high, snapshot.low, snapshot.close
    price_range = h - low

    body = abs(c - o)
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - low
    range_pct = (price_range / c * 100.0) if c != 0 else 0.0
    body_pct = (body / price_range) if price_range > 0 else 0.0
    is_bullish = c > o
    is_bearish = c < o
    close_position = ((c - low) / price_range) if price_range > 0 else 0.5
    volume_ratio = 1.0  # No historical baseline by default

    return FeatureSet(
        asset=snapshot.asset,
        timestamp=snapshot.timestamp.isoformat(),
        timeframe=snapshot.timeframe,
        body=body,
        upper_wick=upper_wick,
        lower_wick=lower_wick,
        range_pct=range_pct,
        body_pct=body_pct,
        is_bullish=is_bullish,
        is_bearish=is_bearish,
        close_position=close_position,
        volume_ratio=volume_ratio,
    )
