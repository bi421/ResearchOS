#ifndef QUANT_SIMULATION_MONTE_CARLO_H
#define QUANT_SIMULATION_MONTE_CARLO_H

#include "paths.h"
#include "quant/core/result.h"
#include "quant/statistics/descriptive.h"
#include <vector>
#include <functional>
#include <cstdint>
#include <future>

namespace quant {

struct MonteCarloResult {
  std::vector<double> final_values;
  DescriptiveStats stats_on_final;
  std::vector<double> expected_path;
  std::vector<double> upper_ci;
  std::vector<double> lower_ci;
  size_t num_paths{0};
  size_t num_steps{0};
  double confidence_level{0.95};

  Result<double> probability_of_exceeding(double threshold) const;
  Result<double> expected_shortfall(double threshold) const;
};

class MonteCarloEngine {
public:
  using PayoffFn = std::function<double(const std::vector<double>& path)>;

  explicit MonteCarloEngine(RNG& rng);

  MonteCarloResult simulate(size_t num_paths, size_t num_steps, double time_horizon,
                             const PathConfig& path_config,
                             PayoffFn payoff = nullptr);

  MonteCarloResult simulate_parallel(size_t num_paths, size_t num_steps, double time_horizon,
                                      const PathConfig& path_config,
                                      size_t num_threads = 0);

  void set_confidence_level(double level) { confidence_level_ = level; }
  double confidence_level() const { return confidence_level_; }

private:
  RNG& rng_;
  double confidence_level_{0.95};

  MonteCarloResult build_result(const std::vector<std::vector<double>>& all_paths,
                                 const PathConfig& path_config,
                                 const std::vector<double>& time_grid,
                                 double dt) const;
};

} // namespace quant
#endif
