#include "quant/simulation/monte_carlo.h"
#include <algorithm>
#include <numeric>

#include <cmath>

namespace quant {

Result<double> MonteCarloResult::probability_of_exceeding(double threshold) const {
  if (final_values.empty()) return Error(ErrorCode::InsufficientData, "no paths");
  size_t count = std::count_if(final_values.begin(), final_values.end(),
                                [threshold](double v) { return v > threshold; });
  return static_cast<double>(count) / static_cast<double>(final_values.size());
}

Result<double> MonteCarloResult::expected_shortfall(double threshold) const {
  if (final_values.empty()) return Error(ErrorCode::InsufficientData, "no paths");
  double sum = 0.0;
  size_t count = 0;
  for (auto v : final_values) {
    if (v <= threshold) { sum += v; ++count; }
  }
  if (count == 0) return Error(ErrorCode::InsufficientData, "no values below threshold");
  return sum / static_cast<double>(count);
}

MonteCarloEngine::MonteCarloEngine(RNG& rng) : rng_(rng) {}

MonteCarloResult MonteCarloEngine::simulate(size_t num_paths, size_t num_steps,
                                             double time_horizon,
                                             const PathConfig& path_config,
                                             PayoffFn payoff) {
  PathGenerator gen(rng_);
  auto path_result = gen.generate(num_paths, num_steps, time_horizon, path_config);

  if (payoff) {
    std::vector<std::vector<double>> payoff_paths(num_paths);
    for (size_t i = 0; i < num_paths; ++i) {
      payoff_paths[i].resize(num_steps + 1);
      for (size_t j = 0; j <= num_steps; ++j) {
        payoff_paths[i][j] = payoff(path_result.paths[i]);
      }
    }
    path_result.paths = std::move(payoff_paths);
  }

  return build_result(path_result.paths, path_config, path_result.time_grid, path_result.dt);
}

static size_t detect_hardware_concurrency() {
  size_t n = std::thread::hardware_concurrency();
  return n > 0 ? n : 4;
}

MonteCarloResult MonteCarloEngine::simulate_parallel(
    size_t num_paths, size_t num_steps, double time_horizon,
    const PathConfig& path_config, size_t num_threads) {
  if (num_threads == 0) num_threads = detect_hardware_concurrency();

  size_t chunk_size = num_paths / num_threads;
  size_t remainder = num_paths % num_threads;

  std::vector<std::future<MonteCarloResult>> futures;
  size_t offset = 0;
  for (size_t t = 0; t < num_threads; ++t) {
    size_t this_chunk = chunk_size + (t < remainder ? 1 : 0);
    if (this_chunk == 0) continue;
    futures.push_back(std::async(std::launch::async, [this, this_chunk, num_steps,
                                                       time_horizon, path_config]() {
      RNG local_rng(std::random_device{}());
      MonteCarloEngine local_engine(local_rng);
      return local_engine.simulate(this_chunk, num_steps, time_horizon, path_config);
    }));
    offset += this_chunk;
  }

  MonteCarloResult combined;
  combined.num_paths = num_paths;
  combined.num_steps = num_steps;
  combined.confidence_level = confidence_level_;

  for (auto& f : futures) {
    auto partial = f.get();
    combined.final_values.insert(combined.final_values.end(),
                                  partial.final_values.begin(),
                                  partial.final_values.end());
  }

  auto final_stats = DescriptiveStats::compute(combined.final_values);
  if (final_stats.is_ok()) combined.stats_on_final = final_stats.value();

  return combined;
}

MonteCarloResult MonteCarloEngine::build_result(
    const std::vector<std::vector<double>>& all_paths,
    const PathConfig&,
    const std::vector<double>&,
    double) const {
  MonteCarloResult result;
  size_t num_paths = all_paths.size();
  size_t num_steps = all_paths.empty() ? 0 : all_paths[0].size() - 1;
  result.num_paths = num_paths;
  result.num_steps = num_steps;
  result.confidence_level = confidence_level_;

  result.final_values.reserve(num_paths);
  for (auto& path : all_paths)
    result.final_values.push_back(path.back());

  auto stats = DescriptiveStats::compute(result.final_values);
  if (stats.is_ok()) result.stats_on_final = stats.value();

  if (num_paths > 0) {
    result.expected_path.assign(num_steps + 1, 0.0);
    result.upper_ci.assign(num_steps + 1, 0.0);
    result.lower_ci.assign(num_steps + 1, 0.0);
    for (size_t j = 0; j <= num_steps; ++j) {
      double sum = 0.0;
      for (size_t i = 0; i < num_paths; ++i) sum += all_paths[i][j];
      result.expected_path[j] = sum / static_cast<double>(num_paths);
    }
    double z = 1.96;
    for (size_t j = 0; j <= num_steps; ++j) {
      double var = 0.0;
      for (size_t i = 0; i < num_paths; ++i) {
        double d = all_paths[i][j] - result.expected_path[j];
        var += d * d;
      }
      var /= static_cast<double>(num_paths);
      double se = std::sqrt(var / static_cast<double>(num_paths));
      result.upper_ci[j] = result.expected_path[j] + z * se;
      result.lower_ci[j] = result.expected_path[j] - z * se;
    }
  }

  return result;
}

} // namespace quant
