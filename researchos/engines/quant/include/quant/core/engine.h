#ifndef QUANT_CORE_ENGINE_H
#define QUANT_CORE_ENGINE_H

#include "result.h"
#include "config.h"
#include "../market/market_data_engine.h"
#include <string>
#include <string_view>
#include <memory>

namespace quant {

struct Version {
  uint32_t major;
  uint32_t minor;
  uint32_t patch;
  std::string to_string() const;
  static Version current();
};

class QuantEngine {
public:
  QuantEngine();
  ~QuantEngine();

  QuantEngine(const QuantEngine&) = delete;
  QuantEngine& operator=(const QuantEngine&) = delete;
  QuantEngine(QuantEngine&&) = default;
  QuantEngine& operator=(QuantEngine&&) = default;

  static Version version();
  static std::string about();

  Result<void> initialize(const Config& config);
  bool is_initialized() const { return initialized_; }
  void shutdown();

  const Config& config() const { return config_; }
  MarketDataEngine& market_data() { return market_data_; }
  const MarketDataEngine& market_data() const { return market_data_; }

private:
  bool initialized_{false};
  Config config_;
  MarketDataEngine market_data_;
};

} // namespace quant
#endif
