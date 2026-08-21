#ifndef QUANT_MARKET_ORDER_BOOK_H
#define QUANT_MARKET_ORDER_BOOK_H

#include <vector>
#include <map>
#include <string>
#include <cstdint>
#include <numeric>
#include <optional>
#include <iterator>
#include <algorithm>

namespace quant {

struct Level {
  double price{0.0};
  double volume{0.0};
  uint32_t order_count{0};

  bool operator==(const Level&) const = default;
};

class OrderBook {
public:
  OrderBook() = default;
  explicit OrderBook(std::string symbol);

  void set_bids(std::vector<Level> bids);
  void set_asks(std::vector<Level> asks);
  void update_bid(double price, double volume);
  void update_ask(double price, double volume);

  const std::vector<Level>& bids() const { return bids_; }
  const std::vector<Level>& asks() const { return asks_; }
  const std::string& symbol() const { return symbol_; }

  double best_bid() const;
  double best_ask() const;
  double mid_price() const;
  double spread() const;
  double spread_pct() const;

  double bid_volume() const;
  double ask_volume() const;
  double imbalance() const;

  double weighted_mid_price(uint32_t levels = 5) const;
  double micro_price() const;

  std::optional<Level> get_bid_level(size_t depth) const;
  std::optional<Level> get_ask_level(size_t depth) const;

  void clear();
  size_t bid_depth() const { return bids_.size(); }
  size_t ask_depth() const { return asks_.size(); }

private:
  std::string symbol_;
  std::vector<Level> bids_;
  std::vector<Level> asks_;
};

} // namespace quant
#endif
