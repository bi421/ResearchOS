#ifndef QUANT_STATISTICS_DESCRIPTIVE_H
#define QUANT_STATISTICS_DESCRIPTIVE_H

#include "quant/core/result.h"
#include <vector>
#include <algorithm>
#include <cmath>
#include <numeric>

namespace quant {

struct DescriptiveStats {
  size_t count{0};
  double sum{0.0};
  double mean{0.0};
  double variance{0.0};
  double stddev{0.0};
  double skewness{0.0};
  double kurtosis{0.0};
  double min{0.0};
  double max{0.0};
  double q1{0.0};
  double median{0.0};
  double q3{0.0};
  double iqr{0.0};

  static Result<DescriptiveStats> compute(const std::vector<double>& data);
  static Result<DescriptiveStats> compute_weighted(const std::vector<double>& data,
                                                    const std::vector<double>& weights);

  static double mean_of(const std::vector<double>& data);
  static double variance_of(const std::vector<double>& data, double mean_val);
  static double stddev_of(double variance);
  static double covariance(const std::vector<double>& x, const std::vector<double>& y);
  static double autocorrelation(const std::vector<double>& data, uint32_t lag = 1);
};

} // namespace quant
#endif
