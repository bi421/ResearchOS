#include <gtest/gtest.h>
#include "quant/simulation/rng.h"
#include "quant/simulation/paths.h"
#include "quant/simulation/monte_carlo.h"
#include <cmath>

using namespace quant;

TEST(RNGTest, UniformRange) {
  RNG rng(42);
  for (int i = 0; i < 100; ++i) {
    double v = rng.uniform(0.0, 1.0);
    EXPECT_GE(v, 0.0);
    EXPECT_LE(v, 1.0);
  }
}

TEST(RNGTest, UniformNegativeRange) {
  RNG rng(123);
  for (int i = 0; i < 100; ++i) {
    double v = rng.uniform(-5.0, 5.0);
    EXPECT_GE(v, -5.0);
    EXPECT_LE(v, 5.0);
  }
}

TEST(RNGTest, NormalMean) {
  RNG rng(42);
  double sum = 0.0;
  int n = 10000;
  for (int i = 0; i < n; ++i) sum += rng.normal(0.0, 1.0);
  double mean = sum / n;
  EXPECT_NEAR(0.0, mean, 0.1);
}

TEST(RNGTest, DeterministicSeed) {
  RNG rng1(42);
  RNG rng2(42);
  for (int i = 0; i < 10; ++i) {
    EXPECT_DOUBLE_EQ(rng1.uniform(), rng2.uniform());
  }
}

TEST(RNGTest, UniformVector) {
  RNG rng(42);
  auto v = rng.uniform_vector(100, 0.0, 1.0);
  EXPECT_EQ(100, v.size());
}

TEST(RNGTest, NormalVector) {
  RNG rng(42);
  auto v = rng.normal_vector(100, 0.0, 1.0);
  EXPECT_EQ(100, v.size());
}

TEST(RNGTest, ExponentialNonNegative) {
  RNG rng(42);
  for (int i = 0; i < 50; ++i) {
    EXPECT_GE(rng.exponential(1.0), 0.0);
  }
}

TEST(RNGTest, PoissonNonNegative) {
  RNG rng(42);
  for (int i = 0; i < 50; ++i) {
    EXPECT_GE(rng.poisson(5.0), 0);
  }
}

TEST(PathGeneratorTest, GBM) {
  RNG rng(42);
  PathGenerator gen(rng);
  PathConfig cfg;
  cfg.type = DiffusionType::GeometricBrownianMotion;
  cfg.spot = 100.0;
  cfg.drift = 0.05;
  cfg.volatility = 0.2;
  auto result = gen.generate(10, 100, 1.0, cfg);
  EXPECT_EQ(10, result.paths.size());
  EXPECT_EQ(101, result.paths[0].size());
  EXPECT_DOUBLE_EQ(100.0, result.paths[0][0]);
  EXPECT_EQ(101, result.time_grid.size());
  EXPECT_DOUBLE_EQ(0.01, result.dt);
}

TEST(PathGeneratorTest, GBMPositive) {
  RNG rng(42);
  PathGenerator gen(rng);
  PathConfig cfg;
  cfg.type = DiffusionType::GeometricBrownianMotion;
  cfg.spot = 100.0;
  auto result = gen.generate(5, 50, 1.0, cfg);
  for (const auto& path : result.paths) {
    for (auto v : path) EXPECT_GT(v, 0.0);
  }
}

TEST(PathGeneratorTest, OrnsteinUhlenbeck) {
  RNG rng(42);
  PathGenerator gen(rng);
  PathConfig cfg;
  cfg.type = DiffusionType::OrnsteinUhlenbeck;
  cfg.spot = 100.0;
  cfg.mean_reversion_level = 100.0;
  cfg.mean_reversion_rate = 1.0;
  cfg.volatility = 0.2;
  auto result = gen.generate(5, 50, 1.0, cfg);
  EXPECT_EQ(5, result.paths.size());
  EXPECT_EQ(51, result.paths[0].size());
}

TEST(PathGeneratorTest, JumpDiffusion) {
  RNG rng(42);
  PathGenerator gen(rng);
  PathConfig cfg;
  cfg.type = DiffusionType::JumpDiffusion;
  cfg.spot = 100.0;
  cfg.jump_intensity = 0.5;
  auto result = gen.generate(5, 50, 1.0, cfg);
  EXPECT_EQ(5, result.paths.size());
}

