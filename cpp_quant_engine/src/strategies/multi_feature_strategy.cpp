#include "quant/strategies/multi_feature_strategy.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace quant {
namespace strategies {
namespace {

constexpr double nan_value() {
  return std::numeric_limits<double>::quiet_NaN();
}

} // namespace

void MultiFeatureStrategy::calculate_indicators(const std::vector<OHLCV>& bars) {
  const std::size_t count = bars.size();
  const double nan = nan_value();

  sma20_.assign(count, nan);
  sma50_.assign(count, nan);
  rsi_.assign(count, nan);
  atr_.assign(count, nan);
  atr_sma20_.assign(count, nan);
  signal_values_.assign(count, 0);

  double sma20_sum = 0.0;
  double sma50_sum = 0.0;
  double atr_sum = 0.0;
  double atr_sma_sum = 0.0;
  double average_gain = 0.0;
  double average_loss = 0.0;

  for (std::size_t i = 0; i < count; ++i) {
    sma20_sum += bars[i].close;
    sma50_sum += bars[i].close;
    if (i >= sma_fast_period) sma20_sum -= bars[i - sma_fast_period].close;
    if (i >= sma_slow_period) sma50_sum -= bars[i - sma_slow_period].close;
    if (i + 1 >= sma_fast_period) sma20_[i] = sma20_sum / sma_fast_period;
    if (i + 1 >= sma_slow_period) sma50_[i] = sma50_sum / sma_slow_period;

    const double true_range = i == 0
        ? bars[i].high - bars[i].low
        : std::max({bars[i].high - bars[i].low,
                    std::abs(bars[i].high - bars[i - 1].close),
                    std::abs(bars[i].low - bars[i - 1].close)});
    if (i < atr_period) {
      atr_sum += true_range;
      if (i + 1 == atr_period) atr_[i] = atr_sum / atr_period;
    } else {
      atr_[i] = (atr_[i - 1] * (atr_period - 1) + true_range) / atr_period;
    }

    if (i > 0) {
      const double change = bars[i].close - bars[i - 1].close;
      if (i <= rsi_period) {
        if (change > 0.0) average_gain += change;
        else average_loss -= change;
        if (i == rsi_period) {
          average_gain /= rsi_period;
          average_loss /= rsi_period;
        }
      } else {
        average_gain = (average_gain * (rsi_period - 1) + std::max(change, 0.0)) / rsi_period;
        average_loss = (average_loss * (rsi_period - 1) + std::max(-change, 0.0)) / rsi_period;
      }
      if (i >= rsi_period) {
        rsi_[i] = average_loss == 0.0
            ? 100.0
            : 100.0 - (100.0 / (1.0 + average_gain / average_loss));
      }
    }

    if (!std::isnan(atr_[i])) {
      atr_sma_sum += atr_[i];
      if (i >= atr_period + atr_sma_period - 1) {
        const std::size_t first = i - atr_sma_period + 1;
        if (first == atr_period - 1) {
          atr_sma20_[i] = atr_sma_sum / atr_sma_period;
        } else {
          atr_sma_sum -= atr_[first - 1];
          atr_sma20_[i] = atr_sma_sum / atr_sma_period;
        }
      }
    }

    if (!std::isnan(sma20_[i]) && !std::isnan(sma50_[i]) &&
        !std::isnan(rsi_[i]) && !std::isnan(atr_[i]) &&
        !std::isnan(atr_sma20_[i])) {
      if (sma20_[i] > sma50_[i] && rsi_[i] > 50.0 && atr_[i] > atr_sma20_[i]) {
        signal_values_[i] = 1;
      } else if (sma20_[i] < sma50_[i] && rsi_[i] < 50.0 &&
                 atr_[i] > atr_sma20_[i]) {
        signal_values_[i] = -1;
      }
    }
  }
}

int MultiFeatureStrategy::generate_signal(std::size_t index) const {
  if (index >= signal_values_.size()) {
    return 0;
  }
  return signal_values_[index];
}

double MultiFeatureStrategy::trailing_stop_distance(std::size_t index) const {
  if (index >= atr_.size() || std::isnan(atr_[index])) return 0.0;
  return trailing_stop_multiplier * atr_[index];
}

} // namespace strategies
} // namespace quant
