#include "quant/statistics/descriptive.h"

namespace quant {

Result<DescriptiveStats> DescriptiveStats::compute(const std::vector<double>& data) {
  if (data.empty()) {
    return Error(ErrorCode::InsufficientData, "cannot compute stats on empty data");
  }
  DescriptiveStats s;
  s.count = data.size();
  s.sum = std::accumulate(data.begin(), data.end(), 0.0);
  s.mean = s.sum / static_cast<double>(s.count);
  s.min = *std::min_element(data.begin(), data.end());
  s.max = *std::max_element(data.begin(), data.end());

  double var_acc = 0.0, skew_acc = 0.0, kurt_acc = 0.0;
  for (auto x : data) {
    double d = x - s.mean;
    var_acc += d * d;
    skew_acc += d * d * d;
    kurt_acc += d * d * d * d;
  }
  s.variance = var_acc / static_cast<double>(s.count);
  s.stddev = std::sqrt(s.variance);

  if (s.variance > 0.0) {
    double n = static_cast<double>(s.count);
    double m2 = var_acc / n;
    double m3 = skew_acc / n;
    double m4 = kurt_acc / n;
    s.skewness = m3 / std::pow(m2, 1.5);
    s.kurtosis = m4 / (m2 * m2) - 3.0;
  }

  auto sorted = data;
  std::sort(sorted.begin(), sorted.end());
  auto quantile = [&](double q) -> double {
    double idx = q * (static_cast<double>(sorted.size()) - 1.0);
    size_t lo = static_cast<size_t>(idx);
    size_t hi = std::min(lo + 1, sorted.size() - 1);
    double frac = idx - static_cast<double>(lo);
    return sorted[lo] + frac * (sorted[hi] - sorted[lo]);
  };
  s.q1 = quantile(0.25);
  s.median = quantile(0.50);
  s.q3 = quantile(0.75);
  s.iqr = s.q3 - s.q1;

  return s;
}

Result<DescriptiveStats> DescriptiveStats::compute_weighted(const std::vector<double>& data,
                                                             const std::vector<double>& weights) {
  if (data.empty()) return Error(ErrorCode::InsufficientData, "empty data");
  if (data.size() != weights.size()) return Error(ErrorCode::InvalidArgument, "size mismatch");
  DescriptiveStats s;
  s.count = data.size();
  double wsum = std::accumulate(weights.begin(), weights.end(), 0.0);
  if (wsum == 0.0) return Error(ErrorCode::DivisionByZero, "weight sum is zero");
  for (size_t i = 0; i < data.size(); ++i) s.sum += data[i] * weights[i];
  s.mean = s.sum / wsum;
  s.min = *std::min_element(data.begin(), data.end());
  s.max = *std::max_element(data.begin(), data.end());
  double var_acc = 0.0;
  for (size_t i = 0; i < data.size(); ++i) {
    double d = data[i] - s.mean;
    var_acc += weights[i] * d * d;
  }
  s.variance = var_acc / wsum;
  s.stddev = std::sqrt(s.variance);
  return s;
}

double DescriptiveStats::mean_of(const std::vector<double>& data) {
  if (data.empty()) return 0.0;
  return std::accumulate(data.begin(), data.end(), 0.0) / static_cast<double>(data.size());
}

double DescriptiveStats::variance_of(const std::vector<double>& data, double mean_val) {
  if (data.size() < 2) return 0.0;
  double acc = 0.0;
  for (auto x : data) { double d = x - mean_val; acc += d * d; }
  return acc / static_cast<double>(data.size());
}

double DescriptiveStats::stddev_of(double variance) {
  return std::sqrt(variance);
}

double DescriptiveStats::covariance(const std::vector<double>& x, const std::vector<double>& y) {
  if (x.size() != y.size() || x.empty()) return 0.0;
  double mx = mean_of(x), my = mean_of(y);
  double acc = 0.0;
  for (size_t i = 0; i < x.size(); ++i) acc += (x[i] - mx) * (y[i] - my);
  return acc / static_cast<double>(x.size());
}

double DescriptiveStats::autocorrelation(const std::vector<double>& data, uint32_t lag) {
  if (data.size() <= lag) return 0.0;
  double m = mean_of(data);
  double num = 0.0, den = 0.0;
  for (size_t i = 0; i < data.size() - lag; ++i) {
    num += (data[i] - m) * (data[i + lag] - m);
    den += (data[i] - m) * (data[i] - m);
  }
  return den != 0.0 ? num / den : 0.0;
}

} // namespace quant
