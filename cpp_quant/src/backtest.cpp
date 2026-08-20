#include "backtest.h"
#include <cmath>
#include <algorithm>

std::tuple<double, double, double, double, int> 
run_ml_backtest_cpp(
    const std::vector<double>& prices,
    const std::vector<double>& probabilities,
    double threshold,
    double initial_capital,
    double commission,
    double slippage
) {
    double capital = initial_capital;
    double position = 0.0;
    double entry_price = 0.0;
    int trades = 0;
    int wins = 0;
    std::vector<double> equity_curve;
    equity_curve.reserve(prices.size());
    equity_curve.push_back(initial_capital);

    size_t n = std::min(prices.size(), probabilities.size());

    for (size_t i = 0; i < n; ++i) {
        double price = prices[i];
        double prob = probabilities[i];

        if (prob > threshold && position == 0.0) {
            double cost_per_unit = price * (1.0 + commission + slippage);
            double size = capital / cost_per_unit;
            if (size > 0.0) {
                capital -= size * cost_per_unit;
                position = size;
                entry_price = price;
            }
        }
        else if (prob < (1.0 - threshold) && position > 0.0) {
            double revenue_per_unit = price * (1.0 - commission - slippage);
            double revenue = position * revenue_per_unit;
            double pnl = revenue - position * entry_price;
            capital += revenue;
            if (pnl > 0) ++wins;
            ++trades;
            position = 0.0;
            entry_price = 0.0;
        }
        double equity = capital + position * price;
        equity_curve.push_back(equity);
    }

    if (position > 0.0 && !prices.empty()) {
        double closing_price = prices.back();
        double revenue_per_unit = closing_price * (1.0 - commission - slippage);
        double revenue = position * revenue_per_unit;
        double pnl = revenue - position * entry_price;
        capital += revenue;
        if (pnl > 0) ++wins;
        ++trades;
    }

    double total_return = (capital - initial_capital) / initial_capital;

    double sharpe = 0.0;
    if (equity_curve.size() > 1) {
        std::vector<double> returns;
        returns.reserve(equity_curve.size()-1);
        for (size_t i = 1; i < equity_curve.size(); ++i) {
            double ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1];
            returns.push_back(ret);
        }
        double mean = 0.0;
        for (double r : returns) mean += r;
        mean /= returns.size();
        double stddev = 0.0;
        for (double r : returns) stddev += (r - mean) * (r - mean);
        stddev = std::sqrt(stddev / returns.size());
        if (stddev > 1e-8) {
            sharpe = (mean / stddev) * std::sqrt(252.0);
        }
    }

    double max_drawdown = 0.0;
    double peak = equity_curve[0];
    for (double e : equity_curve) {
        if (e > peak) peak = e;
        double dd = (peak - e) / peak;
        if (dd > max_drawdown) max_drawdown = dd;
    }
    max_drawdown = -max_drawdown;

    double win_rate = (trades > 0) ? static_cast<double>(wins) / trades : 0.0;

    return {total_return, sharpe, max_drawdown, win_rate, trades};
}
