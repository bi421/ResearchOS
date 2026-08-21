#ifndef QUANT_STATISTICS_CORRELATION_H
#define QUANT_STATISTICS_CORRELATION_H

#include "quant/core/result.h"
#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>

namespace quant {

struct CorrelationResult {
  double coefficient{0.0};
  double p_value{0.0};
  size_t n{0};
};

struct Correlation {
  static Result<CorrelationResult> pearson(const std::vector<double>& x,
                                           const std::vector<double>& y);

  static Result<CorrelationResult> spearman(const std::vector<double>& x,
                                            const std::vector<double>& y);

  static Result<std::vector<std::vector<double>>> covariance_matrix(
      const std::vector<std::vector<double>>& data);

  static Result<std::vector<std::vector<double>>> correlation_matrix(
      const std::vector<std::vector<double>>& data);

  static Result<double> r_squared(const std::vector<double>& actual,
                                  const std::vector<double>& predicted);
};

} // namespace quant
#endif
