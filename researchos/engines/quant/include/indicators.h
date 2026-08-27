#pragma once
#include <vector>
#include "data_loader.h"
#include <utility>

namespace cpp_quant {

class Indicators {
public:
    // SMA (Simple Moving Average)
    static std::vector<double> SMA(const std::vector<double>& prices, int period);

    // RSI (Relative Strength Index)
    static std::vector<double> RSI(const std::vector<double>& prices, int period = 14);

    // MACD
    struct MACDResult {
        std::vector<double> macd;
        std::vector<double> signal;
        std::vector<double> histogram;
    };
    static MACDResult MACD(const std::vector<double>& prices, int fast=12, int slow=26, int signal=9);

    // ATR (Average True Range)
    static std::vector<double> ATR(const std::vector<Candle>& candles, int period = 14);

    // Bollinger Bands
    struct BBResult {
        std::vector<double> upper;
        std::vector<double> middle;
        std::vector<double> lower;
    };
    static BBResult BollingerBands(const std::vector<double>& prices, int period = 20, double num_std = 2.0);
};

} // namespace cpp_quant
