#ifndef QUANT_CORE_ERROR_H
#define QUANT_CORE_ERROR_H

#include <cstdint>
#include <string>
#include <string_view>
#include <source_location>

namespace quant {

enum class ErrorCode : uint32_t {
  None = 0,
  InvalidArgument,
  OutOfBounds,
  DivisionByZero,
  InsufficientData,
  ConvergenceFailure,
  SingularMatrix,
  DomainError,
  ConfigKeyNotFound,
  ConfigTypeMismatch,
  FileNotFound,
  NotImplemented,
  NumericOverflow,
  RuntimeError,
};

class Error {
public:
  Error() = default;
  Error(ErrorCode code, std::string message,
        std::source_location loc = std::source_location::current());

  ErrorCode code() const { return code_; }
  const std::string& message() const { return message_; }
  const std::string& file() const { return file_; }
  uint32_t line() const { return line_; }
  explicit operator bool() const { return code_ != ErrorCode::None; }
  std::string what() const;

  static Error ok() { return {}; }

private:
  ErrorCode code_{ErrorCode::None};
  std::string message_;
  std::string file_;
  uint32_t line_{0};
};

} // namespace quant
#endif
