#pragma once
#include <vector>
#include <string>
#include <tuple>
#include <cstdint>
#include "data_loader.h"

// ---------------------------------------------------------------------
// Existing ML backtest function (unchanged)
// ---------------------------------------------------------------------
std::tuple<double, double, double, double, int>
run_ml_backtest_cpp(
    const std::vector<double>& prices,
    const std::vector<double>& probabilities,
    double threshold,
    double initial_capital = 100000.0,
    double commission = 0.001,
    double slippage = 0.0005
);

namespace cpp_quant {

// ---------------------------------------------------------------------
// Trade / BacktestResult — reconstructed from usage across
// quant_engine.cpp, optimizer.cpp, monte_carlo.cpp, python_bindings.cpp.
// Field-for-field identical to AuditedTrade / AuditResult (audit.h),
// since audit.cpp already implements the look-ahead-bias-fixed
// reference logic for SMA. Kept as a separate type (not a typedef of
// AuditedTrade) so QuantEngine's public API stays independent of the
// audit module.
// ---------------------------------------------------------------------
struct Trade {
    int64_t entry_time;
    int64_t exit_time;
    double entry_price;
    double exit_price;
    double pnl;
    bool is_win;
};

struct BacktestResult {
    std::vector<Trade> trades;
    int num_trades = 0;
    double winrate = 0.0;
    double total_return = 0.0;
    double max_drawdown = 0.0;
    double avg_win = 0.0;
    double avg_loss = 0.0;
    double profit_factor = 0.0;
    double sharpe_ratio = 0.0;
};

// ---------------------------------------------------------------------
// BacktestEngine — reimplemented. No original implementation of this
// class survived in the codebase (grep of src/*.cpp found no
// `BacktestEngine::` definitions anywhere). The execution model below
// (signal computed at bar i, executed at open of bar i+1) is not
// invented — it is lifted directly from AuditEngine::runSMAAudit in
// audit.cpp, which is explicitly documented there as the
// look-ahead-bias-corrected reference implementation. RSI and MACD
// strategies extend the same signal/execution pattern; their specific
// entry/exit rules (see .cpp) are new and were not recovered from any
// existing source — confirm they match intended strategy rules.
// ---------------------------------------------------------------------
class BacktestEngine {
public:
    explicit BacktestEngine(const std::vector<Candle>& data,
                             double initial_capital = 10000.0,
                             double commission = 0.0001);

    // Long-only SMA crossover. Entry: short SMA crosses above long SMA.
    // Exit: short SMA crosses below long SMA.
    BacktestResult runSMA(int short_period, int long_period);

    // Long-only RSI mean-reversion. Entry: RSI crosses above `oversold`.
    // Exit: RSI crosses below `overbought`.
    BacktestResult runRSI(int period, double oversold = 30.0, double overbought = 70.0);

    // Long-only MACD trend-following with an SMA trend filter.
    // Entry: MACD line crosses above signal line AND close > SMA(sma_filter).
    // Exit: MACD line crosses below signal line.
    BacktestResult runMACD(int fast = 12, int slow = 26, int signal = 9, int sma_filter = 200);

private:
    std::vector<Candle> data_;
    double initial_capital_;
    double commission_;

    // Shared trade-simulation + statistics routine. `signals[i]` must be
    // computed using only data up to and including bar i; execution
    // happens at open[i+1] via signals[i-1] at the point of use, exactly
    // mirroring AuditEngine::runSMAAudit's look-ahead handling.
    BacktestResult simulate(const std::vector<int>& signals) const;
};

} // namespace cpp_quant
