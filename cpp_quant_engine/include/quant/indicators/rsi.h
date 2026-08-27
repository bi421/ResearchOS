#pragma once
#include <vector>
#include <cstddef>

namespace quant {
namespace indicators {

// Relative Strength Index (RSI)
// period: ихэвчлэн 14
// Returns: RSI утгуудын вектор (эхний period-1 утга NaN)
std::vector<double> rsi(const std::vector<double>& closes, size_t period = 14);

// RSI-ийн нэг утгыг тооцоолох (streaming)
double rsi_single(double current_rsi, double prev_close, double current_close, size_t period);

} // namespace indicators
} // namespace quant
