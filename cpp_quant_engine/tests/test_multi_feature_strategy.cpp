#include "quant/strategies/multi_feature_strategy.h"

#include <gtest/gtest.h>

#include <cmath>
#include <vector>

namespace {

quant::OHLCV bar(double close, double range) {
  quant::OHLCV result;
  result.open = close;
  result.high = close + range;
  result.low = close - range;
  result.close = close;
  return result;
}

} // namespace

TEST(MultiFeatureStrategy, WarmupReturnsFlatAndStopUsesTwoAtr) {
  std::vector<quant::OHLCV> bars;
  for (int i = 0; i < 70; ++i) bars.push_back(bar(100.0 + i, 1.0));

  quant::strategies::MultiFeatureStrategy strategy;
  strategy.calculate_indicators(bars);

  EXPECT_EQ(strategy.generate_signal(48), 0);
  ASSERT_FALSE(std::isnan(strategy.atr()[69]));
  EXPECT_DOUBLE_EQ(strategy.trailing_stop_distance(69), 2.0 * strategy.atr()[69]);
}

TEST(MultiFeatureStrategy, FlatWhenVolatilityFilterFails) {
  std::vector<quant::OHLCV> bars;
  for (int i = 0; i < 70; ++i) bars.push_back(bar(100.0 + i, 1.0));

  quant::strategies::MultiFeatureStrategy strategy;
  strategy.calculate_indicators(bars);

  EXPECT_EQ(strategy.generate_signal(69), 0);
}

TEST(MultiFeatureStrategy, CombinesTrendMomentumAndVolatility) {
  std::vector<quant::OHLCV> rising;
  std::vector<quant::OHLCV> falling;
  for (int i = 0; i < 50; ++i) {
    rising.push_back(bar(100.0, 0.5));
    falling.push_back(bar(100.0, 0.5));
  }
  for (int i = 0; i < 20; ++i) {
    rising.push_back(bar(101.0 + i, 3.0));
    falling.push_back(bar(99.0 - i, 3.0));
  }

  quant::strategies::MultiFeatureStrategy long_strategy;
  quant::strategies::MultiFeatureStrategy short_strategy;
  long_strategy.calculate_indicators(rising);
  short_strategy.calculate_indicators(falling);

  EXPECT_EQ(long_strategy.generate_signal(69), 1);
  EXPECT_EQ(short_strategy.generate_signal(69), -1);
  EXPECT_EQ(long_strategy.generate_signals().back(), 1);
  EXPECT_EQ(short_strategy.generate_signals().back(), -1);
  EXPECT_EQ(long_strategy.signals().size(), rising.size());
  EXPECT_GT(long_strategy.atr()[69], long_strategy.atr_sma20()[69]);
  EXPECT_GT(short_strategy.atr()[69], short_strategy.atr_sma20()[69]);
}
