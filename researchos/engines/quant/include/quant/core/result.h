#ifndef QUANT_CORE_RESULT_H
#define QUANT_CORE_RESULT_H

#include "error.h"
#include <type_traits>
#include <utility>
#include <variant>

namespace quant {

template <typename T>
class Result {
public:
  Result(T value) : data_(std::move(value)) {}
  Result(Error error) : data_(std::move(error)) {}

  static Result ok(T value) { return Result(std::move(value)); }
  static Result fail(Error err) { return Result(std::move(err)); }

  bool is_ok() const { return std::holds_alternative<T>(data_); }
  bool is_err() const { return std::holds_alternative<Error>(data_); }
  explicit operator bool() const { return is_ok(); }

  T& value() & { return std::get<T>(data_); }
  const T& value() const& { return std::get<T>(data_); }
  T&& value() && { return std::move(std::get<T>(data_)); }

  Error& error() & { return std::get<Error>(data_); }
  const Error& error() const& { return std::get<Error>(data_); }

  template <typename Fn>
  auto map(Fn&& fn) -> Result<std::invoke_result_t<Fn, T>> {
    using U = std::invoke_result_t<Fn, T>;
    if (is_ok()) {
      return Result<U>::ok(std::forward<Fn>(fn)(value()));
    }
    return Result<U>(error());
  }

  template <typename Fn>
  auto and_then(Fn&& fn) -> std::invoke_result_t<Fn, T> {
    using R = std::invoke_result_t<Fn, T>;
    if (is_ok()) {
      return std::forward<Fn>(fn)(value());
    }
    return R(error());
  }

  T value_or(T default_val) const {
    return is_ok() ? value() : default_val;
  }

private:
  std::variant<T, Error> data_;
};

template <>
class Result<void> {
public:
  Result() = default;
  Result(Error error) : error_(std::move(error)), has_error_(true) {}

  static Result ok() { return {}; }
  static Result fail(Error err) { return Result(err); }

  bool is_ok() const { return !has_error_; }
  bool is_err() const { return has_error_; }
  explicit operator bool() const { return is_ok(); }

  Error& error() { return error_; }
  const Error& error() const { return error_; }

private:
  Error error_;
  bool has_error_{false};
};

} // namespace quant
#endif
