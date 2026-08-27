#include "quant/indicators/rsi.h"
#include <cmath>
#include <stdexcept>

namespace quant {
namespace indicators {

std::vector<double> rsi(const std::vector<double>& closes, size_t period) {
    if (closes.size() <= period) {
        return std::vector<double>(closes.size(), std::nan(""));
    }

    std::vector<double> result(closes.size(), std::nan(""));

    // Эхний average gain/loss тооцоолох
    double avg_gain = 0.0;
    double avg_loss = 0.0;

    for (size_t i = 1; i <= period; ++i) {
        double change = closes[i] - closes[i - 1];
        if (change > 0) avg_gain += change;
        else avg_loss += std::abs(change);
    }

    avg_gain /= period;
    avg_loss /= period;

    // Эхний RSI
    if (avg_loss == 0.0) {
        result[period] = 100.0;
    } else {
        double rs = avg_gain / avg_loss;
        result[period] = 100.0 - (100.0 / (1.0 + rs));
    }

    // Үлдсэн RSI утгууд (Wilder's smoothing)
    for (size_t i = period + 1; i < closes.size(); ++i) {
        double change = closes[i] - closes[i - 1];
        double gain = (change > 0) ? change : 0.0;
        double loss = (change < 0) ? std::abs(change) : 0.0;

        avg_gain = (avg_gain * (period - 1) + gain) / period;
        avg_loss = (avg_loss * (period - 1) + loss) / period;

        if (avg_loss == 0.0) {
            result[i] = 100.0;
        } else {
            double rs = avg_gain / avg_loss;
            result[i] = 100.0 - (100.0 / (1.0 + rs));
        }
    }

    return result;
}

double rsi_single(double current_rsi, double prev_close, double current_close, size_t period) {
    double change = current_close - prev_close;
    double gain = (change > 0) ? change : 0.0;
    double loss = (change < 0) ? std::abs(change) : 0.0;

    // Энэ нь зөвхөн streaming хэрэглээнд зориулсан хялбарчилсан хувилбар
    // Бүрэн тооцоололд rsi() функцийг ашиглах
    if (std::isnan(current_rsi)) {
        return std::nan("");
    }

    double rs = gain / (loss > 0 ? loss : 1e-10);
    return 100.0 - (100.0 / (1.0 + rs));
}

} // namespace indicators
} // namespace quant