TEST(PathGeneratorTest, Heston) {
  RNG rng(42);
  PathGenerator gen(rng);
  PathConfig cfg;
  cfg.type = DiffusionType::Heston;
  cfg.spot = 100.0;
  cfg.drift = 0.05;
  cfg.heston_v0 = 0.04;
  cfg.heston_kappa = 2.0;
  cfg.heston_theta = 0.04;
  cfg.heston_xi = 0.3;
  cfg.heston_rho = -0.7;
  auto result = gen.generate(5, 50, 1.0, cfg);
  EXPECT_EQ(5, result.paths.size());
}

TEST(PathGeneratorTest, MakeTimeGrid) {
  auto grid = PathGenerator::make_time_grid(1.0, 10);
  EXPECT_EQ(11, grid.size());
  EXPECT_DOUBLE_EQ(0.0, grid[0]);
  EXPECT_DOUBLE_EQ(1.0, grid[10]);
  EXPECT_DOUBLE_EQ(0.5, grid[5]);
}

TEST(MonteCarloTest, SimulateBasic) {
  RNG rng(42);
  MonteCarloEngine engine(rng);
  PathConfig cfg;
  cfg.type = DiffusionType::GeometricBrownianMotion;
  cfg.spot = 100.0;
  cfg.drift = 0.05;
  cfg.volatility = 0.2;
  auto result = engine.simulate(100, 50, 1.0, cfg);
  EXPECT_EQ(100, result.num_paths);
  EXPECT_EQ(50, result.num_steps);
  EXPECT_EQ(100, result.final_values.size());
  EXPECT_GT(result.stats_on_final.count, 0);
}

TEST(MonteCarloTest, SimulateWithPayoff) {
  RNG rng(42);
  MonteCarloEngine engine(rng);
  PathConfig cfg;
  cfg.type = DiffusionType::GeometricBrownianMotion;
  cfg.spot = 100.0;
  auto payoff = [](const std::vector<double>& path) {
    return std::max(0.0, path.back() - 100.0);
  };
  auto result = engine.simulate(50, 25, 1.0, cfg, payoff);
  EXPECT_EQ(50, result.final_values.size());
}

TEST(MonteCarloTest, ConfidenceInterval) {
  RNG rng(42);
  MonteCarloEngine engine(rng);
  PathConfig cfg;
  cfg.type = DiffusionType::GeometricBrownianMotion;
  cfg.spot = 100.0;
  auto result = engine.simulate(200, 50, 1.0, cfg);
  EXPECT_EQ(result.expected_path.size(), result.upper_ci.size());
  EXPECT_EQ(result.expected_path.size(), result.lower_ci.size());
  for (size_t i = 0; i < result.expected_path.size(); ++i) {
    EXPECT_GE(result.upper_ci[i], result.lower_ci[i]);
  }
}

TEST(MonteCarloTest, ProbabilityOfExceeding) {
  RNG rng(42);
  MonteCarloEngine engine(rng);
  PathConfig cfg;
  cfg.type = DiffusionType::GeometricBrownianMotion;
  cfg.spot = 100.0;
  auto result = engine.simulate(200, 50, 1.0, cfg);
  auto p = result.probability_of_exceeding(90.0);
  ASSERT_TRUE(p.is_ok());
  EXPECT_GE(p.value(), 0.0);
  EXPECT_LE(p.value(), 1.0);
}

TEST(MonteCarloTest, SimulateParallel) {
  RNG rng(42);
  MonteCarloEngine engine(rng);
  PathConfig cfg;
  cfg.type = DiffusionType::GeometricBrownianMotion;
  cfg.spot = 100.0;
  auto result = engine.simulate_parallel(200, 50, 1.0, cfg, 4);
  EXPECT_EQ(200, result.final_values.size());
  EXPECT_GT(result.stats_on_final.count, 0);
}

TEST(MonteCarloTest, CustomConfidenceLevel) {
  RNG rng(42);
  MonteCarloEngine engine(rng);
  engine.set_confidence_level(0.99);
  EXPECT_DOUBLE_EQ(0.99, engine.confidence_level());
}
