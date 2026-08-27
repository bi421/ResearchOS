#include "quant/core/error.h"
#include <format>

namespace quant {

Error::Error(ErrorCode code, std::string message, std::source_location loc)
    : code_(code), message_(std::move(message)),
      file_(loc.file_name()), line_(loc.line()) {}

std::string Error::what() const {
  return std::format("[{}:{}] Error {}: {}",
                     file_, line_,
                     static_cast<uint32_t>(code_),
                     message_);
}

} // namespace quant
