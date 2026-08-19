#pragma once
#include <vector>
#include <string>
#include "data_loader.h"

namespace cpp_quant {

struct Trade {
    int64_t entry_time;
    int64_t exit_time;
    double entry_price;
    double exit_price;
    double pnl;          // decimal (e.g., 0.01 = 1%)
    bool is_win;
};

struct BacktestResult {
    int num_trades = 0;
    double winrate = 0.0;          // 0-1
    double total_return = 0.0;     // decimal
    double sharpe_ratio = 0.0;
    double max_drawdown = 0.0;     // decimal
    double avg_win = 0.0;
    double avg_loss = 0.0;
    double profit_factor = 0.0;
    std::vector<Trade> trades;
};

class BacktestEngine {
public:
    BacktestEngine(const std::vector<Candle>& data, double initial_capital = 10000.0, double commission = 0.001);
    
    // SMA Crossover
    BacktestResult runSMA(int short_period, int long_period);
    
    // RSI Mean Reversion
    BacktestResult runRSI(int period, double oversold=30.0, double overbought=70.0);
    
    // MACD + SMA filter
    BacktestResult runMACD(int fast=12, int slow=26, int signal=9, int sma_filter=200);
    
    // Generic function to run any signal vector (1 = buy, -1 = sell, 0 = hold)
    BacktestResult runGeneric(const std::vector<int>& signals);

private:
    std::vector<Candle> data_;
    double initial_capital_;
    double commission_;
};

} // namespace cpp_quant
