#pragma once
#include <vector>
#include <string>
#include "quant/indicators/rsi.h"
#include "quant/indicators/macd.h"

namespace quant {
namespace strategies {

struct TradeSignal {
    int action; // 1 = BUY, -1 = SELL, 0 = HOLD
    double confidence; // 0.0 to 1.0
};

class RsiMacdStrategy {
public:
    RsiMacdStrategy(int rsi_period = 14, int macd_fast = 12, int macd_slow = 26, int macd_signal = 9)
        : rsi_period_(rsi_period), macd_fast_(macd_fast), macd_slow_(macd_slow), macd_signal_(macd_signal) {}

    TradeSignal evaluate(const std::vector<double>& closes);

private:
    int rsi_period_;
    int macd_fast_;
    int macd_slow_;
    int macd_signal_;
};

} // namespace strategies
} // namespace quant
