#ifndef QUANT_BACKTEST_OHLCV_SOURCE_H
#define QUANT_BACKTEST_OHLCV_SOURCE_H

#include "quant/market/types.h"
#include <vector>
#include <cstddef>

namespace quant {

// Abstract, indexable read-only view over an OHLCV series. This is the data
// contract consumed by the backtest engine, decoupling it from any concrete
// storage container.
struct OHLCVSource {
  virtual ~OHLCVSource() = default;
  virtual size_t size() const = 0;
  virtual const OHLCV& operator[](size_t index) const = 0;
  virtual std::vector<OHLCV> range(size_t start, size_t end) const = 0;
};

// In-memory implementation backed by a plain vector.
struct InMemoryOHLCVSource : OHLCVSource {
  std::vector<OHLCV> data;
  size_t size() const override { return data.size(); }
  const OHLCV& operator[](size_t index) const override { return data[index]; }
  std::vector<OHLCV> range(size_t start, size_t end) const override;
};

} // namespace quant
#endif
