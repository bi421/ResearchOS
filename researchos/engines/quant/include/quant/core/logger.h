#ifndef QUANT_CORE_LOGGER_H
#define QUANT_CORE_LOGGER_H

#include <string>
#include <string_view>
#include <source_location>
#include <format>
#include <chrono>
#include <mutex>
#include <vector>
#include <functional>
#include <source_location>

namespace quant {

enum class LogLevel : uint8_t {
  Trace = 0,
  Debug = 1,
  Info = 2,
  Warn = 3,
  Error = 4,
  Fatal = 5,
};

struct LogEntry {
  LogLevel level;
  std::string message;
  std::string file;
  uint32_t line;
  std::string function;
  std::chrono::system_clock::time_point timestamp;
};

class Logger {
public:
  using Sink = std::function<void(const LogEntry&)>;

  static Logger& instance();

  void set_level(LogLevel level) { level_ = level; }
  LogLevel level() const { return level_; }

  void add_sink(Sink sink);
  void clear_sinks();

  void log(LogLevel level, std::string_view message,
           std::source_location loc = std::source_location::current());

  void trace(std::string_view msg, std::source_location loc = std::source_location::current());
  void debug(std::string_view msg, std::source_location loc = std::source_location::current());
  void info(std::string_view msg, std::source_location loc = std::source_location::current());
  void warn(std::string_view msg, std::source_location loc = std::source_location::current());
  void error(std::string_view msg, std::source_location loc = std::source_location::current());
  void fatal(std::string_view msg, std::source_location loc = std::source_location::current());

  template <typename... Args>
  void logfmt(LogLevel level, std::string_view fmt, Args&&... args,
              std::source_location loc = std::source_location::current()) {
    log(level, std::vformat(fmt, std::make_format_args(std::forward<Args>(args)...)), loc);
  }

  const std::vector<LogEntry>& entries() const { return entries_; }
  void clear() { entries_.clear(); }

private:
  Logger() = default;
  LogLevel level_{LogLevel::Info};
  std::vector<Sink> sinks_;
  std::vector<LogEntry> entries_;
  mutable std::mutex mtx_;
};

} // namespace quant
#endif
