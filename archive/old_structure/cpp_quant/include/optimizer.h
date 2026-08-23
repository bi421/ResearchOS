#pragma once
#include <vector>
#include <map>
#include "backtest.h"

namespace cpp_quant {

class Optimizer {
public:
    // SMA параметрийг оновчтой болгох (энгийн grid search)
    static std::map<std::string, double> optimizeSMA(
        const std::vector<Candle>& data,
        int short_min=5, int short_max=30, int short_step=5,
        int long_min=20, int long_max=100, int long_step=10,
        const std::string& metric = "winrate"  // "winrate", "sharpe", "total_return"
    );

    // RSI параметрийг оновчтой болгох
    static std::map<std::string, double> optimizeRSI(
        const std::vector<Candle>& data,
        int period_min=10, int period_max=20, int period_step=2,
        double oversold_min=20, double oversold_max=40, double oversold_step=5,
        double overbought_min=60, double overbought_max=80, double overbought_step=5
    );
};

} // namespace cpp_quant
