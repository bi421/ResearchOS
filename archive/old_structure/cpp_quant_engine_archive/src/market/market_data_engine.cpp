#include "quant/market/market_data_engine.h"
#include "quant/core/logger.h"
#include <format>
#include <algorithm>

namespace quant {

Result<void> MarketDataEngine::load_from_file(const std::filesystem::path& path,
                                               const LoadConfig& cfg,
                                               const std::string& symbol) {
  loader_.set_symbol(symbol);
  auto result = loader_.load_file(path, cfg);
  if (result.is_err()) return result.error();

  auto container = std::move(result.value());
  SeriesKey key{container.symbol(), container.timeframe()};
  store_.insert_or_assign(key, std::move(container));

  Logger::instance().info(std::format("MarketDataEngine: loaded series {}/{} from {}",
                                      key.symbol, timeframe_name(key.tf), path.string()));
  return Result<void>::ok();
}

Result<void> MarketDataEngine::load_directory(const std::filesystem::path& dir,
                                               const LoadConfig& cfg,
                                               const std::string& symbol) {
  loader_.set_symbol(symbol);
  auto containers = loader_.load_directory(dir, cfg);
  if (containers.is_err()) return containers.error();

  for (auto& container : containers.value()) {
    SeriesKey key{container.symbol(), container.timeframe()};
    store_.insert_or_assign(key, std::move(container));
  }

  Logger::instance().info(std::format("MarketDataEngine: loaded {} series from directory {}",
                                      containers.value().size(), dir.string()));
  return Result<void>::ok();
}

Result<OHLCVContainer> MarketDataEngine::get_series(const std::string& symbol,
                                                     Timeframe tf) const {
  SeriesKey key{symbol, tf};
  auto it = store_.find(key);
  if (it == store_.end()) {
    return Error(ErrorCode::ConfigKeyNotFound,
                 std::format("series {}/{} not loaded", symbol, timeframe_name(tf)));
  }
  return it->second;
}

bool MarketDataEngine::has_series(const std::string& symbol, Timeframe tf) const {
  SeriesKey key{symbol, tf};
  return store_.find(key) != store_.end();
}

OHLCVContainer& MarketDataEngine::register_series(const std::string& symbol,
                                                   Timeframe tf,
                                                   OHLCVContainer container) {
  SeriesKey key{symbol, tf};
  auto [it, _] = store_.insert_or_assign(key, std::move(container));
  return it->second;
}

std::vector<std::string> MarketDataEngine::symbols() const {
  std::vector<std::string> result;
  for (const auto& [key, _] : store_) {
    if (std::find(result.begin(), result.end(), key.symbol) == result.end()) {
      result.push_back(key.symbol);
    }
  }
  return result;
}

std::vector<Timeframe> MarketDataEngine::available_timeframes(const std::string& symbol) const {
  std::vector<Timeframe> result;
  for (const auto& [key, _] : store_) {
    if (key.symbol == symbol) result.push_back(key.tf);
  }
  return result;
}

Result<OHLCVContainer> MarketDataEngine::aggregate(const std::string& symbol,
                                                    Timeframe source_tf,
                                                    Timeframe target_tf) {
  auto source = get_series(symbol, source_tf);
  if (source.is_err()) return source.error();

  SeriesKey cache_key{symbol, target_tf};
  auto cached = store_.find(cache_key);
  if (cached != store_.end()) {
    return cached->second;
  }

  auto aggregated = TimeframeAggregator::aggregate(source.value(), target_tf);
  if (aggregated.is_err()) return aggregated.error();

  auto& stored = register_series(symbol, target_tf, std::move(aggregated.value()));
  return stored;
}

void MarketDataEngine::clear() {
  store_.clear();
}

} // namespace quant
