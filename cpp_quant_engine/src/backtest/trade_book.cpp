#include "quant/backtest/trade_book.h"
#include <numeric>
#include <algorithm>

namespace quant {

double Trade::pnl() const {
  if (status != TradeStatus::Closed) return 0.0;
  double multiplier = (direction == TradeDirection::Buy) ? 1.0 : -1.0;
  return (exit_price - entry_price) * quantity * multiplier - total_commission();
}

double Trade::pnl_pct() const {
  if (status != TradeStatus::Closed || entry_price == 0.0) return 0.0;
  return (pnl() / (entry_price * quantity)) * 100.0;
}

double Trade::gross_pnl() const {
  if (status != TradeStatus::Closed) return 0.0;
  double multiplier = (direction == TradeDirection::Buy) ? 1.0 : -1.0;
  return (exit_price - entry_price) * quantity * multiplier;
}

double Trade::total_commission() const { return entry_commission + exit_commission; }

double Trade::duration_hours() const {
  if (status != TradeStatus::Closed) return 0.0;
  auto dur = exit_time - entry_time;
  return std::chrono::duration<double>(dur).count() / 3600.0;
}

bool Trade::is_profitable() const { return status == TradeStatus::Closed && pnl() > 0.0; }

TradeBook::TradeBook(std::string symbol) : symbol_(std::move(symbol)) {}

void TradeBook::add_trade(Trade trade) {
  trade.id = next_id_++;
  trades_.push_back(std::move(trade));
}

void TradeBook::close_trade(uint64_t trade_id, double exit_price, TimePoint exit_time,
                             double commission) {
  for (auto& t : trades_) {
    if (t.id == trade_id && t.status == TradeStatus::Open) {
      t.exit_price = exit_price;
      t.exit_time = exit_time;
      t.exit_commission = commission;
      t.status = TradeStatus::Closed;
      break;
    }
  }
}

void TradeBook::cancel_trade(uint64_t trade_id) {
  for (auto& t : trades_) {
    if (t.id == trade_id && t.status == TradeStatus::Open) {
      t.status = TradeStatus::Canceled;
      break;
    }
  }
}

std::vector<Trade> TradeBook::closed_trades() const {
  std::vector<Trade> result;
  std::copy_if(trades_.begin(), trades_.end(), std::back_inserter(result),
               [](const Trade& t) { return t.status == TradeStatus::Closed; });
  return result;
}

std::vector<Trade> TradeBook::open_trades() const {
  std::vector<Trade> result;
  std::copy_if(trades_.begin(), trades_.end(), std::back_inserter(result),
               [](const Trade& t) { return t.status == TradeStatus::Open; });
  return result;
}

std::vector<Trade> TradeBook::profitable_trades() const {
  std::vector<Trade> result;
  std::copy_if(trades_.begin(), trades_.end(), std::back_inserter(result),
               [](const Trade& t) { return t.is_profitable(); });
  return result;
}

std::vector<Trade> TradeBook::losing_trades() const {
  auto closed = closed_trades();
  std::vector<Trade> result;
  std::copy_if(closed.begin(), closed.end(), std::back_inserter(result),
               [](const Trade& t) { return t.pnl() <= 0.0; });
  return result;
}

std::optional<Trade> TradeBook::get_trade(uint64_t trade_id) const {
  for (auto& t : trades_) {
    if (t.id == trade_id) return t;
  }
  return std::nullopt;
}

size_t TradeBook::winning_trades() const { return profitable_trades().size(); }
size_t TradeBook::losing_trades_count() const { return losing_trades().size(); }

double TradeBook::win_rate() const {
  auto closed = closed_trades();
  if (closed.empty()) return 0.0;
  return static_cast<double>(winning_trades()) / static_cast<double>(closed.size()) * 100.0;
}

double TradeBook::total_pnl() const {
  double sum = 0.0;
  for (auto& t : trades_) sum += t.pnl();
  return sum;
}

double TradeBook::total_commission() const {
  double sum = 0.0;
  for (auto& t : trades_) sum += t.total_commission();
  return sum;
}

void TradeBook::clear() { trades_.clear(); next_id_ = 1; }

} // namespace quant
