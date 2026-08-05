#include <gtest/gtest.h>
#include <cmath>
#include <vector>

#include "quant/statistics/rolling.h"
#include "quant/core/result.h"

using namespace quant;

namespace {

// std::vector<double> helper with a tiny tolerance.
void expect_series(const std::vector<double>& actual,
                   const std::vector<double>& expected, double tol = 1e-9) {
  ASSERT_EQ(actual.size(), expected.size());
  for (size_t i = 0; i < actual.size(); ++i) {
    EXPECT_NEAR(actual[i], expected[i], tol) << "index " << i;
  }
}

}  // namespace

TEST(RollingMean, SingleWindowEqualsFullMean) {
  std::vector<double> data = {1.0, 2.0, 3.0, 4.0, 5.0};
  auto res = RollingWindow::mean(data, data.size());
  ASSERT_TRUE(res.is_ok());
  ASSERT_EQ(res.value().size(), 1u);
  EXPECT_NEAR(res.value()[0], 3.0, 1e-12);
}

TEST(RollingMean, KnownSeries) {
  std::vector<double> data = {1.0, 2.0, 3.0, 4.0, 5.0};
  auto res = RollingWindow::mean(data, 3);
  ASSERT_TRUE(res.is_ok());
  // Window 3 means: (1+2+3)/3=2, (2+3+4)/3=3, (3+4+5)/3=4
  std::vector<double> expected = {2.0, 3.0, 4.0};
  expect_series(res.value(), expected);
}

TEST(RollingMean, Deterministic) {
  std::vector<double> data = {0.01, -0.02, 0.03, -0.01, 0.02, 0.015};
  auto a = RollingWindow::mean(data, 3);
  auto b = RollingWindow::mean(data, 3);
  ASSERT_TRUE(a.is_ok() && b.is_ok());
  expect_series(a.value(), b.value(), 1e-15);
}

TEST(RollingMean, InsufficientData) {
  std::vector<double> data = {1.0, 2.0};
  auto res = RollingWindow::mean(data, 5);
  ASSERT_TRUE(res.is_err());
  EXPECT_EQ(res.error().code(), ErrorCode::InsufficientData);
}

TEST(RollingMean, ZeroWindowRejected) {
  std::vector<double> data = {1.0, 2.0, 3.0};
  auto res = RollingWindow::mean(data, 0);
  ASSERT_TRUE(res.is_err());
  EXPECT_EQ(res.error().code(), ErrorCode::InvalidArgument);
}

TEST(RollingVolatility, MatchesReference) {
  std::vector<double> data = {0.01, -0.02, 0.03, -0.01, 0.02, 0.015, -0.005, 0.007};
  auto fast = RollingWindow::volatility(data, 4);
  auto ref = RollingWindow::volatility_reference(data, 4);
  ASSERT_TRUE(fast.is_ok() && ref.is_ok());
  expect_series(fast.value(), ref.value(), 1e-9);
}

TEST(RollingVolatility, MatchesReferencePopulation) {
  std::vector<double> data = {0.01, -0.02, 0.03, -0.01, 0.02, 0.015, -0.005, 0.007};
  auto fast = RollingWindow::volatility(data, 4, 0);
  auto ref = RollingWindow::volatility_reference(data, 4, 0);
  ASSERT_TRUE(fast.is_ok() && ref.is_ok());
  expect_series(fast.value(), ref.value(), 1e-9);
}

TEST(RollingVolatility, KnownConstantInputZeroVol) {
  std::vector<double> data(10, 0.01);
  auto res = RollingWindow::volatility(data, 3);
  ASSERT_TRUE(res.is_ok());
  for (double v : res.value()) {
    EXPECT_NEAR(v, 0.0, 1e-12);
  }
}

TEST(RollingVolatility, Deterministic) {
  std::vector<double> data = {0.01, -0.02, 0.03, -0.01, 0.02, 0.015};
  auto a = RollingWindow::volatility(data, 3);
  auto b = RollingWindow::volatility(data, 3);
  ASSERT_TRUE(a.is_ok() && b.is_ok());
  expect_series(a.value(), b.value(), 1e-15);
}

TEST(RollingVolatility, InsufficientData) {
  std::vector<double> data = {1.0, 2.0};
  auto res = RollingWindow::volatility(data, 5);
  ASSERT_TRUE(res.is_err());
  EXPECT_EQ(res.error().code(), ErrorCode::InsufficientData);
}

TEST(RollingVolatility, InvalidDdof) {
  std::vector<double> data = {1.0, 2.0, 3.0, 4.0};
  auto res = RollingWindow::volatility(data, 3, 3);
  ASSERT_TRUE(res.is_err());
  EXPECT_EQ(res.error().code(), ErrorCode::InvalidArgument);
}

TEST(RollingVolatility, FullWindowLength) {
  std::vector<double> data = {0.01, -0.02, 0.03, -0.01, 0.02};
  auto res = RollingWindow::volatility(data, data.size());
  ASSERT_TRUE(res.is_ok());
  ASSERT_EQ(res.value().size(), 1u);
  EXPECT_TRUE(std::isfinite(res.value()[0]));
}

TEST(RollingVolatility, ReferenceMatchesNaive) {
  // Validate the reference against a hand-rolled naive per-window std.
  std::vector<double> data = {0.02, -0.01, 0.03, 0.005, -0.02, 0.01};
  size_t window = 3;
  auto ref = RollingWindow::volatility_reference(data, window);
  ASSERT_TRUE(ref.is_ok());

  std::vector<double> expected;
  for (size_t i = 0; i + window <= data.size(); ++i) {
    double m = 0.0;
    for (size_t j = i; j < i + window; ++j) m += data[j];
    m /= static_cast<double>(window);
    double acc = 0.0;
    for (size_t j = i; j < i + window; ++j) acc += (data[j] - m) * (data[j] - m);
    expected.push_back(std::sqrt(acc / static_cast<double>(window - 1)));
  }
  expect_series(ref.value(), expected, 1e-12);
}
