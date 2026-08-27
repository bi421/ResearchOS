#include "quant/strategies/rsi_macd_strategy.h"
#include <cmath>

namespace quant {
namespace strategies {

TradeSignal RsiMacdStrategy::evaluate(const std::vector<double>& closes) {
    TradeSignal signal = {0, 0.0}; 
    
    if (closes.size() < static_cast<size_t>(macd_slow_ + macd_signal_)) {
        return signal;
    }

    auto rsi_values = quant::indicators::rsi(closes, rsi_period_);
    double current_rsi = rsi_values.back();

    auto macd_result = quant::indicators::macd(closes, macd_fast_, macd_slow_, macd_signal_);
    double current_histogram = macd_result.histogram.back();

    if (current_rsi < 30.0 && current_histogram > 0.0) {
        signal.action = 1; 
        signal.confidence = 0.8;
    }
    else if (current_rsi > 70.0 && current_histogram < 0.0) {
        signal.action = -1; 
        signal.confidence = 0.8;
    }

    return signal;
}

} // namespace strategies
} // namespace quant
