#ifndef QUANT_FAST_FAST_NUMERIC_H
#define QUANT_FAST_FAST_NUMERIC_H

#include <cstddef>
#include <vector>

namespace quant::fast {

struct BacktestOutput {
  double final_equity{0.0};
  double total_return_pct{0.0};
  double max_drawdown_pct{0.0};
  std::size_t trades{0};
  std::size_t wins{0};
};

BacktestOutput backtest_next_open(const std::vector<double>& open,
                                  const std::vector<double>& close,
                                  const std::vector<int>& signal,
                                  const std::vector<double>& quantity,
                                  double initial_capital,
                                  double commission_pct,
                                  double slippage_pct,
                                  bool allow_short);

std::vector<double> simple_returns(const std::vector<double>& close);
std::vector<double> drawdown_pct(const std::vector<double>& equity);

struct RiskScanOutput {
  double mean{0.0};
  double stddev{0.0};
  double sharpe{0.0};
  double max_drawdown_pct{0.0};
  double var95{0.0};
  double cvar95{0.0};
};

RiskScanOutput risk_scan(const std::vector<double>& returns,
                         const std::vector<double>& equity);

}  // namespace quant::fast

#endif
