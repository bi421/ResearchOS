#include "quant/core/engine.h"
#include "quant/core/logger.h"
#include <format>

namespace quant {

Version Version::current() {
  return {0, 1, 0};
}

std::string Version::to_string() const {
  return std::format("{}.{}.{}", major, minor, patch);
}

QuantEngine::QuantEngine() {
  Logger::instance().info("QuantEngine constructed");
}

QuantEngine::~QuantEngine() {
  if (initialized_) shutdown();
}

Result<void> QuantEngine::initialize(const Config& config) {
  if (initialized_) {
    return Error(ErrorCode::RuntimeError, "QuantEngine already initialized");
  }
  config_ = config;
  initialized_ = true;

  if (config.has("market_data.load_path")) {
    auto path = config["market_data"]["load_path"].get_string().value_or("");
    if (!path.empty()) {
      LoadConfig load_cfg;
      load_cfg.target_timeframe = Timeframe::M1;
      auto r = market_data_.load_from_file(path, load_cfg);
      if (r.is_err()) {
        Logger::instance().info(std::format("Market data load skipped: {}", r.error().message()));
      }
    }
  }

  auto msg = std::format("QuantEngine initialized with config: {}", config_.to_string());
  Logger::instance().info(msg);
  return Result<void>::ok();
}

void QuantEngine::shutdown() {
  if (!initialized_) return;
  initialized_ = false;
  Logger::instance().info("QuantEngine shut down");
}

Version QuantEngine::version() {
  return Version::current();
}

std::string QuantEngine::about() {
  return std::format("QuantEngine v{} - C++ Quant Computing Engine for TRADER-OS",
                     Version::current().to_string());
}

} // namespace quant
