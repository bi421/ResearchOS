#include "quant/market/historical_iterator.h"

namespace quant {

HistoricalIterator::HistoricalIterator(const OHLCVContainer* container, size_t pos)
  : container_(container), pos_(pos) {}

HistoricalIterator::reference HistoricalIterator::operator*() const {
  return (*container_)[pos_];
}

HistoricalIterator::pointer HistoricalIterator::operator->() const {
  return &(*container_)[pos_];
}

HistoricalIterator::reference HistoricalIterator::operator[](difference_type i) const {
  return (*container_)[pos_ + static_cast<size_t>(i)];
}

HistoricalIterator& HistoricalIterator::operator++() {
  ++pos_; return *this;
}

HistoricalIterator HistoricalIterator::operator++(int) {
  auto tmp = *this; ++pos_; return tmp;
}

HistoricalIterator& HistoricalIterator::operator--() {
  --pos_; return *this;
}

HistoricalIterator HistoricalIterator::operator--(int) {
  auto tmp = *this; --pos_; return tmp;
}

HistoricalIterator& HistoricalIterator::operator+=(difference_type n) {
  pos_ = static_cast<size_t>(static_cast<difference_type>(pos_) + n);
  return *this;
}

HistoricalIterator& HistoricalIterator::operator-=(difference_type n) {
  pos_ = static_cast<size_t>(static_cast<difference_type>(pos_) - n);
  return *this;
}

HistoricalIterator HistoricalIterator::operator+(difference_type n) const {
  return HistoricalIterator(container_, static_cast<size_t>(static_cast<difference_type>(pos_) + n));
}

HistoricalIterator HistoricalIterator::operator-(difference_type n) const {
  return HistoricalIterator(container_, static_cast<size_t>(static_cast<difference_type>(pos_) - n));
}

HistoricalIterator::difference_type HistoricalIterator::operator-(const HistoricalIterator& other) const {
  return static_cast<difference_type>(pos_) - static_cast<difference_type>(other.pos_);
}

// HistoricalRange
HistoricalRange::HistoricalRange(OHLCVContainer& container, size_t start, size_t end)
  : begin_(&container, start), end_(&container, end) {}

std::vector<Candle> HistoricalRange::to_vector() const {
  std::vector<Candle> result;
  result.reserve(size());
  for (auto it = begin_; it != end_; ++it) {
    result.push_back(*it);
  }
  return result;
}

} // namespace quant
