"""
Historical Analytics Engine — deterministic historical research analytics.

Modules:
    - Historical pattern mining (N-day return patterns)
    - Market regime statistics (bull/bear/sideways/vol regimes)
    - Seasonality (month-of-year, day-of-week)
    - Session statistics
    - Volatility clustering
    - Trend persistence
    - Breakout / mean-reversion frequency
    - Drawdown & recovery statistics
    - Market state transitions (probability table)
    - Historical feature extraction
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

from researchos.quant_engine.historical.contracts import (
    DrawdownStatistics,
    FeatureExtraction,
    MarketState,
    RegimeStatistics,
    ReturnSeries,
    SeasonalityProfile,
    StateTransitionTable,
)


def _mean(values: Sequence[float]) -> float:
    if len(values) == 0:
        return 0.0
    return sum(values) / len(values)


def _std(values: Sequence[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = _mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / n)


# ──────────────────────────────────────────────
# Pattern mining
# ──────────────────────────────────────────────


def pattern_frequencies(
    returns: ReturnSeries,
    window: int = 5,
    up_threshold: float = 0.0,
) -> Dict[str, float]:
    """
    Frequency of N-day consecutive up/down patterns.

    Returns mapping of pattern → fraction of windows that match.
    """
    returns.validate()
    n = returns.length
    if window <= 0 or n < window + 1:
        return {}
    ups = [1 if r > up_threshold else 0 for r in returns.returns]
    counts: Dict[str, int] = {}
    for i in range(len(ups) - window):
        pattern = "".join("U" if ups[i + j] else "D" for j in range(window))
        counts[pattern] = counts.get(pattern, 0) + 1
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()}


def consecutive_streaks(returns: ReturnSeries) -> Dict[str, float]:
    """Distribution of consecutive positive/negative streak lengths."""
    returns.validate()
    [1 if r > 0 else (1 if r == 0 else 0) for r in returns.returns]
    pos_counts: Dict[int, int] = {}
    neg_counts: Dict[int, int] = {}
    pos_streak = 0
    neg_streak = 0
    for r in returns.returns:
        if r > 0:
            pos_streak += 1
            if neg_streak > 0:
                neg_counts[neg_streak] = neg_counts.get(neg_streak, 0) + 1
                neg_streak = 0
        elif r < 0:
            neg_streak += 1
            if pos_streak > 0:
                pos_counts[pos_streak] = pos_counts.get(pos_streak, 0) + 1
                pos_streak = 0
        else:
            if pos_streak > 0:
                pos_counts[pos_streak] = pos_counts.get(pos_streak, 0) + 1
                pos_streak = 0
            if neg_streak > 0:
                neg_counts[neg_streak] = neg_counts.get(neg_streak, 0) + 1
                neg_streak = 0
    return {"positive_streaks": dict(pos_counts), "negative_streaks": dict(neg_counts)}


# ──────────────────────────────────────────────
# Regimes
# ──────────────────────────────────────────────


def detect_market_regimes(
    returns: ReturnSeries,
    lookback: int = 20,
    vol_percentile: float = 0.7,
) -> List[RegimeStatistics]:
    """Segment returns into market state regimes."""
    returns.validate()
    n = returns.length
    if n < lookback:
        return []

    # Rolling mean & vol to classify states per window.
    states: List[MarketState] = []
    rolling_vols: List[float] = []
    for i in range(lookback - 1, n):
        window = returns.returns[i - lookback + 1 : i + 1]
        m = _mean(window)
        v = _std(window)
        rolling_vols.append(v)
        if v == 0:
            states.append(MarketState.SIDEWAYS)
        elif m > 0 and v <= 0.02:
            states.append(MarketState.BULL)
        elif m < 0 and v <= 0.02:
            states.append(MarketState.BEAR)
        elif v > 0.03:
            states.append(MarketState.HIGH_VOLATILITY)
        else:
            states.append(MarketState.SIDEWAYS)

    if not rolling_vols:
        return []

    # Segment contiguous runs of the same state.
    segments: List[Tuple[MarketState, int, int]] = []
    start = 0
    current = states[0]
    for i in range(1, len(states)):
        if states[i] != current:
            segments.append((current, start, i - 1))
            start = i
            current = states[i]
    segments.append((current, start, len(states) - 1))

    out: List[RegimeStatistics] = []
    for state, s, e in segments:
        # Convert back to full-series indices (offset by lookback-1).
        full_s = s + (lookback - 1)
        full_e = e + (lookback - 1)
        seg = returns.returns[full_s : full_e + 1]
        out.append(
            RegimeStatistics(
                state=state,
                start_index=full_s,
                end_index=full_e,
                mean_return=_mean(seg),
                volatility=_std(seg),
                cumulative_return=math.prod(1.0 + r for r in seg) - 1.0 if seg else 0.0,
                num_periods=len(seg),
            )
        )
    return out


# ──────────────────────────────────────────────
# Seasonality
# ──────────────────────────────────────────────


def monthly_seasonality(returns: ReturnSeries) -> SeasonalityProfile:
    """Average return and hit rate by month index (0-11)."""
    returns.validate()
    months: Dict[int, List[float]] = {}
    for i, r in enumerate(returns.returns):
        months.setdefault(i % 12, []).append(r)
    periods = {}
    for m in range(12):
        if m in months:
            vals = months[m]
            periods[str(m)] = {
                "mean_return": _mean(vals),
                "hit_rate": sum(1.0 for v in vals if v > 0) / len(vals),
                "num_periods": len(vals),
            }
    return SeasonalityProfile(group_key="month", periods=periods)


def weekly_seasonality(returns: ReturnSeries) -> SeasonalityProfile:
    """Average return and hit rate by weekday index (0-6)."""
    returns.validate()
    days: Dict[int, List[float]] = {}
    for i, r in enumerate(returns.returns):
        days.setdefault(i % 7, []).append(r)
    periods = {}
    for d in range(7):
        if d in days:
            vals = days[d]
            periods[str(d)] = {
                "mean_return": _mean(vals),
                "hit_rate": sum(1.0 for v in vals if v > 0) / len(vals),
                "num_periods": len(vals),
            }
    return SeasonalityProfile(group_key="weekday", periods=periods)


# ──────────────────────────────────────────────
# Session statistics & volatility clustering
# ──────────────────────────────────────────────


def session_statistics(returns: ReturnSeries) -> Dict[str, float]:
    """Summary statistics per session (whole-series aggregates)."""
    returns.validate()
    vals = returns.returns
    return {
        "mean": _mean(vals),
        "std": _std(vals),
        "min": min(vals),
        "max": max(vals),
        "positive_ratio": sum(1.0 for v in vals if v > 0) / len(vals),
        "negative_ratio": sum(1.0 for v in vals if v < 0) / len(vals),
        "flat_ratio": sum(1.0 for v in vals if v == 0) / len(vals),
    }


def volatility_clustering(
    returns: ReturnSeries,
    window: int = 20,
) -> Dict[str, float]:
    """Autocorrelation of |returns| / squared returns → clustering measure."""
    returns.validate()
    n = returns.length
    if n < window + 2:
        return {"abs_return_autocorr": 0.0, "squared_return_autocorr": 0.0, "clustering_ratio": 0.0}
    abs_r = [abs(r) for r in returns.returns]
    sq_r = [r * r for r in returns.returns]

    def _acf(values: List[float], lag: int = 1) -> float:
        m = _mean(values)
        num = sum((values[i] - m) * (values[i - lag] - m) for i in range(lag, len(values)))
        den = sum((v - m) ** 2 for v in values)
        return num / den if den != 0 else 0.0

    abs_acf = _acf(abs_r, 1)
    sq_acf = _acf(sq_r, 1)
    # High vol clustering: mean(|r|) vs std ratio.
    clustering_ratio = (_std(abs_r)) / (_mean(abs_r) + 1e-12)
    return {
        "abs_return_autocorr": abs_acf,
        "squared_return_autocorr": sq_acf,
        "clustering_ratio": clustering_ratio,
    }


# ──────────────────────────────────────────────
# Trend persistence, breakouts, mean reversion
# ──────────────────────────────────────────────


def trend_persistence(returns: ReturnSeries, window: int = 10) -> Dict[str, float]:
    """Fraction of windows where return sign is maintained for N periods."""
    returns.validate()
    n = returns.length
    if n < window * 2:
        return {"persistence_ratio": 0.0, "reversal_ratio": 0.0}
    persist = 0
    reverse = 0
    for i in range(n - window):
        first = sum(returns.returns[i : i + window])
        second = sum(returns.returns[i + window : i + 2 * window])
        if first > 0 and second > 0:
            persist += 1
        elif first < 0 and second < 0:
            persist += 1
        elif first > 0 and second < 0:
            reverse += 1
        elif first < 0 and second > 0:
            reverse += 1
    total = persist + reverse
    if total == 0:
        return {"persistence_ratio": 0.0, "reversal_ratio": 0.0}
    return {"persistence_ratio": persist / total, "reversal_ratio": reverse / total}


def breakout_frequency(returns: ReturnSeries, window: int = 20) -> Dict[str, float]:
    """Frequency of 2-day-range breakouts."""
    returns.validate()
    n = returns.length
    if n < window + 2:
        return {"breakout_up": 0.0, "breakout_down": 0.0}
    # Use cumulative returns to proxy price levels.
    price = [100.0]
    for r in returns.returns:
        price.append(price[-1] * (1.0 + r))
    up = 0
    down = 0
    for i in range(window, n - 1):
        high = max(price[i - window + 1 : i + 1])
        low = min(price[i - window + 1 : i + 1])
        if price[i + 1] > high:
            up += 1
        elif price[i + 1] < low:
            down += 1
    total = up + down
    if total == 0:
        return {"breakout_up": 0.0, "breakout_down": 0.0}
    return {"breakout_up": up / total, "breakout_down": down / total}


def mean_reversion_frequency(returns: ReturnSeries, window: int = 5) -> Dict[str, float]:
    """Frequency of return sign reversal after an N-day move."""
    returns.validate()
    n = returns.length
    if n < window + 2:
        return {"mean_reversion_ratio": 0.0}
    rev = 0
    total = 0
    for i in range(n - window - 1):
        move = sum(returns.returns[i : i + window])
        next_day = returns.returns[i + window]
        if move > 0 and next_day < 0:
            rev += 1
            total += 1
        elif move < 0 and next_day > 0:
            rev += 1
            total += 1
        elif move > 0.001 or move < -0.001:
            total += 1
    if total == 0:
        return {"mean_reversion_ratio": 0.0}
    return {"mean_reversion_ratio": rev / total}


# ──────────────────────────────────────────────
# Drawdown & recovery statistics
# ──────────────────────────────────────────────


def drawdown_statistics(returns: ReturnSeries) -> DrawdownStatistics:
    """Drawdown and recovery statistics."""
    returns.validate()
    price = [100.0]
    for r in returns.returns:
        price.append(price[-1] * (1.0 + r))

    peak = price[0]
    peak_idx = 0
    dd_start = 0
    dd_depth = 0.0
    max_dd = 0.0
    drawdowns: List[Tuple[float, int]] = []  # (depth, length)
    recovery_periods: List[int] = []
    in_drawdown = False

    for i, v in enumerate(price):
        if v > peak:
            if in_drawdown and dd_depth < 0:
                length = i - dd_start
                drawdowns.append((dd_depth, length))
                recovery_periods.append(length)
                if dd_depth < max_dd:
                    max_dd = dd_depth
            peak = v
            peak_idx = i
            in_drawdown = False
        else:
            dd = (v - peak) / peak if peak != 0 else 0.0
            if dd < dd_depth or not in_drawdown:
                if not in_drawdown:
                    dd_start = peak_idx
                    dd_depth = dd
                    in_drawdown = True
                elif dd < dd_depth:
                    dd_depth = dd

    # Close any open drawdown at the end.
    if in_drawdown:
        length = len(price) - dd_start
        drawdowns.append((dd_depth, length))
        recovery_periods.append(length)
        if dd_depth < max_dd:
            max_dd = dd_depth
            len(price) - 1

    if not drawdowns:
        return DrawdownStatistics()

    depths = [d[0] for d in drawdowns]
    lengths = [d[1] for d in drawdowns]
    return DrawdownStatistics(
        max_drawdown=max_dd,
        avg_drawdown=_mean(depths),
        longest_drawdown_periods=max(lengths),
        avg_drawdown_periods=_mean(lengths),
        recovery_periods=recovery_periods,
        num_drawdowns=len(drawdowns),
    )


def recovery_statistics(returns: ReturnSeries) -> Dict[str, float]:
    """Recovery time after maximum drawdown."""
    ds = drawdown_statistics(returns)
    if ds.recovery_periods:
        return {
            "avg_recovery_periods": _mean(ds.recovery_periods),
            "max_recovery_periods": max(ds.recovery_periods),
            "min_recovery_periods": min(ds.recovery_periods),
        }
    return {"avg_recovery_periods": 0.0, "max_recovery_periods": 0.0, "min_recovery_periods": 0.0}


# ──────────────────────────────────────────────
# State transitions
# ──────────────────────────────────────────────


def state_transition_table(returns: ReturnSeries, lookback: int = 20) -> StateTransitionTable:
    """Transition probabilities between discretized market states."""
    regimes = detect_market_regimes(returns, lookback)
    if len(regimes) < 2:
        return StateTransitionTable(states=[s.value for s in MarketState])

    state_order = [s.value for s in MarketState]
    counts = {s: 0 for s in state_order}
    matrix = {s: {t: 0 for t in state_order} for s in state_order}

    for i in range(len(regimes) - 1):
        f = regimes[i].state.value
        t = regimes[i + 1].state.value
        matrix[f][t] += 1
        counts[f] += 1

    rows = []
    for s in state_order:
        row_total = counts[s]
        if row_total == 0:
            rows.append([0.0] * len(state_order))
        else:
            rows.append([matrix[s][t] / row_total for t in state_order])

    return StateTransitionTable(
        states=state_order,
        transition_matrix=rows,
        state_counts=counts,
    )


# ──────────────────────────────────────────────
# Feature extraction
# ──────────────────────────────────────────────


def extract_features(returns: ReturnSeries) -> FeatureExtraction:
    """Extract a flat set of deterministic historical features."""
    returns.validate()
    vals = returns.returns
    n = len(vals)
    positive = [r for r in vals if r > 0]
    negative = [r for r in vals if r < 0]
    dd = drawdown_statistics(returns)
    vc = volatility_clustering(returns)
    features = {
        "length": float(n),
        "mean_return": _mean(vals),
        "std_return": _std(vals),
        "min_return": min(vals) if vals else 0.0,
        "max_return": max(vals) if vals else 0.0,
        "skewness": _skew(vals),
        "kurtosis": _kurtosis(vals),
        "positive_ratio": len(positive) / n if n else 0.0,
        "avg_positive": _mean(positive) if positive else 0.0,
        "avg_negative": _mean(negative) if negative else 0.0,
        "max_drawdown": dd.max_drawdown,
        "num_drawdowns": float(dd.num_drawdowns),
        "abs_return_autocorr": vc.get("abs_return_autocorr", 0.0),
        "squared_return_autocorr": vc.get("squared_return_autocorr", 0.0),
    }
    return FeatureExtraction(features=features)


def _skew(values: Sequence[float]) -> float:
    n = len(values)
    if n < 3:
        return 0.0
    m = _mean(values)
    sd = _std(values)
    if sd == 0:
        return 0.0
    return sum((v - m) ** 3 for v in values) / (n * sd**3)


def _kurtosis(values: Sequence[float]) -> float:
    n = len(values)
    if n < 4:
        return 0.0
    m = _mean(values)
    var = sum((v - m) ** 2 for v in values) / n
    if var == 0:
        return 0.0
    return sum((v - m) ** 4 for v in values) / (n * var**2) - 3.0
