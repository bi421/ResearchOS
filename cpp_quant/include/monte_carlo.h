#pragma once
#include <vector>
#include "backtest.h"

namespace cpp_quant {

class MonteCarlo {
public:
    // Бодит арилжааны өгөөжийн дундажийг санамсаргүй арилжаатай харьцуулах (p-value)
    static double pValue(const std::vector<Trade>& actual_trades, int num_simulations = 10000);
    
    // Equity curve-ийн bootstrap
    static std::vector<double> bootstrapEquity(const std::vector<double>& returns, int num_paths = 1000);
};

} // namespace cpp_quant
