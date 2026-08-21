#include "quant/simulation/paths.h"
#include <cmath>

namespace quant {

PathGenerator::PathGenerator(RNG& rng) : rng_(rng) {}

std::vector<double> PathGenerator::make_time_grid(double time_horizon, size_t num_steps) {
  std::vector<double> grid(num_steps + 1);
  double dt = time_horizon / static_cast<double>(num_steps);
  for (size_t i = 0; i <= num_steps; ++i) grid[i] = static_cast<double>(i) * dt;
  return grid;
}

PathResult PathGenerator::generate(size_t num_paths, size_t num_steps,
                                    double time_horizon, const PathConfig& config) {
  PathResult result;
  result.config = config;
  result.dt = time_horizon / static_cast<double>(num_steps);
  result.time_grid = make_time_grid(time_horizon, num_steps);
  result.paths.resize(num_paths, std::vector<double>(num_steps + 1, config.spot));

  switch (config.type) {
    case DiffusionType::GeometricBrownianMotion: fill_gbm(result, result.dt); break;
    case DiffusionType::OrnsteinUhlenbeck: fill_ou(result, result.dt); break;
    case DiffusionType::JumpDiffusion: fill_jump_diffusion(result, result.dt); break;
    case DiffusionType::Heston: fill_heston(result, result.dt); break;
  }
  return result;
}

void PathGenerator::fill_gbm(PathResult& result, double dt) {
  double sqrt_dt = std::sqrt(dt);
  double mu = result.config.drift;
  double sigma = result.config.volatility;
  for (auto& path : result.paths) {
    double s = path[0];
    for (size_t i = 1; i < path.size(); ++i) {
      double z = rng_.normal(0.0, 1.0);
      s *= std::exp((mu - 0.5 * sigma * sigma) * dt + sigma * sqrt_dt * z);
      path[i] = s;
    }
  }
}

void PathGenerator::fill_ou(PathResult& result, double dt) {
  double theta = result.config.mean_reversion_rate;
  double mu = result.config.mean_reversion_level;
  double sigma = result.config.volatility;
  double e_theta_dt = std::exp(-theta * dt);
  double ou_sigma = sigma * std::sqrt((1.0 - std::exp(-2.0 * theta * dt)) / (2.0 * theta));
  for (auto& path : result.paths) {
    double x = path[0];
    for (size_t i = 1; i < path.size(); ++i) {
      double z = rng_.normal(0.0, 1.0);
      x = mu + (x - mu) * e_theta_dt + ou_sigma * z;
      path[i] = x;
    }
  }
}

void PathGenerator::fill_jump_diffusion(PathResult& result, double dt) {
  double sqrt_dt = std::sqrt(dt);
  double mu = result.config.drift;
  double sigma = result.config.volatility;
  double lambda = result.config.jump_intensity;
  double jump_mu = result.config.jump_mean;
  double jump_sigma = result.config.jump_std;
  double jump_prob = lambda * dt;
  for (auto& path : result.paths) {
    double s = path[0];
    for (size_t i = 1; i < path.size(); ++i) {
      double z = rng_.normal(0.0, 1.0);
      double jump = 0.0;
      if (rng_.uniform() < jump_prob) {
        jump = rng_.normal(jump_mu, jump_sigma);
      }
      s *= std::exp((mu - 0.5 * sigma * sigma) * dt + sigma * sqrt_dt * z + jump);
      path[i] = s;
    }
  }
}

void PathGenerator::fill_heston(PathResult& result, double dt) {
  double sqrt_dt = std::sqrt(dt);
  double mu = result.config.drift;
  double kappa = result.config.heston_kappa;
  double theta = result.config.heston_theta;
  double xi = result.config.heston_xi;
  double rho = result.config.heston_rho;
  for (auto& path : result.paths) {
    double s = path[0];
    double v = result.config.heston_v0;
    for (size_t i = 1; i < path.size(); ++i) {
      double z1 = rng_.normal(0.0, 1.0);
      double z2 = rho * z1 + std::sqrt(1.0 - rho * rho) * rng_.normal(0.0, 1.0);
      v = std::max(0.0, v + kappa * (theta - v) * dt + xi * std::sqrt(std::max(0.0, v)) * sqrt_dt * z2);
      double sqrt_v = std::sqrt(v);
      s *= std::exp((mu - 0.5 * v) * dt + sqrt_v * sqrt_dt * z1);
      path[i] = s;
    }
  }
}

} // namespace quant
