#include "quant/core/logger.h"

namespace quant {

Logger& Logger::instance() {
  static Logger inst;
  return inst;
}

void Logger::add_sink(Sink sink) {
  std::lock_guard lock(mtx_);
  sinks_.push_back(std::move(sink));
}

void Logger::clear_sinks() {
  std::lock_guard lock(mtx_);
  sinks_.clear();
}

void Logger::log(LogLevel level, std::string_view message, std::source_location loc) {
  if (level < level_) return;
  std::lock_guard lock(mtx_);
  auto& entry = entries_.emplace_back();
  entry.level = level;
  entry.message = message;
  entry.file = loc.file_name();
  entry.line = loc.line();
  entry.function = loc.function_name();
  entry.timestamp = std::chrono::system_clock::now();
  for (auto& sink : sinks_) {
    sink(entry);
  }
}

void Logger::trace(std::string_view msg, std::source_location loc) { log(LogLevel::Trace, msg, loc); }
void Logger::debug(std::string_view msg, std::source_location loc) { log(LogLevel::Debug, msg, loc); }
void Logger::info(std::string_view msg, std::source_location loc) { log(LogLevel::Info, msg, loc); }
void Logger::warn(std::string_view msg, std::source_location loc) { log(LogLevel::Warn, msg, loc); }
void Logger::error(std::string_view msg, std::source_location loc) { log(LogLevel::Error, msg, loc); }
void Logger::fatal(std::string_view msg, std::source_location loc) { log(LogLevel::Fatal, msg, loc); }

} // namespace quant
