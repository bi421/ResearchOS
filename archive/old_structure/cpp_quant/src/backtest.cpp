#include "backtest.h"
#include "indicators.h"
#include <cmath>
#include <algorithm>

// ---------------------------------------------------------------------
// Existing ML backtest function (unchanged, moved from original file)
// ---------------------------------------------------------------------
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

// ---------------------------------------------------------------------
// BacktestEngine — new implementation (see backtest.h for provenance
// notes: signal/execution timing lifted from AuditEngine::runSMAAudit
// in audit.cpp; RSI/MACD entry-exit rules are new).
// ---------------------------------------------------------------------
namespace cpp_quant {

BacktestEngine::BacktestEngine(const std::vector<Candle>& data,
                                double initial_capital,
                                double commission)
    : data_(data), initial_capital_(initial_capital), commission_(commission) {}

BacktestResult BacktestEngine::simulate(const std::vector<int>& signals) const {
    BacktestResult result;
    size_t n = data_.size();
    if (n == 0 || signals.size() != n) return result;

    double capital = initial_capital_;
    double position = 0.0;
    double entry_price = 0.0;
    int64_t entry_time = 0;
    bool in_position = false;

    std::vector<double> equity_curve;
    equity_curve.reserve(n);
    equity_curve.push_back(initial_capital_);

    // Same timing as AuditEngine::runSMAAudit: signal computed at bar
    // i-1 (using only data through i-1) is executed at the OPEN of bar
    // i, avoiding look-ahead bias.
    for (size_t i = 1; i < n; ++i) {
        double open_price = data_[i].open;
        double close_price = data_[i].close;

        if (signals[i-1] == 1 && !in_position) {
            double cost = open_price * (1.0 + commission_);
            if (cost > 0.0) {
                position = capital / cost;
                capital = 0.0;
                entry_price = cost;
                entry_time = data_[i].timestamp;
                in_position = true;
            }
        }
        else if (signals[i-1] == -1 && in_position) {
            double revenue = close_price * position * (1.0 - commission_);
            Trade t;
            t.entry_time = entry_time;
            t.exit_time = data_[i].timestamp;
            t.entry_price = entry_price;
            t.exit_price = close_price;
            t.pnl = (close_price - entry_price) / entry_price;
            t.is_win = t.pnl > 0;
            result.trades.push_back(t);

            capital = revenue;
            position = 0.0;
            in_position = false;
        }

        double equity = capital + position * close_price;
        equity_curve.push_back(equity);
    }

    // Close any open position at the final bar's close.
    if (in_position && !data_.empty()) {
        double close_price = data_.back().close;
        double revenue = close_price * position * (1.0 - commission_);
        Trade t;
        t.entry_time = entry_time;
        t.exit_time = data_.back().timestamp;
        t.entry_price = entry_price;
        t.exit_price = close_price;
        t.pnl = (close_price - entry_price) / entry_price;
        t.is_win = t.pnl > 0;
        result.trades.push_back(t);
        capital = revenue;
    }

    if (!result.trades.empty()) {
        result.num_trades = (int)result.trades.size();
        int wins = 0;
        double sum_pnl = 0.0, sum_win = 0.0, sum_loss = 0.0;
        for (const auto& t : result.trades) {
            sum_pnl += t.pnl;
            if (t.is_win) { wins++; sum_win += t.pnl; }
            else { sum_loss += t.pnl; }
        }
        // winrate/total_return/avg_win/avg_loss/max_drawdown are returned
        // as PERCENTAGES (0-100), not fractions — matching the Python
        // wrapper's `_to_dict`, which passes these fields through
        // unscaled and documents them as "Already a percentage"
        // (see researchos/tests/test_cpp_backtest_regression.py).
        // sharpe_ratio and profit_factor are ratios, not percentages,
        // and are left unscaled.
        result.winrate = 100.0 * (double)wins / result.trades.size();
        result.total_return = 100.0 * (capital - initial_capital_) / initial_capital_;
        result.avg_win = (wins > 0) ? 100.0 * sum_win / wins : 0.0;
        result.avg_loss = (result.trades.size() - wins > 0)
            ? 100.0 * sum_loss / (result.trades.size() - wins) : 0.0;
        result.profit_factor = (sum_loss != 0) ? sum_win / std::abs(sum_loss) : 1000.0;

        double mean = sum_pnl / result.trades.size();
        double var = 0.0;
        for (const auto& t : result.trades) var += (t.pnl - mean) * (t.pnl - mean);
        if (result.trades.size() > 1) var /= (result.trades.size() - 1);
        double stddev = std::sqrt(var);
        if (stddev > 0) result.sharpe_ratio = (mean / stddev) * std::sqrt(252.0);

        double peak = equity_curve.empty() ? initial_capital_ : equity_curve[0];
        for (double eq : equity_curve) {
            if (eq > peak) peak = eq;
            double dd = (peak - eq) / peak;
            if (dd > result.max_drawdown) result.max_drawdown = dd;
        }
        result.max_drawdown *= 100.0;
    }

    return result;
}

BacktestResult BacktestEngine::runSMA(int short_period, int long_period) {
    size_t n = data_.size();
    if (n < (size_t)long_period + 1) return BacktestResult();

    std::vector<double> closes(n);
    for (size_t i = 0; i < n; ++i) closes[i] = data_[i].close;

    std::vector<double> sma_short = Indicators::SMA(closes, short_period);
    std::vector<double> sma_long = Indicators::SMA(closes, long_period);

    std::vector<int> signals(n, 0);
    for (size_t i = (size_t)long_period; i < n; ++i) {
        if (sma_short[i] > sma_long[i] && sma_short[i-1] <= sma_long[i-1]) signals[i] = 1;
        else if (sma_short[i] < sma_long[i] && sma_short[i-1] >= sma_long[i-1]) signals[i] = -1;
    }
    return simulate(signals);
}

BacktestResult BacktestEngine::runRSI(int period, double oversold, double overbought) {
    size_t n = data_.size();
    if (n < (size_t)period + 2) return BacktestResult();

    std::vector<double> closes(n);
    for (size_t i = 0; i < n; ++i) closes[i] = data_[i].close;

    std::vector<double> rsi = Indicators::RSI(closes, period);

    std::vector<int> signals(n, 0);
    for (size_t i = (size_t)period + 1; i < n; ++i) {
        if (rsi[i] > oversold && rsi[i-1] <= oversold) signals[i] = 1;
        else if (rsi[i] < overbought && rsi[i-1] >= overbought) signals[i] = -1;
    }
    return simulate(signals);
}

BacktestResult BacktestEngine::runMACD(int fast, int slow, int signal, int sma_filter) {
    size_t n = data_.size();
    size_t warmup = (size_t)std::max({fast, slow, signal, sma_filter});
    if (n < warmup + 1) return BacktestResult();

    std::vector<double> closes(n);
    for (size_t i = 0; i < n; ++i) closes[i] = data_[i].close;

    Indicators::MACDResult macd = Indicators::MACD(closes, fast, slow, signal);
    std::vector<double> filter_sma = Indicators::SMA(closes, sma_filter);

    std::vector<int> signals(n, 0);
    for (size_t i = warmup; i < n; ++i) {
        bool cross_up = macd.macd[i] > macd.signal[i] && macd.macd[i-1] <= macd.signal[i-1];
        bool cross_down = macd.macd[i] < macd.signal[i] && macd.macd[i-1] >= macd.signal[i-1];
        if (cross_up && closes[i] > filter_sma[i]) signals[i] = 1;
        else if (cross_down) signals[i] = -1;
    }
    return simulate(signals);
}

} // namespace cpp_quant
