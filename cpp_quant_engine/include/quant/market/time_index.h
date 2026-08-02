#ifndef QUANT_MARKET_TIME_INDEX_H
#define QUANT_MARKET_TIME_INDEX_H

#include "types.h"
#include <vector>
#include <algorithm>
#include <cstdint>
#include <optional>

namespace quant {

class TimeIndex {
public:
  using Entry = std::pair<TimePoint, size_t>;

  TimeIndex() = default;

  void build(const std::vector<TimePoint>& timestamps);
  void rebuild();
  void reserve(size_t n) { entries_.reserve(n); }

  void add(TimePoint tp, size_t index);

  size_t size() const { return entries_.size(); }
  bool empty() const { return entries_.empty(); }
  void clear() { entries_.clear(); }

  std::optional<size_t> find(TimePoint tp) const;
  std::optional<size_t> find_closest(TimePoint tp) const;

  size_t lower_bound(TimePoint tp) const;
  size_t upper_bound(TimePoint tp) const;

  std::pair<size_t, size_t> range(TimePoint from, TimePoint to) const;

  const Entry& operator[](size_t i) const { return entries_[i]; }
  const std::vector<Entry>& entries() const { return entries_; }

  bool is_sorted() const { return sorted_; }

private:
  std::vector<Entry> entries_;
  bool sorted_{true};
};

} // namespace quant
#endif
