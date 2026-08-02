#include "quant/simulation/rng.h"
#include <cmath>
#include <numeric>

namespace quant {

RNG::RNG(uint64_t seed) : seed_(seed), rng_(seed) {}

double RNG::uniform(double min, double max) {
  std::uniform_real_distribution<double> dist(min, max);
  return dist(rng_);
}

double RNG::normal(double mean, double stddev) {
  std::normal_distribution<double> dist(mean, stddev);
  return dist(rng_);
}

double RNG::cauchy(double location, double scale) {
  std::cauchy_distribution<double> dist(location, scale);
  return dist(rng_);
}

double RNG::exponential(double lambda) {
  std::exponential_distribution<double> dist(lambda);
  return dist(rng_);
}

int32_t RNG::poisson(double mean) {
  std::poisson_distribution<int32_t> dist(mean);
  return dist(rng_);
}

double RNG::chi_squared(double df) {
  std::chi_squared_distribution<double> dist(df);
  return dist(rng_);
}

double RNG::student_t(double df) {
  std::student_t_distribution<double> dist(df);
  return dist(rng_);
}

std::vector<double> RNG::uniform_vector(size_t n, double min, double max) {
  std::vector<double> v(n);
  std::uniform_real_distribution<double> dist(min, max);
  for (auto& x : v) x = dist(rng_);
  return v;
}

std::vector<double> RNG::normal_vector(size_t n, double mean, double stddev) {
  std::vector<double> v(n);
  std::normal_distribution<double> dist(mean, stddev);
  for (auto& x : v) x = dist(rng_);
  return v;
}

std::vector<std::vector<double>> RNG::normal_correlated(
    size_t n, const std::vector<double>& means,
    const std::vector<std::vector<double>>& covar) {
  size_t d = means.size();
  // Cholesky decomposition
  std::vector<std::vector<double>> L(d, std::vector<double>(d, 0.0));
  for (size_t i = 0; i < d; ++i) {
    for (size_t j = 0; j <= i; ++j) {
      double sum = 0.0;
      for (size_t k = 0; k < j; ++k) sum += L[i][k] * L[j][k];
      if (i == j) L[i][j] = std::sqrt(std::max(0.0, covar[i][i] - sum));
      else L[i][j] = (covar[i][j] - sum) / L[j][j];
    }
  }

  std::vector<std::vector<double>> result(n, std::vector<double>(d));
  for (size_t i = 0; i < n; ++i) {
    auto z = normal_vector(d, 0.0, 1.0);
    for (size_t j = 0; j < d; ++j) {
      result[i][j] = means[j];
      for (size_t k = 0; k <= j; ++k) result[i][j] += L[j][k] * z[k];
    }
  }
  return result;
}

} // namespace quant
