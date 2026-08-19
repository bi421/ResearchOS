#include "backtest.h"
#include "statistics.h"
#include "indicators.h"
#include <algorithm>
#include <cmath>
#include <iostream>

namespace cpp_quant {

BacktestEngine::BacktestEngine(const std::vector<Candle>& data, double initial_capital, double commission)
    : data_(data), initial_capital_(initial_capital), commission_(commission) {}

BacktestResult BacktestEngine::runSMA(int short_period, int long_period) {
    std::vector<double> prices;
    prices.reserve(data_.size());
    for (const auto& c : data_) prices.push_back(c.close);
    
    auto sma_short = Indicators::SMA(prices, short_period);
    auto sma_long = Indicators::SMA(prices, long_period);
    
    std::vector<int> signals(data_.size(), 0);
    for (size_t i = 1; i < data_.size(); ++i) {
        if (i < (size_t)long_period) continue;
        if (sma_short[i] > sma_long[i] && sma_short[i-1] <= sma_long[i-1]) signals[i] = 1;
        else if (sma_short[i] < sma_long[i] && sma_short[i-1] >= sma_long[i-1]) signals[i] = -1;
    }
    return runGeneric(signals);
}

BacktestResult BacktestEngine::runRSI(int period, double oversold, double overbought) {
    std::vector<double> prices;
    prices.reserve(data_.size());
    for (const auto& c : data_) prices.push_back(c.close);
    
    auto rsi = Indicators::RSI(prices, period);
    std::vector<int> signals(data_.size(), 0);
    for (size_t i = 1; i < data_.size(); ++i) {
        if (i < (size_t)period + 1) continue;
        if (rsi[i] < oversold && rsi[i-1] >= oversold) signals[i] = 1;
        else if (rsi[i] > overbought && rsi[i-1] <= overbought) signals[i] = -1;
    }
    return runGeneric(signals);
}

BacktestResult BacktestEngine::runMACD(int fast, int slow, int signal, int sma_filter) {
    std::vector<double> prices;
    prices.reserve(data_.size());
    for (const auto& c : data_) prices.push_back(c.close);
    
    auto macd_res = Indicators::MACD(prices, fast, slow, signal);
    auto sma = Indicators::SMA(prices, sma_filter);
    
    std::vector<int> signals(data_.size(), 0);
    for (size_t i = 1; i < data_.size(); ++i) {
        if (i < (size_t)std::max({fast, slow, signal, sma_filter}) + 1) continue;
        if (macd_res.histogram[i] > 0 && macd_res.histogram[i-1] <= 0 && prices[i-1] > sma[i-1]) signals[i] = 1;
        else if (macd_res.histogram[i] < 0 && macd_res.histogram[i-1] >= 0 && prices[i-1] < sma[i-1]) signals[i] = -1;
    }
    return runGeneric(signals);
}

// ============================================================
// ЗӨВ runGeneric (signal-ийг 1 индексээр шилжүүлсэн)
// ============================================================
BacktestResult BacktestEngine::runGeneric(const std::vector<int>& signals) {
    BacktestResult result;
    if (data_.size() != signals.size() || data_.empty()) return result;

    double capital = initial_capital_;
    double position = 0.0;
    double entry_price = 0.0;
    int64_t entry_time = 0;
    bool in_position = false;

    std::vector<double> equity_curve;
    equity_curve.reserve(data_.size());

    for (size_t i = 1; i < data_.size(); ++i) {
        double open_price = data_[i].open;
        double close_price = data_[i].close;

        if (signals[i-1] == 1 && !in_position) {
            double cost = open_price * (1 + commission_);
            position = capital / cost;
            capital = 0.0;
            entry_price = cost;
            entry_time = data_[i].timestamp;
            in_position = true;
        } 
        else if (signals[i-1] == -1 && in_position) {
            double revenue = close_price * position * (1 - commission_);
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

    if (in_position && !data_.empty()) {
        double close_price = data_.back().close;
        double revenue = close_price * position * (1 - commission_);
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
        result.winrate = (double)wins / result.trades.size();
        result.total_return = (capital - initial_capital_) / initial_capital_;
        result.avg_win = (wins > 0) ? sum_win / wins : 0.0;
        result.avg_loss = (result.trades.size() - wins > 0) ? sum_loss / (result.trades.size() - wins) : 0.0;
        result.profit_factor = (sum_loss != 0) ? sum_win / std::abs(sum_loss) : 1000.0;

        std::vector<double> returns;
        for (const auto& t : result.trades) returns.push_back(t.pnl);
        double mean = sum_pnl / result.trades.size();
        double var = 0.0;
        for (double r : returns) var += (r - mean) * (r - mean);
        if (result.trades.size() > 1) var /= (result.trades.size() - 1);
        double stddev = std::sqrt(var);
        if (stddev > 0) {
            result.sharpe_ratio = (mean / stddev) * std::sqrt(252.0);
        }

        double peak = equity_curve.empty() ? initial_capital_ : equity_curve[0];
        for (double eq : equity_curve) {
            if (eq > peak) peak = eq;
            double dd = (peak - eq) / peak;
            if (dd > result.max_drawdown) result.max_drawdown = dd;
        }
    }
    return result;
}

} // namespace cpp_quant
