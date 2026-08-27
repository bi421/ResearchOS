#ifndef QUANT_MARKET_HISTORICAL_ITERATOR_H
#define QUANT_MARKET_HISTORICAL_ITERATOR_H

#include "candle.h"
#include "ohlcv_container.h"
#include <iterator>
#include <cstddef>
#include <cstdint>

namespace quant {

class HistoricalIterator {
public:
  using iterator_category = std::random_access_iterator_tag;
  using value_type = Candle;
  using difference_type = ptrdiff_t;
  using pointer = const Candle*;
  using reference = const Candle&;

  HistoricalIterator() = default;
  explicit HistoricalIterator(const OHLCVContainer* container, size_t pos = 0);

  reference operator*() const;
  pointer operator->() const;
  reference operator[](difference_type i) const;

  HistoricalIterator& operator++();
  HistoricalIterator operator++(int);
  HistoricalIterator& operator--();
  HistoricalIterator operator--(int);
  HistoricalIterator& operator+=(difference_type n);
  HistoricalIterator& operator-=(difference_type n);

  HistoricalIterator operator+(difference_type n) const;
  HistoricalIterator operator-(difference_type n) const;
  difference_type operator-(const HistoricalIterator& other) const;

  bool operator==(const HistoricalIterator& other) const { return pos_ == other.pos_ && container_ == other.container_; }
  bool operator<(const HistoricalIterator& other) const { return pos_ < other.pos_; }
  bool operator>(const HistoricalIterator& other) const { return pos_ > other.pos_; }
  bool operator<=(const HistoricalIterator& other) const { return pos_ <= other.pos_; }
  bool operator>=(const HistoricalIterator& other) const { return pos_ >= other.pos_; }

  bool is_valid() const { return container_ != nullptr; }
  size_t position() const { return pos_; }

private:
  const OHLCVContainer* container_{nullptr};
  size_t pos_{0};
};

inline HistoricalIterator operator+(ptrdiff_t n, const HistoricalIterator& it) {
  return it + n;
}

class HistoricalRange {
public:
  HistoricalRange(OHLCVContainer& container, size_t start, size_t end);

  HistoricalIterator begin() const { return begin_; }
  HistoricalIterator end() const { return end_; }

  size_t size() const { return static_cast<size_t>(end_ - begin_); }
  bool empty() const { return begin_ == end_; }

  std::vector<Candle> to_vector() const;

private:
  HistoricalIterator begin_;
  HistoricalIterator end_;
};

} // namespace quant
#endif
