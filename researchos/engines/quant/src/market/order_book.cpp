#include "quant/market/order_book.h"

namespace quant {

OrderBook::OrderBook(std::string symbol) : symbol_(std::move(symbol)) {}

void OrderBook::set_bids(std::vector<Level> bids) {
  std::sort(bids.begin(), bids.end(), [](const Level& a, const Level& b) {
    return a.price > b.price;
  });
  bids_ = std::move(bids);
}

void OrderBook::set_asks(std::vector<Level> asks) {
  std::sort(asks.begin(), asks.end(), [](const Level& a, const Level& b) {
    return a.price < b.price;
  });
  asks_ = std::move(asks);
}

void OrderBook::update_bid(double price, double volume) {
  auto it = std::find_if(bids_.begin(), bids_.end(),
                          [price](const Level& l) { return l.price == price; });
  if (it != bids_.end()) {
    if (volume == 0.0) bids_.erase(it);
    else it->volume = volume;
  } else if (volume > 0.0) {
    bids_.push_back({price, volume, 1});
    std::sort(bids_.begin(), bids_.end(), [](const Level& a, const Level& b) {
      return a.price > b.price;
    });
  }
}

void OrderBook::update_ask(double price, double volume) {
  auto it = std::find_if(asks_.begin(), asks_.end(),
                          [price](const Level& l) { return l.price == price; });
  if (it != asks_.end()) {
    if (volume == 0.0) asks_.erase(it);
    else it->volume = volume;
  } else if (volume > 0.0) {
    asks_.push_back({price, volume, 1});
    std::sort(asks_.begin(), asks_.end(), [](const Level& a, const Level& b) {
      return a.price < b.price;
    });
  }
}

double OrderBook::best_bid() const {
  return bids_.empty() ? 0.0 : bids_.front().price;
}

double OrderBook::best_ask() const {
  return asks_.empty() ? 0.0 : asks_.front().price;
}

double OrderBook::mid_price() const {
  double bb = best_bid(), ba = best_ask();
  if (bb == 0.0 || ba == 0.0) return 0.0;
  return (bb + ba) / 2.0;
}

double OrderBook::spread() const {
  double bb = best_bid(), ba = best_ask();
  if (bb == 0.0 || ba == 0.0) return 0.0;
  return ba - bb;
}

double OrderBook::spread_pct() const {
  double mid = mid_price();
  return mid != 0.0 ? (spread() / mid) * 100.0 : 0.0;
}

double OrderBook::bid_volume() const {
  return std::accumulate(bids_.begin(), bids_.end(), 0.0,
                          [](double sum, const Level& l) { return sum + l.volume; });
}

double OrderBook::ask_volume() const {
  return std::accumulate(asks_.begin(), asks_.end(), 0.0,
                          [](double sum, const Level& l) { return sum + l.volume; });
}

double OrderBook::imbalance() const {
  double bv = bid_volume(), av = ask_volume();
  double total = bv + av;
  return total != 0.0 ? (bv - av) / total : 0.0;
}

double OrderBook::weighted_mid_price(uint32_t levels) const {
  double bid_val = 0.0, ask_val = 0.0;
  double bid_vol = 0.0, ask_vol = 0.0;
  for (uint32_t i = 0; i < levels && i < bids_.size(); ++i) {
    bid_val += bids_[i].price * bids_[i].volume;
    bid_vol += bids_[i].volume;
  }
  for (uint32_t i = 0; i < levels && i < asks_.size(); ++i) {
    ask_val += asks_[i].price * asks_[i].volume;
    ask_vol += asks_[i].volume;
  }
  double wb = bid_vol > 0.0 ? bid_val / bid_vol : best_bid();
  double wa = ask_vol > 0.0 ? ask_val / ask_vol : best_ask();
  return (wb + wa) / 2.0;
}

double OrderBook::micro_price() const {
  double bv = bid_volume(), av = ask_volume();
  double bb = best_bid(), ba = best_ask();
  double total = bv + av;
  return total != 0.0 ? (bb * av + ba * bv) / total : mid_price();
}

std::optional<Level> OrderBook::get_bid_level(size_t depth) const {
  if (depth >= bids_.size()) return std::nullopt;
  return bids_[depth];
}

std::optional<Level> OrderBook::get_ask_level(size_t depth) const {
  if (depth >= asks_.size()) return std::nullopt;
  return asks_[depth];
}

void OrderBook::clear() {
  bids_.clear();
  asks_.clear();
}

} // namespace quant
