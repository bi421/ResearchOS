#ifndef QUANT_SIMULATION_RNG_H
#define QUANT_SIMULATION_RNG_H

#include <random>
#include <vector>
#include <cstdint>

namespace quant {

class RNG {
public:
  explicit RNG(uint64_t seed = std::random_device{}());

  double uniform(double min = 0.0, double max = 1.0);
  double normal(double mean = 0.0, double stddev = 1.0);
  double cauchy(double location = 0.0, double scale = 1.0);
  double exponential(double lambda = 1.0);
  int32_t poisson(double mean);
  double chi_squared(double df);
  double student_t(double df);

  std::vector<double> uniform_vector(size_t n, double min = 0.0, double max = 1.0);
  std::vector<double> normal_vector(size_t n, double mean = 0.0, double stddev = 1.0);
  std::vector<std::vector<double>> normal_correlated(size_t n, const std::vector<double>& means,
                                                       const std::vector<std::vector<double>>& covar);

  void seed(uint64_t s) { rng_.seed(s); }
  uint64_t current_seed() const { return seed_; }

private:
  uint64_t seed_;
  std::mt19937_64 rng_;
};

} // namespace quant
#endif
