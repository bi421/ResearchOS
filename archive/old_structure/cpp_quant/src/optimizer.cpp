#include "optimizer.h"
#include "backtest.h"
#include <limits>
#include <iostream>

namespace cpp_quant {

std::map<std::string, double> Optimizer::optimizeSMA(
    const std::vector<Candle>& data,
    int short_min, int short_max, int short_step,
    int long_min, int long_max, int long_step,
    const std::string& metric) {

    std::map<std::string, double> best_params;
    double best_score = -std::numeric_limits<double>::infinity();

    for (int short_p = short_min; short_p <= short_max; short_p += short_step) {
        for (int long_p = long_min; long_p <= long_max; long_p += long_step) {
            if (short_p >= long_p) continue;
            BacktestEngine engine(data);
            auto result = engine.runSMA(short_p, long_p);

            double score = 0.0;
            if (metric == "winrate") score = result.winrate;
            else if (metric == "sharpe") score = result.sharpe_ratio;
            else if (metric == "total_return") score = result.total_return;
            else score = result.winrate;

            if (score > best_score) {
                best_score = score;
                best_params["short"] = short_p;
                best_params["long"] = long_p;
                best_params["score"] = best_score;
        best_params["metric_name"] = 0.0; // placeholder
                // best_params["metric"] = metric; // string to double conversion removed
            }
        }
    }
    return best_params;
}

std::map<std::string, double> Optimizer::optimizeRSI(
    const std::vector<Candle>& data,
    int period_min, int period_max, int period_step,
    double oversold_min, double oversold_max, double oversold_step,
    double overbought_min, double overbought_max, double overbought_step) {

    std::map<std::string, double> best_params;
    double best_score = -std::numeric_limits<double>::infinity();

    for (int p = period_min; p <= period_max; p += period_step) {
        for (double os = oversold_min; os <= oversold_max; os += oversold_step) {
            for (double ob = overbought_min; ob <= overbought_max; ob += overbought_step) {
                BacktestEngine engine(data);
                auto result = engine.runRSI(p, os, ob);
                if (result.winrate > best_score) {
                    best_score = result.winrate;
                    best_params["period"] = p;
                    best_params["oversold"] = os;
                    best_params["overbought"] = ob;
                    best_params["winrate"] = best_score;
                }
            }
        }
    }
    return best_params;
}

} // namespace cpp_quant
