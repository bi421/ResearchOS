#include "quant/strategy/trade_result.h"

#include <cstdio>

namespace quant {
namespace strategy {

double TradeResult::profit_loss_percent() const {
  return net_pnl_pct;
}

std::string TradeResult::summary() const {
  char buf[160];
  std::snprintf(buf, sizeof(buf), "Trade #%lld %s entry=%.6f@%lld exit=%.6f@%lld "
                                  "pnl=%+.6f (%.3fR, %s)",
                static_cast<long long>(trade_id), side_name(side), entry_price,
                static_cast<long long>(entry_bar), exit_price,
                static_cast<long long>(exit_bar), net_pnl, r_multiple,
                exit_reason_name(exit_reason));
  return std::string(buf);
}

} // namespace strategy
} // namespace quant
