#ifndef QUANT_SIMULATION_PATHS_H
#define QUANT_SIMULATION_PATHS_H

#include "rng.h"
#include <vector>
#include <cstdint>
#include <cmath>

namespace quant {

enum class DiffusionType {
  GeometricBrownianMotion,
  OrnsteinUhlenbeck,
  JumpDiffusion,
  Heston,
};

struct PathConfig {
  DiffusionType type{DiffusionType::GeometricBrownianMotion};
  double spot{100.0};
  double drift{0.05};
  double volatility{0.2};
  double mean_reversion_rate{1.0};
  double mean_reversion_level{100.0};
  double jump_intensity{0.1};
  double jump_mean{-0.02};
  double jump_std{0.03};
  double heston_v0{0.04};
  double heston_kappa{2.0};
  double heston_theta{0.04};
  double heston_xi{0.3};
  double heston_rho{-0.7};
};

struct PathResult {
  std::vector<std::vector<double>> paths;
  std::vector<double> time_grid;
  PathConfig config;
  double dt{0.0};
};

class PathGenerator {
public:
  explicit PathGenerator(RNG& rng);

  PathResult generate(size_t num_paths, size_t num_steps, double time_horizon,
                       const PathConfig& config);

  static std::vector<double> make_time_grid(double time_horizon, size_t num_steps);

private:
  RNG& rng_;

  void fill_gbm(PathResult& result, double dt);
  void fill_ou(PathResult& result, double dt);
  void fill_jump_diffusion(PathResult& result, double dt);
  void fill_heston(PathResult& result, double dt);
};

} // namespace quant
#endif
