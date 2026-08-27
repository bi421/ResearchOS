#ifndef QUANT_BACKTEST_TRADE_BOOK_H
#define QUANT_BACKTEST_TRADE_BOOK_H

#include "quant/market/types.h"
#include <vector>
#include <string>
#include <optional>
#include <cstdint>

namespace quant {

enum class TradeDirection : uint8_t { Buy, Sell };
enum class TradeStatus : uint8_t { Open, Closed, Canceled };

struct Trade {
  uint64_t id{0};
  std::string symbol;
  TradeDirection direction{TradeDirection::Buy};
  double quantity{0.0};
  double entry_price{0.0};
  double exit_price{0.0};
  double entry_commission{0.0};
  double exit_commission{0.0};
  TimePoint entry_time;
  TimePoint exit_time;
  TradeStatus status{TradeStatus::Open};
  std::string notes;

  double pnl() const;
  double pnl_pct() const;
  double gross_pnl() const;
  double total_commission() const;
  double duration_hours() const;
  bool is_profitable() const;
};

class TradeBook {
public:
  TradeBook() = default;
  explicit TradeBook(std::string symbol);

  void add_trade(Trade trade);
  void close_trade(uint64_t trade_id, double exit_price, TimePoint exit_time,
                   double commission = 0.0);
  void cancel_trade(uint64_t trade_id);

  const std::vector<Trade>& trades() const { return trades_; }
  std::vector<Trade> closed_trades() const;
  std::vector<Trade> open_trades() const;
  std::vector<Trade> profitable_trades() const;
  std::vector<Trade> losing_trades() const;

  std::optional<Trade> get_trade(uint64_t trade_id) const;

  size_t total_trades() const { return trades_.size(); }
  size_t winning_trades() const;
  size_t losing_trades_count() const;
  double win_rate() const;

  double total_pnl() const;
  double total_commission() const;

  void clear();
  const std::string& symbol() const { return symbol_; }

private:
  std::string symbol_;
  std::vector<Trade> trades_;
  uint64_t next_id_{1};
};

} // namespace quant
#endif
