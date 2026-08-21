#include "quant/statistics/regression.h"

#include <cmath>

namespace quant {
namespace statistics {

namespace {

// Validate a finite, non-empty series with at least `min_n` observations.
// Returns Error on failure, otherwise Error::ok().  The result is unset
// (empty) unless the caller invokes error() when is_ok() is false; we use
// Result<Error> semantics indirectly via a bool + out-param-free design.
bool validate_series(const std::vector<double>& v, size_t min_n, Error& err) {
  if (v.empty()) {
    err = Error(ErrorCode::InsufficientData, "cannot regress on empty data");
    return false;
  }
  if (v.size() < min_n) {
    err = Error(ErrorCode::InsufficientData,
                "need at least " + std::to_string(min_n) +
                    " observations, got " + std::to_string(v.size()));
    return false;
  }
  for (double x : v) {
    if (!std::isfinite(x)) {
      err = Error(ErrorCode::DomainError, "series contains NaN or Inf");
      return false;
    }
  }
  return true;
}

// Validate that two series are finite, non-empty, equal length, and each has
// at least `min_n` observations.
bool validate_pair(const std::vector<double>& x, const std::vector<double>& y,
                   size_t min_n, Error& err) {
  if (x.size() != y.size()) {
    err = Error(ErrorCode::InvalidArgument, "x and y size mismatch");
    return false;
  }
  if (!validate_series(x, min_n, err)) return false;
  return validate_series(y, min_n, err);
}

// One-pass accumulation of the OLS sufficient statistics.
struct OLSStats {
  double xbar{0.0};
  double Sxx{0.0};
  double Sxy{0.0};
  double Syy{0.0};
};

OLSStats accumulate(const std::vector<double>& x, const std::vector<double>& y) {
  const double n = static_cast<double>(x.size());
  double sum_x = 0.0, sum_y = 0.0;
  for (size_t i = 0; i < x.size(); ++i) {
    sum_x += x[i];
    sum_y += y[i];
  }
  const double xbar = sum_x / n;
  const double ybar = sum_y / n;

  OLSStats s;
  s.xbar = xbar;
  for (size_t i = 0; i < x.size(); ++i) {
    const double dx = x[i] - xbar;
    const double dy = y[i] - ybar;
    s.Sxx += dx * dx;
    s.Syy += dy * dy;
    s.Sxy += dx * dy;
  }
  return s;
}

}  // namespace

Result<double> Regression::slope(const std::vector<double>& y) {
  Error err;
  if (!validate_series(y, 2, err)) return Result<double>(err);

  // x_i = i (implicit index), xbar = (n-1)/2.
  const double n = static_cast<double>(y.size());
  const double xbar = (n - 1.0) / 2.0;
  const double ybar = [&] {
    double s = 0.0;
    for (double v : y) s += v;
    return s / n;
  }();

  double Sxy = 0.0, Sxx = 0.0;
  for (size_t i = 0; i < y.size(); ++i) {
    const double dx = static_cast<double>(i) - xbar;
    const double dy = y[i] - ybar;
    Sxy += dx * dy;
    Sxx += dx * dx;
  }
  if (Sxx == 0.0) {
    return Result<double>(
        Error(ErrorCode::DivisionByZero, "zero x variance (degenerate index)"));
  }
  return Result<double>(Sxy / Sxx);
}

Result<double> Regression::intercept(const std::vector<double>& y) {
  Error err;
  if (!validate_series(y, 2, err)) return Result<double>(err);

  const double n = static_cast<double>(y.size());
  const double xbar = (n - 1.0) / 2.0;
  const double ybar = [&] {
    double s = 0.0;
    for (double v : y) s += v;
    return s / n;
  }();

  double Sxy = 0.0, Sxx = 0.0;
  for (size_t i = 0; i < y.size(); ++i) {
    const double dx = static_cast<double>(i) - xbar;
    const double dy = y[i] - ybar;
    Sxy += dx * dy;
    Sxx += dx * dx;
  }
  if (Sxx == 0.0) {
    return Result<double>(
        Error(ErrorCode::DivisionByZero, "zero x variance (degenerate index)"));
  }
  const double beta = Sxy / Sxx;
  return Result<double>(ybar - beta * xbar);
}

Result<double> Regression::correlation(const std::vector<double>& x,
                                       const std::vector<double>& y) {
  Error err;
  if (!validate_pair(x, y, 2, err)) return Result<double>(err);

  const OLSStats s = accumulate(x, y);
  if (s.Sxx == 0.0 || s.Syy == 0.0) {
    return Result<double>(
        Error(ErrorCode::DivisionByZero, "zero variance in x or y"));
  }
  const double r = s.Sxy / std::sqrt(s.Sxx * s.Syy);
  // Clamp to [-1, 1] to remove floating-point overshoot beyond the unit disk.
  const double clamped = std::max(-1.0, std::min(1.0, r));
  return Result<double>(clamped);
}

Result<double> Regression::r_squared(const std::vector<double>& x,
                                     const std::vector<double>& y) {
  Error err;
  if (!validate_pair(x, y, 2, err)) return Result<double>(err);

  const OLSStats s = accumulate(x, y);
  if (s.Sxx == 0.0 || s.Syy == 0.0) {
    return Result<double>(
        Error(ErrorCode::DivisionByZero, "zero variance in x or y"));
  }
  const double r = s.Sxy / std::sqrt(s.Sxx * s.Syy);
  const double clamped = std::max(-1.0, std::min(1.0, r));
  return Result<double>(clamped * clamped);
}

Result<double> Regression::standard_error(const std::vector<double>& x,
                                          const std::vector<double>& y) {
  Error err;
  if (!validate_pair(x, y, 2, err)) return Result<double>(err);

  const OLSStats s = accumulate(x, y);
  if (s.Sxx == 0.0) {
    return Result<double>(
        Error(ErrorCode::DivisionByZero, "zero x variance"));
  }
const double beta = s.Sxy / s.Sxx;
  // alpha = ybar - beta * xbar; recompute ybar cleanly below.
  const double n = static_cast<double>(x.size());
  double sum_y = 0.0;
  for (double v : y) sum_y += v;
  const double ybar = sum_y / n;
  const double intercept_val = ybar - beta * s.xbar;

  double sse = 0.0;
  for (size_t i = 0; i < x.size(); ++i) {
    const double e = y[i] - (intercept_val + beta * x[i]);
    sse += e * e;
  }
  const double se = std::sqrt(sse / (n - 2.0));
  return Result<double>(se);
}

}  // namespace statistics
}  // namespace quant
