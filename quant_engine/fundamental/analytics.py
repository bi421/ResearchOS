"""
Fundamental Research Engine — deterministic macro research analytics.

Modules:
    - Macro event normalization
    - Surprise scoring (actual vs forecast)
    - Interest rate / inflation / employment / GDP analysis
    - Central bank decision tracking
    - Treasury yield curve research
    - Dollar index & gold macro factor modeling
    - Commodity relationship research
    - Bond market analytics
    - Economic calendar abstraction
    - News-event normalization (deterministic text features)

No online API integration — deterministic architecture and models only.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

from researchos.quant_engine.fundamental.contracts import (
    CommodityBasket,
    EconomicCalendarEvent,
    EventSeverity,
    MacroDataPoint,
    MacroFactorModel,
    NewsEvent,
)

# ──────────────────────────────────────────────
# Macro data analytics
# ──────────────────────────────────────────────


def surprise_score(point: MacroDataPoint) -> float:
    """Standardized surprise: (actual - forecast) / |forecast|."""
    if point.forecast == 0:
        return 0.0
    return (point.value - point.forecast) / abs(point.forecast)


def classify_surprise(point: MacroDataPoint) -> str:
    """Classify the surprise as positive/negative/neutral."""
    s = surprise_score(point)
    if s > 0.01:
        return "positive"
    if s < -0.01:
        return "negative"
    return "neutral"


def macro_series_statistics(points: Sequence[MacroDataPoint]) -> dict[str, float]:
    """Summary statistics of a macro indicator series."""
    values = [p.value for p in points]
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "count": 0.0}
    n = len(values)
    m = sum(values) / n
    var = sum((v - m) ** 2 for v in values) / n
    return {
        "mean": m,
        "std": math.sqrt(var),
        "min": min(values),
        "max": max(values),
        "count": float(n),
    }


# ──────────────────────────────────────────────
# Central bank & policy analytics
# ──────────────────────────────────────────────


def policy_rate_delta(previous_rate: float, new_rate: float) -> float:
    """Change in policy rate (in percentage points)."""
    return new_rate - previous_rate


def classify_policy_action(previous_rate: float, new_rate: float) -> str:
    d = policy_rate_delta(previous_rate, new_rate)
    if d > 0:
        return "hike"
    if d < 0:
        return "cut"
    return "hold"


# ──────────────────────────────────────────────
# Treasury yield curve research
# ──────────────────────────────────────────────


def yield_curve_metrics(
    maturities: Sequence[str],
    yields: Sequence[float],
) -> dict[str, float]:
    """Slope, level, and curvature proxies for a yield curve."""
    if len(maturities) != len(yields) or len(yields) < 3:
        return {"level": 0.0, "slope": 0.0, "curvature": 0.0}

    def _to_years(m: str) -> float:
        m = m.strip().lower()
        if m.endswith("y"):
            return float(m[:-1])
        if m.endswith("m"):
            return float(m[:-1]) / 12.0
        return float(m)

    years = [_to_years(m) for m in maturities]
    n = len(years)
    my = sum(years) / n
    mx = sum(yields) / n
    num = sum((years[i] - my) * (yields[i] - mx) for i in range(n))
    den = sum((years[i] - my) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0.0

    level = yields[-1]
    short = yields[0]
    long_ = yields[-1]
    mid = yields[n // 2]
    curvature = (short + long_) - 2.0 * mid

    return {"level": level, "slope": slope, "curvature": curvature}


# ──────────────────────────────────────────────
# Commodity relationships
# ──────────────────────────────────────────────


def commodity_correlations(basket: CommodityBasket) -> dict[str, float]:
    """Correlations between gold and other commodities."""
    basket.validate()
    if len(basket.gold) < 2:
        return {}

    def _corr(x: list[float], y: list[float]) -> float:
        n = len(x)
        mx = sum(x) / n
        my = sum(y) / n
        num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
        dx = math.sqrt(sum((v - mx) ** 2 for v in x))
        dy = math.sqrt(sum((v - my) ** 2 for v in y))
        if dx == 0 or dy == 0:
            return 0.0
        return num / (dx * dy)

    return {
        "gold_oil": _corr(basket.gold, basket.oil),
        "gold_silver": _corr(basket.gold, basket.silver),
        "gold_copper": _corr(basket.gold, basket.copper),
        "oil_silver": _corr(basket.oil, basket.silver),
        "oil_copper": _corr(basket.oil, basket.copper),
        "silver_copper": _corr(basket.silver, basket.copper),
    }


def commodity_ratio(basket: CommodityBasket) -> dict[str, float]:
    """Research ratios: gold/silver, gold/oil, copper/gold."""
    basket.validate()
    gold_last = basket.gold[-1] if basket.gold else 0.0
    silver_last = basket.silver[-1] if basket.silver else 0.0
    oil_last = basket.oil[-1] if basket.oil else 0.0
    copper_last = basket.copper[-1] if basket.copper else 0.0
    out = {}
    if silver_last != 0:
        out["gold_silver_ratio"] = gold_last / silver_last
    if oil_last != 0:
        out["gold_oil_ratio"] = gold_last / oil_last
    if gold_last != 0:
        out["copper_gold_ratio"] = copper_last / gold_last
    return out


# ──────────────────────────────────────────────
# Bond market analytics
# ──────────────────────────────────────────────


def bond_convexity(
    price: float,
    duration: float,
    yield_change: float,
    convexity: float,
) -> float:
    """Approximate bond price change from duration + convexity."""
    return (-duration * yield_change + 0.5 * convexity * yield_change**2) * price


def duration_estimate(
    coupon: float,
    yield_to_maturity: float,
    periods: int,
) -> float:
    """Macaulay duration approximation for a fixed-coupon bond."""
    if periods <= 0:
        return 0.0
    if yield_to_maturity + 1.0 == 0:
        return float(periods)
    num_sum = sum(((t + 1) * coupon / (1.0 + yield_to_maturity) ** (t + 1)) for t in range(periods))
    maturity_value = periods * (1.0 + coupon) / (1.0 + yield_to_maturity) ** periods
    price = (
        sum(coupon / (1.0 + yield_to_maturity) ** (t + 1) for t in range(periods))
        + (1.0 + coupon) / (1.0 + yield_to_maturity) ** periods
    )
    if price == 0:
        return 0.0
    return (num_sum + maturity_value) / price


def real_yield(nominal_yield: float, inflation_rate: float) -> float:
    """Real yield via linear proxy: nominal_yield - inflation_rate."""
    return nominal_yield - inflation_rate


def fisher_real_yield(nominal_yield: float, inflation_rate: float) -> float:
    """Real yield via exact Fisher equation: ((1 + r_nom) / (1 + r_inf)) - 1."""
    nom = nominal_yield / 100.0 if abs(nominal_yield) > 1.0 else nominal_yield
    inf = inflation_rate / 100.0 if abs(inflation_rate) > 1.0 else inflation_rate
    if 1.0 + inf == 0:
        return 0.0
    real_dec = ((1.0 + nom) / (1.0 + inf)) - 1.0
    return real_dec * 100.0 if abs(nominal_yield) > 1.0 else real_dec


def real_yield_series(
    nominal_yields: Sequence[float],
    inflation_rates: Sequence[float],
    exact_fisher: bool = False,
) -> list[float]:
    """Compute real yield series from nominal yields and inflation rates."""
    if len(nominal_yields) != len(inflation_rates):
        raise ValueError("nominal_yields and inflation_rates must have equal length")
    if exact_fisher:
        return [fisher_real_yield(n, i) for n, i in zip(nominal_yields, inflation_rates)]
    return [real_yield(n, i) for n, i in zip(nominal_yields, inflation_rates)]


def bond_spread(yield_a: float, yield_b: float) -> float:
    """Yield spread between two bonds or instruments (yield_a - yield_b)."""
    return yield_a - yield_b


def bond_spread_series(
    yields_a: Sequence[float],
    yields_b: Sequence[float],
) -> list[float]:
    """Compute yield spread series."""
    if len(yields_a) != len(yields_b):
        raise ValueError("yields_a and yields_b must have equal length")
    return [a - b for a, b in zip(yields_a, yields_b)]


def yield_spread_metrics(yields_by_maturity: dict[str, float]) -> dict[str, float]:
    """
    Key benchmark yield curve spreads from a dictionary of maturity → yield.

    Keys normalized to uppercase e.g. {"2Y": 4.5, "10Y": 4.2, "30Y": 4.4, "3M": 5.2}.
    """
    normalized = {k.strip().upper(): float(v) for k, v in yields_by_maturity.items()}
    out: dict[str, float] = {}
    if "10Y" in normalized and "2Y" in normalized:
        out["10y_2y_spread"] = normalized["10Y"] - normalized["2Y"]
    if "30Y" in normalized and "10Y" in normalized:
        out["30y_10y_spread"] = normalized["30Y"] - normalized["10Y"]
    if "10Y" in normalized and "3M" in normalized:
        out["10y_3m_spread"] = normalized["10Y"] - normalized["3M"]
    return out


# ──────────────────────────────────────────────
# Economic calendar abstraction
# ──────────────────────────────────────────────


def filter_high_severity(events: Sequence[EconomicCalendarEvent]) -> list[EconomicCalendarEvent]:
    return [e for e in events if e.severity in (EventSeverity.HIGH, EventSeverity.CRITICAL)]


def events_by_country(events: Sequence[EconomicCalendarEvent], country: str) -> list[EconomicCalendarEvent]:
    return [e for e in events if e.country.upper() == country.upper()]


def concentration_by_indicator(events: Sequence[EconomicCalendarEvent]) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in events:
        key = e.indicator.value if e.indicator else "other"
        out[key] = out.get(key, 0) + 1
    return out


def calendar_density(events: Sequence[EconomicCalendarEvent]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for e in events:
        counts[e.time] = counts.get(e.time, 0) + 1
    return {k: float(v) for k, v in counts.items()}


# ──────────────────────────────────────────────
# News-event normalization
# ──────────────────────────────────────────────


def normalize_news_text(raw: str) -> str:
    """Deterministic news text normalization."""
    text = raw.lower().strip()
    text = re.sub(r"[^a-z0-9\s%$.-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def keyword_sentiment(text: str) -> float:
    """Simple deterministic lexicon-based sentiment score in [-1, 1]."""
    positive = {
        "beat",
        "surge",
        "gain",
        "growth",
        "improve",
        "strong",
        "rise",
        "up",
        "positive",
        "exceeds",
        "record",
        "boost",
        "rally",
    }
    negative = {
        "miss",
        "fall",
        "drop",
        "decline",
        "weak",
        "slow",
        "downgrade",
        "loss",
        "cut",
        "negative",
        "below",
        "fear",
        "plunge",
        "slump",
    }
    words = set(normalize_news_text(text).split())
    pos_hits = words & positive
    neg_hits = words & negative
    if not pos_hits and not neg_hits:
        return 0.0
    return (len(pos_hits) - len(neg_hits)) / max(len(pos_hits | neg_hits), 1)


def normalize_news_event(raw_headline: str, source: str = "") -> NewsEvent:
    """Create a normalized NewsEvent with deterministic features."""
    normalized = normalize_news_text(raw_headline)
    sentiment = keyword_sentiment(raw_headline)
    severity = EventSeverity.MEDIUM
    if abs(sentiment) >= 0.6:
        severity = EventSeverity.HIGH
    return NewsEvent(
        headline=raw_headline,
        source=source,
        sentiment=sentiment,
        normalized_text=normalized,
        severity=severity,
    )


# ──────────────────────────────────────────────
# Simple deterministic macro factor model
# ──────────────────────────────────────────────


def fit_macro_factor_model(
    target: Sequence[float],
    features: dict[str, Sequence[float]],
) -> MacroFactorModel:
    """
    Fit a deterministic OLS-style macro factor model via normal equations.

    Returns:
        MacroFactorModel with coefficients, intercept, and R².
    """
    n = len(target)
    if n == 0:
        raise ValueError("target must be non-empty")
    keys = sorted(features.keys())
    for k in keys:
        if len(features[k]) != n:
            raise ValueError(f"feature '{k}' length does not match target")

    X = [[1.0] + [features[k][i] for k in keys] for i in range(n)]
    y = list(target)

    Xt = _transpose(X)
    A = _mat_mul(Xt, X)
    b = _mat_vec_mul(Xt, y)
    coefs = _solve_linear(A, b)

    intercept = coefs[0]
    coefficients = {keys[i]: coefs[i + 1] for i in range(len(keys))}

    y_mean = sum(y) / n
    ss_tot = sum((v - y_mean) ** 2 for v in y)
    ss_res = 0.0
    for i in range(n):
        pred = intercept + sum(coefficients[k] * features[k][i] for k in keys)
        ss_res += (y[i] - pred) ** 2
    r2 = 1.0 - ss_res / ss_tot if ss_tot != 0 else 0.0

    return MacroFactorModel(
        factor_name="macro_factor",
        coefficients=coefficients,
        intercept=intercept,
        r_squared=r2,
    )


def _transpose(m: list[list[float]]) -> list[list[float]]:
    if not m:
        return []
    return [[m[i][j] for i in range(len(m))] for j in range(len(m[0]))]


def _mat_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    n, k = len(a), len(a[0]) if a else 0
    m = len(b[0]) if b else 0
    out = [[0.0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            out[i][j] = sum(a[i][t] * b[t][j] for t in range(k))
    return out


def _mat_vec_mul(a: list[list[float]], v: list[float]) -> list[float]:
    return [sum(row[i] * v[i] for i in range(len(v))) for row in a]


def _solve_linear(a: list[list[float]], b: list[float]) -> list[float]:
    """Solve Ax=b by Gaussian elimination with partial pivoting."""
    n = len(b)
    aug = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[pivot] = aug[pivot], aug[col]
        pv = aug[col][col]
        if abs(pv) < 1e-12:
            return [0.0] * n
        for r in range(col + 1, n):
            factor = aug[r][col] / pv
            for c in range(col, n + 1):
                aug[r][c] -= factor * aug[col][c]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = aug[i][n] - sum(aug[i][j] * x[j] for j in range(i + 1, n))
        x[i] = s / aug[i][i]
    return x
