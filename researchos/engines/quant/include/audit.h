#pragma once
#include <vector>
#include <string>
#include <utility>
#include <cstdint>

namespace cpp_quant {

struct AuditedTrade {
    int64_t entry_time;
    int64_t exit_time;
    double entry_price;
    double exit_price;
    double pnl;
    bool is_win;
};

struct AuditResult {
    std::vector<AuditedTrade> trades;
    int num_trades = 0;
    double winrate = 0.0;
    double total_return = 0.0;
    double max_drawdown = 0.0;
    double avg_win = 0.0;
    double avg_loss = 0.0;
    double profit_factor = 0.0;
    double sharpe_ratio = 0.0;
    std::string strategy_name;
    double commission = 0.0001;
    bool look_ahead_fixed = true;
};

class AuditEngine {
public:
    // 1. Вектор хувилбар (Python-д шууд ашиглах)
    static AuditResult runSMAAudit(
        const std::vector<int64_t>& timestamps,
        const std::vector<double>& opens,
        const std::vector<double>& highs,
        const std::vector<double>& lows,
        const std::vector<double>& closes,
        const std::vector<double>& volumes,
        int short_period,
        int long_period,
        double commission = 0.0001
    );

    // 2. Харьцуулах функц (одоо байгаа)
    static std::string compareResults(const AuditResult& a, const AuditResult& b);
};

} // namespace cpp_quant
