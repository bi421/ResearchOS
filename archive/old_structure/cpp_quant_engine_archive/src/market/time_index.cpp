#include "quant/market/time_index.h"
#include <algorithm>

namespace quant {

void TimeIndex::build(const std::vector<TimePoint>& timestamps) {
  entries_.clear();
  entries_.reserve(timestamps.size());
  for (size_t i = 0; i < timestamps.size(); ++i) {
    entries_.emplace_back(timestamps[i], i);
  }
  rebuild();
}

void TimeIndex::rebuild() {
  std::sort(entries_.begin(), entries_.end(),
            [](const Entry& a, const Entry& b) { return a.first < b.first; });
  sorted_ = true;
}

void TimeIndex::add(TimePoint tp, size_t index) {
  entries_.emplace_back(tp, index);
  sorted_ = false;
}

std::optional<size_t> TimeIndex::find(TimePoint tp) const {
  if (!sorted_) const_cast<TimeIndex*>(this)->rebuild();
  auto it = std::lower_bound(entries_.begin(), entries_.end(), tp,
                              [](const Entry& e, TimePoint t) { return e.first < t; });
  if (it != entries_.end() && it->first == tp) {
    return it->second;
  }
  return std::nullopt;
}

std::optional<size_t> TimeIndex::find_closest(TimePoint tp) const {
  if (entries_.empty()) return std::nullopt;
  if (!sorted_) const_cast<TimeIndex*>(this)->rebuild();
  auto it = std::lower_bound(entries_.begin(), entries_.end(), tp,
                              [](const Entry& e, TimePoint t) { return e.first < t; });
  if (it == entries_.end()) return entries_.back().second;
  if (it == entries_.begin()) return it->second;
  auto prev = std::prev(it);
  auto diff_cur = std::abs(std::chrono::duration_cast<std::chrono::seconds>(it->first - tp).count());
  auto diff_prev = std::abs(std::chrono::duration_cast<std::chrono::seconds>(prev->first - tp).count());
  return diff_cur < diff_prev ? it->second : prev->second;
}

size_t TimeIndex::lower_bound(TimePoint tp) const {
  if (!sorted_) const_cast<TimeIndex*>(this)->rebuild();
  auto it = std::lower_bound(entries_.begin(), entries_.end(), tp,
                              [](const Entry& e, TimePoint t) { return e.first < t; });
  return static_cast<size_t>(std::distance(entries_.begin(), it));
}

size_t TimeIndex::upper_bound(TimePoint tp) const {
  if (!sorted_) const_cast<TimeIndex*>(this)->rebuild();
  auto it = std::upper_bound(entries_.begin(), entries_.end(), tp,
                              [](TimePoint t, const Entry& e) { return t < e.first; });
  return static_cast<size_t>(std::distance(entries_.begin(), it));
}

std::pair<size_t, size_t> TimeIndex::range(TimePoint from, TimePoint to) const {
  auto lo = lower_bound(from);
  auto hi = upper_bound(to);
  return {lo, hi};
}

} // namespace quant
