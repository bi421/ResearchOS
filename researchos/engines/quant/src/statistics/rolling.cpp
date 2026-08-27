#include "quant/statistics/rolling.h"

#include <limits>

namespace quant {

Result<std::vector<double>> RollingWindow::mean(const std::vector<double>& data,
                                                 size_t window) {
  if (window == 0) return Error(ErrorCode::InvalidArgument, "window must be > 0");
  if (data.size() < window) {
    return Error(ErrorCode::InsufficientData,
                 "window size exceeds data length");
  }

  const size_t n = data.size();
  std::vector<double> out(n - window + 1);
  double sum = 0.0;

  // Initialise the first window.
  for (size_t i = 0; i < window; ++i) sum += data[i];
  out[0] = sum / static_cast<double>(window);

  // Slide: add the incoming element, drop the outgoing element.  O(n).
  for (size_t i = window; i < n; ++i) {
    sum += data[i];
    sum -= data[i - window];
    out[i - window + 1] = sum / static_cast<double>(window);
  }

  return out;
}

Result<std::vector<double>> RollingWindow::volatility(const std::vector<double>& data,
                                                       size_t window, int ddof) {
  if (window == 0) return Error(ErrorCode::InvalidArgument, "window must be > 0");
  if (data.size() < window) {
    return Error(ErrorCode::InsufficientData,
                 "window size exceeds data length");
  }
  if (ddof < 0 || static_cast<size_t>(ddof) >= window) {
    return Error(ErrorCode::InvalidArgument,
                 "ddof must be in [0, window)");
  }

  const size_t n = data.size();
  const double win = static_cast<double>(window);
  const double denom = win - static_cast<double>(ddof);
  std::vector<double> out(n - window + 1);

  double sum = 0.0;
  double sum_sq = 0.0;
  for (size_t i = 0; i < window; ++i) {
    sum += data[i];
    sum_sq += data[i] * data[i];
  }

// Variance = (sum_sq - sum^2 / window) / (window - ddof).
  // One-pass formula. For constant (or near-constant) input, catastrophic
  // cancellation can leave a tiny positive residual; clamp anything below a
  // scale-relative epsilon to exactly 0 so the fast path matches the
  // reference (which returns 0) numerically.
  auto vol_of = [&](double s, double s2) -> double {
    double numerator = s2 - s * s / win;
    double scale = s2 + (s * s / win);
    double eps = std::numeric_limits<double>::epsilon();
    if (scale > 0.0 && numerator <= eps * 8.0 * scale) {
      return 0.0;
    }
    double var = numerator / denom;
    return var > 0.0 ? std::sqrt(var) : 0.0;
  };

  out[0] = vol_of(sum, sum_sq);
  for (size_t i = window; i < n; ++i) {
    sum += data[i];
    sum_sq += data[i] * data[i];
    sum -= data[i - window];
    sum_sq -= data[i - window] * data[i - window];
    out[i - window + 1] = vol_of(sum, sum_sq);
  }

  return out;
}

Result<std::vector<double>> RollingWindow::variance(const std::vector<double>& data,
                                                     size_t window, int ddof) {
  if (window == 0) return Error(ErrorCode::InvalidArgument, "window must be > 0");
  if (data.size() < window) {
    return Error(ErrorCode::InsufficientData,
                 "window size exceeds data length");
  }
  if (ddof < 0 || static_cast<size_t>(ddof) >= window) {
    return Error(ErrorCode::InvalidArgument,
                 "ddof must be in [0, window)");
  }

  const size_t n = data.size();
  const double win = static_cast<double>(window);
  const double denom = win - static_cast<double>(ddof);
  std::vector<double> out(n - window + 1);

  double sum = 0.0;
  double sum_sq = 0.0;
  for (size_t i = 0; i < window; ++i) {
    sum += data[i];
    sum_sq += data[i] * data[i];
  }

  // Variance = (sum_sq - sum^2 / window) / (window - ddof). One-pass formula.
  // For constant (or near-constant) input, catastrophic cancellation can leave
  // a tiny positive residual; clamp anything below a scale-relative epsilon to
  // exactly 0 so the variance matches the volatility path (which returns 0).
  auto var_of = [&](double s, double s2) -> double {
    double numerator = s2 - s * s / win;
    double scale = s2 + (s * s / win);
    double eps = std::numeric_limits<double>::epsilon();
    if (scale > 0.0 && numerator <= eps * 8.0 * scale) {
      return 0.0;
    }
    double var = numerator / denom;
    return var > 0.0 ? var : 0.0;
  };

  out[0] = var_of(sum, sum_sq);
  for (size_t i = window; i < n; ++i) {
    sum += data[i];
    sum_sq += data[i] * data[i];
    sum -= data[i - window];
    sum_sq -= data[i - window] * data[i - window];
    out[i - window + 1] = var_of(sum, sum_sq);
  }

  return out;
}

Result<std::vector<double>> RollingWindow::volatility_reference(
    const std::vector<double>& data, size_t window, int ddof) {
  if (window == 0) return Error(ErrorCode::InvalidArgument, "window must be > 0");
  if (data.size() < window) {
    return Error(ErrorCode::InsufficientData,
                 "window size exceeds data length");
  }
  if (ddof < 0 || static_cast<size_t>(ddof) >= window) {
    return Error(ErrorCode::InvalidArgument,
                 "ddof must be in [0, window)");
  }

  const size_t n = data.size();
  const double win = static_cast<double>(window);
  const double denom = win - static_cast<double>(ddof);
  std::vector<double> out(n - window + 1);

  for (size_t i = 0; i <= n - window; ++i) {
    double mean = 0.0;
    for (size_t j = i; j < i + window; ++j) mean += data[j];
    mean /= win;

    double acc = 0.0;
    for (size_t j = i; j < i + window; ++j) {
      double d = data[j] - mean;
      acc += d * d;
    }
    double var = acc / denom;
    out[i] = var > 0.0 ? std::sqrt(var) : 0.0;
  }

  return out;
}

}  // namespace quant
