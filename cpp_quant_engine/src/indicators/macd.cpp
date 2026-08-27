#include "quant/indicators/macd.h"
#include <cmath>
#include <stdexcept>

namespace quant {
namespace indicators {

std::vector<double> ema(const std::vector<double>& data, size_t period) {
    if (data.empty() || period == 0) {
        return std::vector<double>();
    }

    std::vector<double> result(data.size(), std::nan(""));
    double multiplier = 2.0 / (period + 1);

    // Эхний EMA = эхний period утгуудын энгийн дундаж
    double sum = 0.0;
    for (size_t i = 0; i < period && i < data.size(); ++i) {
        sum += data[i];
    }
    result[period - 1] = sum / period;

    // Үлдсэн EMA утгууд
    for (size_t i = period; i < data.size(); ++i) {
        result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1];
    }

    return result;
}

MACDResult macd(const std::vector<double>& closes, size_t fast_period, size_t slow_period, size_t signal_period) {
    MACDResult result;

    if (closes.size() < slow_period) {
        result.macd_line = std::vector<double>(closes.size(), std::nan(""));
        result.signal_line = std::vector<double>(closes.size(), std::nan(""));
        result.histogram = std::vector<double>(closes.size(), std::nan(""));
        return result;
    }

    // EMA тооцоолох
    std::vector<double> fast_ema = ema(closes, fast_period);
    std::vector<double> slow_ema = ema(closes, slow_period);

    // MACD line = Fast EMA - Slow EMA
    result.macd_line.resize(closes.size(), std::nan(""));
    for (size_t i = slow_period - 1; i < closes.size(); ++i) {
        if (!std::isnan(fast_ema[i]) && !std::isnan(slow_ema[i])) {
            result.macd_line[i] = fast_ema[i] - slow_ema[i];
        }
    }

    // Signal line = EMA of MACD line
    result.signal_line = ema(result.macd_line, signal_period);

    // Histogram = MACD line - Signal line
    result.histogram.resize(closes.size(), std::nan(""));
    for (size_t i = 0; i < closes.size(); ++i) {
        if (!std::isnan(result.macd_line[i]) && !std::isnan(result.signal_line[i])) {
            result.histogram[i] = result.macd_line[i] - result.signal_line[i];
        }
    }

    return result;
}

} // namespace indicators
} // namespace quant
