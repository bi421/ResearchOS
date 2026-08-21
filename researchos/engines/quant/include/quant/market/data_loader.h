#ifndef QUANT_MARKET_DATA_LOADER_H
#define QUANT_MARKET_DATA_LOADER_H

#include "candle.h"
#include "ohlcv_container.h"
#include "quant/core/result.h"
#include <string>
#include <string_view>
#include <vector>
#include <filesystem>

namespace quant {

enum class FileFormat : uint8_t {
  CSV,
  CSV_MT4,
  CSV_Generic,
};

struct LoadConfig {
  FileFormat format{FileFormat::CSV};
  bool has_header{true};
  char delimiter{','};
  size_t col_timestamp{0};
  size_t col_open{1};
  size_t col_high{2};
  size_t col_low{3};
  size_t col_close{4};
  size_t col_volume{5};
  std::string datetime_format{"%Y-%m-%d %H:%M:%S"};
  Timeframe target_timeframe{Timeframe::M1};
};

class DataLoader {
public:
  DataLoader() = default;

  explicit DataLoader(std::string symbol);
  void set_symbol(std::string s) { symbol_ = std::move(s); }

  Result<OHLCVContainer> load_file(const std::filesystem::path& path,
                                    const LoadConfig& cfg = {});

  Result<OHLCVContainer> load_csv(const std::filesystem::path& path,
                                   const LoadConfig& cfg = {});

  Result<std::vector<OHLCVContainer>> load_directory(
      const std::filesystem::path& dir,
      const LoadConfig& cfg = {});

  static Result<std::vector<Candle>> parse_csv_string(std::string_view data,
                                                       const LoadConfig& cfg = {});

  static TimePoint parse_datetime(const std::string& str,
                                   const std::string& fmt = "%Y-%m-%d %H:%M:%S");

  static std::string format_datetime(TimePoint tp,
                                      const std::string& fmt = "%Y-%m-%d %H:%M:%S");

private:
  std::string symbol_;
};

} // namespace quant
#endif
