#ifndef QUANT_CORE_CONFIG_H
#define QUANT_CORE_CONFIG_H

#include "result.h"
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>
#include <variant>
#include <memory>

namespace quant {

class Config {
public:
  using Value = std::variant<std::nullptr_t, bool, int64_t, double, std::string,
                              std::vector<Config>, std::unordered_map<std::string, Config>>;

  Config() = default;
  Config(Value val) : value_(std::move(val)) {}

  static Config object();
  static Config array();

  bool is_null() const;
  bool is_bool() const;
  bool is_int() const;
  bool is_double() const;
  bool is_string() const;
  bool is_array() const;
  bool is_object() const;

  Result<bool> get_bool() const;
  Result<int64_t> get_int() const;
  Result<double> get_double() const;
  Result<std::string> get_string() const;
  Result<std::vector<Config>> get_array() const;

  Config& operator[](std::string_view key);
  const Config& operator[](std::string_view key) const;
  void set(std::string_view key, Config val);
  bool has(std::string_view key) const;

  Result<Config> get(std::string_view path) const;

  void push_back(Config val);
  size_t size() const;

  std::vector<std::string> keys() const;

  std::string to_string() const;

  static Config parse_json(std::string_view json);

private:
  Value value_{nullptr};
  std::unordered_map<std::string, Config> children_;
  std::vector<Config> items_;
};

} // namespace quant
#endif
