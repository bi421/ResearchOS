#ifndef QUANT_MARKET_MARKET_DATA_ENGINE_H
#define QUANT_MARKET_MARKET_DATA_ENGINE_H

#include "ohlcv_container.h"
#include "data_loader.h"
#include "timeframe_aggregator.h"
#include "quant/core/result.h"
#include <string>
#include <unordered_map>
#include <memory>

namespace quant {

class MarketDataEngine {
public:
  MarketDataEngine() = default;

  Result<void> load_from_file(const std::filesystem::path& path,
                               const LoadConfig& cfg = {},
                               const std::string& symbol = "XAUUSD");

  Result<void> load_directory(const std::filesystem::path& dir,
                               const LoadConfig& cfg = {},
                               const std::string& symbol = "XAUUSD");

  Result<OHLCVContainer> get_series(const std::string& symbol,
                                     Timeframe tf) const;

  bool has_series(const std::string& symbol, Timeframe tf) const;

  OHLCVContainer& register_series(const std::string& symbol,
                                   Timeframe tf,
                                   OHLCVContainer container);

  std::vector<std::string> symbols() const;
  std::vector<Timeframe> available_timeframes(const std::string& symbol) const;

  Result<OHLCVContainer> aggregate(const std::string& symbol,
                                    Timeframe source_tf,
                                    Timeframe target_tf);

  void clear();
  size_t total_series() const { return store_.size(); }

private:
  struct SeriesKey {
    std::string symbol;
    Timeframe tf;

    bool operator==(const SeriesKey& other) const {
      return symbol == other.symbol && tf == other.tf;
    }
  };

  struct SeriesKeyHash {
    size_t operator()(const SeriesKey& k) const {
      return std::hash<std::string>{}(k.symbol) ^
             (static_cast<size_t>(k.tf) << 16);
    }
  };

  std::unordered_map<SeriesKey, OHLCVContainer, SeriesKeyHash> store_;
  DataLoader loader_;
};

} // namespace quant
#endif
