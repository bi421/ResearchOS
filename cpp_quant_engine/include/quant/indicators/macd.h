#pragma once
#include <vector>
#include <cstddef>

namespace quant {
namespace indicators {

struct MACDResult {
    std::vector<double> macd_line;      // EMA(12) - EMA(26)
    std::vector<double> signal_line;    // EMA(9) of MACD line
    std::vector<double> histogram;      // MACD line - Signal line
};

// MACD тооцоолох
// fast_period: ихэвчлэн 12
// slow_period: ихэвчлэн 26
// signal_period: ихэвчлэн 9
MACDResult macd(const std::vector<double>& closes,
                size_t fast_period = 12,
                size_t slow_period = 26,
                size_t signal_period = 9);

// EMA (Exponential Moving Average) тооцоолох
std::vector<double> ema(const std::vector<double>& data, size_t period);

} // namespace indicators
} // namespace quant
