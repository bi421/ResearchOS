#ifndef QUANT_STRATEGY_STRATEGY_INTERNAL_H
#define QUANT_STRATEGY_STRATEGY_INTERNAL_H

#include "quant/market/types.h"
#include <cstdint>
#include <initializer_list>
#include <string>
#include <utility>
#include <vector>

namespace quant {
namespace strategy {
namespace detail {

// â”€â”€ SHA-256 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Self-contained SHA-256 (FIPS 180-4) returning the hex digest.
std::string sha256_hex(const std::string& input);

// â”€â”€ Canonical serialization â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Deterministic byte-level representation used for input/result hashes:
// keys sorted alphabetically, numbers fixed-point {:.10f}, strings JSON-escaped.

struct UtcParts {
  int year;
  int month;
  int day;
  int hour;
  int weekday;    // 0 = Sunday .. 6 = Saturday
  int64_t day_key;
};

UtcParts utc_parts(TimePoint tp);
std::string iso8601(TimePoint tp);

std::string canonical_double(double v);
std::string canonical_int(int64_t v);
std::string canonical_bool(bool b);
std::string canonical_str(const std::string& s);
std::string canonical_double_array(const std::vector<double>& a);
std::string canonical_int_array(const std::vector<int64_t>& a);

using KV = std::pair<std::string, std::string>;
std::string canonical_object(std::initializer_list<KV> kvs);
std::string canonical_array(std::initializer_list<std::string> items);
std::string canonical_array(const std::vector<std::string>& items);

} // namespace detail
} // namespace strategy
} // namespace quant
#endif
