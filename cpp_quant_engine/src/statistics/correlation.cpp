#include "quant/statistics/correlation.h"
#include "quant/statistics/descriptive.h"

namespace quant {

Result<CorrelationResult> Correlation::pearson(const std::vector<double>& x,
                                               const std::vector<double>& y) {
  if (x.size() != y.size()) return Error(ErrorCode::InvalidArgument, "size mismatch");
  if (x.size() < 3) return Error(ErrorCode::InsufficientData, "need at least 3 points");

  size_t n = x.size();
  double sum_x = 0.0, sum_y = 0.0, sum_xy = 0.0, sum_x2 = 0.0, sum_y2 = 0.0;
  for (size_t i = 0; i < n; ++i) {
    sum_x += x[i]; sum_y += y[i];
    sum_xy += x[i] * y[i];
    sum_x2 += x[i] * x[i];
    sum_y2 += y[i] * y[i];
  }
  double num = n * sum_xy - sum_x * sum_y;
  double den = std::sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y));
  if (den == 0.0) return Error(ErrorCode::DivisionByZero, "zero denominator in Pearson");

  CorrelationResult r;
  r.coefficient = num / den;
  r.n = n;
  double t = r.coefficient * std::sqrt(static_cast<double>(n - 2) / (1.0 - r.coefficient * r.coefficient));
  r.p_value = 2.0 * (1.0 - std::erf(std::abs(t) / std::sqrt(2.0)));
  return r;
}

Result<CorrelationResult> Correlation::spearman(const std::vector<double>& x,
                                                const std::vector<double>& y) {
  if (x.size() != y.size()) return Error(ErrorCode::InvalidArgument, "size mismatch");
  if (x.size() < 3) return Error(ErrorCode::InsufficientData, "need at least 3 points");

  size_t n = x.size();
  std::vector<size_t> idx(n);
  std::iota(idx.begin(), idx.end(), 0);

  auto rank = [&](const std::vector<double>& v) -> std::vector<double> {
    std::vector<size_t> order = idx;
    std::sort(order.begin(), order.end(), [&](size_t a, size_t b) { return v[a] < v[b]; });
    std::vector<double> ranks(n);
    for (size_t i = 0; i < n;) {
      size_t j = i;
      while (j < n && v[order[j]] == v[order[i]]) ++j;
      double avg = static_cast<double>(i + j - 1) / 2.0 + 1.0;
      for (size_t k = i; k < j; ++k) ranks[order[k]] = avg;
      i = j;
    }
    return ranks;
  };

  auto rx = rank(x), ry = rank(y);
  return pearson(rx, ry);
}

Result<std::vector<std::vector<double>>> Correlation::covariance_matrix(
    const std::vector<std::vector<double>>& data) {
  if (data.empty()) return Error(ErrorCode::InsufficientData, "empty data");
  size_t n = data.size();
  size_t m = data[0].size();
  for (auto& row : data)
    if (row.size() != m) return Error(ErrorCode::InvalidArgument, "inconsistent row sizes");

  std::vector<double> means(n);
  for (size_t i = 0; i < n; ++i)
    means[i] = DescriptiveStats::mean_of(data[i]);

  std::vector<std::vector<double>> cov(n, std::vector<double>(n, 0.0));
  for (size_t i = 0; i < n; ++i)
    for (size_t j = 0; j <= i; ++j) {
      double acc = 0.0;
      for (size_t k = 0; k < m; ++k)
        acc += (data[i][k] - means[i]) * (data[j][k] - means[j]);
      cov[i][j] = cov[j][i] = acc / static_cast<double>(m);
    }
  return cov;
}

Result<std::vector<std::vector<double>>> Correlation::correlation_matrix(
    const std::vector<std::vector<double>>& data) {
  auto cov_res = covariance_matrix(data);
  if (cov_res.is_err()) return cov_res.error();
  auto& cov = cov_res.value();
  size_t n = cov.size();
  for (size_t i = 0; i < n; ++i) {
    double sd = std::sqrt(cov[i][i]);
    if (sd == 0.0) return Error(ErrorCode::SingularMatrix, "zero variance in series");
    for (size_t j = 0; j < n; ++j)
      cov[i][j] /= sd * std::sqrt(cov[j][j]);
  }
  return cov;
}

Result<double> Correlation::r_squared(const std::vector<double>& actual,
                                      const std::vector<double>& predicted) {
  auto corr = pearson(actual, predicted);
  if (corr.is_err()) return corr.error();
  return corr.value().coefficient * corr.value().coefficient;
}

} // namespace quant
