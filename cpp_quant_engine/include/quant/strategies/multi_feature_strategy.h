#ifndef QUANT_STRATEGIES_MULTI_FEATURE_STRATEGY_H
#define QUANT_STRATEGIES_MULTI_FEATURE_STRATEGY_H

#include "quant/market/types.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace quant {
namespace strategies {

class BaseStrategy {
public:
  using SignalArray = std::vector<std::int8_t>;

  virtual ~BaseStrategy() = default;

  virtual void calculate_indicators(const std::vector<OHLCV>& bars) = 0;
  virtual int generate_signal(std::size_t index) const = 0;
  virtual SignalArray generate_signals() const = 0;
};

class MultiFeatureStrategy final : public BaseStrategy {
public:
  static constexpr std::size_t sma_fast_period = 20;
  static constexpr std::size_t sma_slow_period = 50;
  static constexpr std::size_t rsi_period = 14;
  static constexpr std::size_t atr_period = 14;
  static constexpr std::size_t atr_sma_period = 20;
  static constexpr double trailing_stop_multiplier = 2.0;

  void calculate_indicators(const std::vector<OHLCV>& bars) override;
  int generate_signal(std::size_t index) const override;
  SignalArray generate_signals() const override { return signal_values_; }

  const SignalArray& signals() const { return signal_values_; }

  // Returns the trailing-stop distance in price units for the selected bar.
  double trailing_stop_distance(std::size_t index) const;

  const std::vector<double>& sma20() const { return sma20_; }
  const std::vector<double>& sma50() const { return sma50_; }
  const std::vector<double>& rsi() const { return rsi_; }
  const std::vector<double>& atr() const { return atr_; }
  const std::vector<double>& atr_sma20() const { return atr_sma20_; }

private:
  std::vector<double> sma20_;
  std::vector<double> sma50_;
  std::vector<double> rsi_;
  std::vector<double> atr_;
  std::vector<double> atr_sma20_;
  SignalArray signal_values_;
};

} // namespace strategies
} // namespace quant

#endif
