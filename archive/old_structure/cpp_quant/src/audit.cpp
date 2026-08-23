#include "audit.h"
#include "indicators.h"
#include <cmath>
#include <algorithm>
#include <sstream>

namespace cpp_quant {

AuditResult AuditEngine::runSMAAudit(
    const std::vector<int64_t>& timestamps,
    const std::vector<double>& opens,
    const std::vector<double>& highs,
    const std::vector<double>& lows,
    const std::vector<double>& closes,
    const std::vector<double>& volumes,
    int short_period,
    int long_period,
    double commission
) {
    AuditResult result;
    result.strategy_name = "SMA " + std::to_string(short_period) + "/" + std::to_string(long_period);
    result.commission = commission;
    result.look_ahead_fixed = true;

    size_t n = timestamps.size();
    if (n < (size_t)long_period + 1) return result;

    // 1. SMAs
    std::vector<double> sma_short = Indicators::SMA(closes, short_period);
    std::vector<double> sma_long = Indicators::SMA(closes, long_period);

    // 2. Signals
    std::vector<int> signals(n, 0);
    for (size_t i = 0; i < n; ++i) {
        if (i < (size_t)long_period) continue;
        if (sma_short[i] > sma_long[i] && sma_short[i-1] <= sma_long[i-1]) signals[i] = 1;
        else if (sma_short[i] < sma_long[i] && sma_short[i-1] >= sma_long[i-1]) signals[i] = -1;
    }

    // 3. Бэктест (look-ahead зассан)
    double capital = 10000.0;
    double position = 0.0;
    double entry_price = 0.0;
    int64_t entry_time = 0;
    bool in_position = false;

    std::vector<double> equity_curve;
    equity_curve.reserve(n);

    for (size_t i = 1; i < n; ++i) {
        double open_price = opens[i];
        double close_price = closes[i];

        if (signals[i-1] == 1 && !in_position) {
            double cost = open_price * (1 + commission);
            position = capital / cost;
            capital = 0.0;
            entry_price = cost;
            entry_time = timestamps[i];
            in_position = true;
        }
        else if (signals[i-1] == -1 && in_position) {
            double revenue = close_price * position * (1 - commission);
            AuditedTrade t;
            t.entry_time = entry_time;
            t.exit_time = timestamps[i];
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

    // Хаагдаагүй позиц хаах
    if (in_position && !timestamps.empty()) {
        double close_price = closes.back();
        double revenue = close_price * position * (1 - commission);
        AuditedTrade t;
        t.entry_time = entry_time;
        t.exit_time = timestamps.back();
        t.entry_price = entry_price;
        t.exit_price = close_price;
        t.pnl = (close_price - entry_price) / entry_price;
        t.is_win = t.pnl > 0;
        result.trades.push_back(t);
        capital = revenue;
    }

    // Статистик
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
        result.total_return = (capital - 10000.0) / 10000.0;
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
        if (stddev > 0) result.sharpe_ratio = (mean / stddev) * std::sqrt(252.0);

        double peak = equity_curve.empty() ? 10000.0 : equity_curve[0];
        for (double eq : equity_curve) {
            if (eq > peak) peak = eq;
            double dd = (peak - eq) / peak;
            if (dd > result.max_drawdown) result.max_drawdown = dd;
        }
    }
    return result;
}

std::string AuditEngine::compareResults(const AuditResult& a, const AuditResult& b) {
    std::ostringstream oss;
    oss << "\n===== AUDIT COMPARISON =====\n";
    oss << "Strategy: " << a.strategy_name << "\n";
    oss << "Commission: " << a.commission << "\n";
    oss << "\n--- Original (from run_sma) ---\n";
    oss << "Trades: " << b.num_trades << "\n";
    oss << "Winrate: " << b.winrate*100 << "%\n";
    oss << "Total Return: " << b.total_return*100 << "%\n";
    oss << "Avg Win: " << b.avg_win*100 << "%\n";
    oss << "Avg Loss: " << b.avg_loss*100 << "%\n";
    oss << "Sharpe: " << b.sharpe_ratio << "\n";
    oss << "Max DD: " << b.max_drawdown*100 << "%\n";

    oss << "\n--- Audit (Corrected) ---\n";
    oss << "Trades: " << a.num_trades << "\n";
    oss << "Winrate: " << a.winrate*100 << "%\n";
    oss << "Total Return: " << a.total_return*100 << "%\n";
    oss << "Avg Win: " << a.avg_win*100 << "%\n";
    oss << "Avg Loss: " << a.avg_loss*100 << "%\n";
    oss << "Sharpe: " << a.sharpe_ratio << "\n";
    oss << "Max DD: " << a.max_drawdown*100 << "%\n";

    double win_diff = std::abs(a.winrate - b.winrate);
    double ret_diff = std::abs(a.total_return - b.total_return);
    oss << "\n--- Mismatches ---\n";
    if (win_diff > 0.01) oss << "⚠️ Winrate mismatch: " << win_diff*100 << "%\n";
    if (ret_diff > 0.01) oss << "⚠️ Return mismatch: " << ret_diff*100 << "%\n";
    if (a.num_trades != b.num_trades) oss << "⚠️ Number of trades differ: " << a.num_trades << " vs " << b.num_trades << "\n";
    if (win_diff < 0.01 && ret_diff < 0.01 && a.num_trades == b.num_trades)
        oss << "✅ All metrics match! System is correct.\n";
    else
        oss << "❌ There are discrepancies. Check look-ahead bias or commission.\n";

    return oss.str();
}

} // namespace cpp_quant
