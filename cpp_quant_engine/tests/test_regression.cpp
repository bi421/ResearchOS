#include <gtest/gtest.h>
#include <cmath>
#include <limits>
#include <vector>

#include "quant/statistics/regression.h"
#include "quant/core/result.h"

using namespace quant::statistics;
using quant::ErrorCode;

namespace {

constexpr double kEps = 1e-9;

// Linear generator: y = a + b*x + noise (noise == 0 for perfect fit).
std::vector<double> line(double a, double b, size_t n, double noise = 0.0,
                         unsigned seed = 42u) {
  std::vector<double> y(n);
  unsigned s = seed;
  for (size_t i = 0; i < n; ++i) {
    double x = static_cast<double>(i);
    double nz = 0.0;
    if (noise != 0.0) {
      // Deterministic LCG pseudo-random noise.
      s = s * 1664525u + 1013904223u;
      nz = noise * (static_cast<double>((s >> 8) & 0xFFFFu) / 65535.0 - 0.5);
    }
    y[i] = a + b * x + nz;
  }
  return y;
}

}  // namespace

// ── Perfect positive line (y = 2 + 3x) ─────────────────────────────────────
TEST(RegressionSlope, PerfectPositiveLine) {
  std::vector<double> y = {2.0, 5.0, 8.0, 11.0, 14.0};  // 2 + 3*(0..4)
  auto beta = Regression::slope(y);
  ASSERT_TRUE(beta.is_ok());
  EXPECT_NEAR(beta.value(), 3.0, kEps);
}

TEST(RegressionIntercept, PerfectPositiveLine) {
  std::vector<double> y = {2.0, 5.0, 8.0, 11.0, 14.0};
  auto alpha = Regression::intercept(y);
  ASSERT_TRUE(alpha.is_ok());
  EXPECT_NEAR(alpha.value(), 2.0, kEps);
}

// ── Perfect negative line (y = 10 - 2x) ────────────────────────────────────
TEST(RegressionSlope, PerfectNegativeLine) {
  std::vector<double> y = {10.0, 8.0, 6.0, 4.0, 2.0};  // 10 - 2*(0..4)
  auto beta = Regression::slope(y);
  ASSERT_TRUE(beta.is_ok());
  EXPECT_NEAR(beta.value(), -2.0, kEps);
}

TEST(RegressionIntercept, PerfectNegativeLine) {
  std::vector<double> y = {10.0, 8.0, 6.0, 4.0, 2.0};
  auto alpha = Regression::intercept(y);
  ASSERT_TRUE(alpha.is_ok());
  EXPECT_NEAR(alpha.value(), 10.0, kEps);
}

// ── Horizontal line (y = const) ────────────────────────────────────────────
TEST(RegressionSlope, HorizontalLineZeroSlope) {
  std::vector<double> y(8, 7.0);
  auto beta = Regression::slope(y);
  ASSERT_TRUE(beta.is_ok());
  EXPECT_NEAR(beta.value(), 0.0, kEps);
}

TEST(RegressionIntercept, HorizontalLine) {
  std::vector<double> y(8, 7.0);
  auto alpha = Regression::intercept(y);
  ASSERT_TRUE(alpha.is_ok());
  EXPECT_NEAR(alpha.value(), 7.0, kEps);
}

// ── Rejections ─────────────────────────────────────────────────────────────
TEST(RegressionSlope, EmptyRejected) {
  std::vector<double> y;
  auto beta = Regression::slope(y);
  ASSERT_TRUE(beta.is_err());
  EXPECT_EQ(beta.error().code(), ErrorCode::InsufficientData);
}

TEST(RegressionSlope, SingleObservationRejected) {
  std::vector<double> y = {3.0};
  auto beta = Regression::slope(y);
  ASSERT_TRUE(beta.is_err());
  EXPECT_EQ(beta.error().code(), ErrorCode::InsufficientData);
}

TEST(RegressionCorrelation, EmptyRejected) {
  std::vector<double> x, y;
  auto r = Regression::correlation(x, y);
  ASSERT_TRUE(r.is_err());
  EXPECT_EQ(r.error().code(), ErrorCode::InsufficientData);
}

TEST(RegressionCorrelation, SizeMismatchRejected) {
  std::vector<double> x = {1.0, 2.0, 3.0};
  std::vector<double> y = {1.0, 2.0};
  auto r = Regression::correlation(x, y);
  ASSERT_TRUE(r.is_err());
  EXPECT_EQ(r.error().code(), ErrorCode::InvalidArgument);
}

TEST(RegressionRSquared, SizeMismatchRejected) {
  std::vector<double> x = {1.0, 2.0};
  std::vector<double> y = {1.0, 2.0, 3.0};
  auto r2 = Regression::r_squared(x, y);
  ASSERT_TRUE(r2.is_err());
  EXPECT_EQ(r2.error().code(), ErrorCode::InvalidArgument);
}

TEST(RegressionStandardError, SizeMismatchRejected) {
  std::vector<double> x = {1.0, 2.0, 3.0, 4.0};
  std::vector<double> y = {1.0, 2.0};
  auto se = Regression::standard_error(x, y);
  ASSERT_TRUE(se.is_err());
  EXPECT_EQ(se.error().code(), ErrorCode::InvalidArgument);
}

TEST(RegressionCorrelation, ConstantXRejected) {
  std::vector<double> x = {5.0, 5.0, 5.0, 5.0};
  std::vector<double> y = {1.0, 2.0, 3.0, 4.0};
  auto r = Regression::correlation(x, y);
  ASSERT_TRUE(r.is_err());
  EXPECT_EQ(r.error().code(), ErrorCode::DivisionByZero);
}

TEST(RegressionStandardError, ConstantXRejected) {
  std::vector<double> x = {5.0, 5.0, 5.0, 5.0};
  std::vector<double> y = {1.0, 2.0, 3.0, 4.0};
  auto se = Regression::standard_error(x, y);
  ASSERT_TRUE(se.is_err());
  EXPECT_EQ(se.error().code(), ErrorCode::DivisionByZero);
}

// ── NaN / Inf rejection ────────────────────────────────────────────────────
TEST(RegressionSlope, NaNRejected) {
  std::vector<double> y = {1.0, 2.0, std::nan(""), 4.0};
  auto beta = Regression::slope(y);
  ASSERT_TRUE(beta.is_err());
  EXPECT_EQ(beta.error().code(), ErrorCode::DomainError);
}

TEST(RegressionIntercept, InfRejected) {
  std::vector<double> y = {1.0, 2.0, std::numeric_limits<double>::infinity(), 4.0};
  auto alpha = Regression::intercept(y);
  ASSERT_TRUE(alpha.is_err());
  EXPECT_EQ(alpha.error().code(), ErrorCode::DomainError);
}

TEST(RegressionCorrelation, NaNInYRejected) {
  std::vector<double> x = {1.0, 2.0, 3.0, 4.0};
  std::vector<double> y = {1.0, std::nan(""), 3.0, 4.0};
  auto r = Regression::correlation(x, y);
  ASSERT_TRUE(r.is_err());
  EXPECT_EQ(r.error().code(), ErrorCode::DomainError);
}

TEST(RegressionCorrelation, InfInXRejected) {
  std::vector<double> x = {1.0, std::numeric_limits<double>::infinity(), 3.0, 4.0};
  std::vector<double> y = {1.0, 2.0, 3.0, 4.0};
  auto r = Regression::correlation(x, y);
  ASSERT_TRUE(r.is_err());
  EXPECT_EQ(r.error().code(), ErrorCode::DomainError);
}

// ── Correlation perfect fits ──────────────────────────────────────────────
TEST(RegressionCorrelation, PerfectPositiveCorrelation) {
  std::vector<double> x = {1.0, 2.0, 3.0, 4.0, 5.0};
  std::vector<double> y = {2.0, 4.0, 6.0, 8.0, 10.0};
  auto r = Regression::correlation(x, y);
  ASSERT_TRUE(r.is_ok());
  EXPECT_NEAR(r.value(), 1.0, kEps);
}

TEST(RegressionCorrelation, PerfectNegativeCorrelation) {
  std::vector<double> x = {1.0, 2.0, 3.0, 4.0, 5.0};
  std::vector<double> y = {10.0, 8.0, 6.0, 4.0, 2.0};
  auto r = Regression::correlation(x, y);
  ASSERT_TRUE(r.is_ok());
  EXPECT_NEAR(r.value(), -1.0, kEps);
}

TEST(RegressionCorrelation, UncorrelatedZero) {
  std::vector<double> x = {1.0, 2.0, 3.0, 4.0, 5.0};
  std::vector<double> y = {1.0, -1.0, 1.0, -1.0, 1.0};
  auto r = Regression::correlation(x, y);
  ASSERT_TRUE(r.is_ok());
  EXPECT_NEAR(r.value(), 0.0, kEps);
}

// ── R^2 ────────────────────────────────────────────────────────────────────
TEST(RegressionRSquared, PerfectFitIsOne) {
  std::vector<double> x = {0.0, 1.0, 2.0, 3.0, 4.0};
  std::vector<double> y = line(1.0, 2.0, 5);
  auto r2 = Regression::r_squared(x, y);
  ASSERT_TRUE(r2.is_ok());
  EXPECT_NEAR(r2.value(), 1.0, kEps);
}

TEST(RegressionRSquared, PerfectFitNegativeSlopeIsOne) {
  std::vector<double> x = {0.0, 1.0, 2.0, 3.0, 4.0};
  std::vector<double> y = line(5.0, -1.0, 5);
  auto r2 = Regression::r_squared(x, y);
  ASSERT_TRUE(r2.is_ok());
  EXPECT_NEAR(r2.value(), 1.0, 1e-12);
}

// ── Standard error ─────────────────────────────────────────────────────────
TEST(RegressionStandardError, PerfectFitIsZero) {
  std::vector<double> x = {0.0, 1.0, 2.0, 3.0, 4.0};
  std::vector<double> y = line(2.0, 3.0, 5);
  auto se = Regression::standard_error(x, y);
  ASSERT_TRUE(se.is_ok());
  EXPECT_NEAR(se.value(), 0.0, 1e-9);
}

TEST(RegressionStandardError, PositiveForNoisyFit) {
  std::vector<double> x = {0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0};
  std::vector<double> y = line(1.0, 0.5, 8, 0.4);
  auto se = Regression::standard_error(x, y);
  ASSERT_TRUE(se.is_ok());
  EXPECT_GT(se.value(), 0.0);
  EXPECT_TRUE(std::isfinite(se.value()));
}

// ── Known textbook example ─────────────────────────────────────────────────
// x = {1,2,3,4,5}, y = {2,4,5,4,5}; textbook least-squares:
//   xbar=3, ybar=4, Sxx=10, Sxy=5, beta=0.5, alpha=2.5, r=0.5/sqrt(0.5*?).
// Compute explicitly: Sxy = sum((x-3)(y-4)) = (-2)(-2)+(-1)(0)+0(1)+1(0)+2(1)
//   = 4 + 0 + 0 + 0 + 2 = 6.  Syy = 4+0+1+0+1 = 6.  Sxx=4+1+0+1+4=10.
//   beta = 6/10 = 0.6, alpha = 4 - 0.6*3 = 2.2.
//   r = 6/sqrt(10*6) = 6/sqrt(60) = 0.774596669...
TEST(RegressionSlope, TextbookExample) {
  std::vector<double> x = {1.0, 2.0, 3.0, 4.0, 5.0};
  std::vector<double> y = {2.0, 4.0, 5.0, 4.0, 5.0};
  // slope over explicit index: use correlation-style via slope(y) where
  // y is the series; but slope(y) regresses against index 0..4 == x-1, so
  // the slope is identical (translation-invariant). beta = 0.6.
  auto beta = Regression::slope(y);
  ASSERT_TRUE(beta.is_ok());
  EXPECT_NEAR(beta.value(), 0.6, kEps);
}

TEST(RegressionIntercept, TextbookExample) {
  std::vector<double> y = {2.0, 4.0, 5.0, 4.0, 5.0};
  auto alpha = Regression::intercept(y);
  ASSERT_TRUE(alpha.is_ok());
  // xbar_index = 2.0, ybar = 4.0, beta = 0.6 -> alpha = 4 - 0.6*2 = 2.8.
  EXPECT_NEAR(alpha.value(), 2.8, kEps);
}

TEST(RegressionCorrelation, TextbookExample) {
  std::vector<double> x = {1.0, 2.0, 3.0, 4.0, 5.0};
  std::vector<double> y = {2.0, 4.0, 5.0, 4.0, 5.0};
  auto r = Regression::correlation(x, y);
  ASSERT_TRUE(r.is_ok());
  EXPECT_NEAR(r.value(), 6.0 / std::sqrt(60.0), kEps);
}

TEST(RegressionRSquared, TextbookExample) {
  std::vector<double> x = {1.0, 2.0, 3.0, 4.0, 5.0};
  std::vector<double> y = {2.0, 4.0, 5.0, 4.0, 5.0};
  auto r2 = Regression::r_squared(x, y);
  ASSERT_TRUE(r2.is_ok());
  EXPECT_NEAR(r2.value(), 36.0 / 60.0, kEps);
}

// ── Random (deterministic) regression ──────────────────────────────────────
TEST(RegressionRandom, SlopeMatchesSeededLinear) {
  std::vector<double> x = {0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0};
  std::vector<double> y = line(0.0, 1.7, 10, 0.2);
  auto beta = Regression::slope(y);
  ASSERT_TRUE(beta.is_ok());
  EXPECT_NEAR(beta.value(), 1.7, 0.15);
}

// ── Determinism ────────────────────────────────────────────────────────────
TEST(RegressionDeterminism, RepeatedCallsEqual) {
  std::vector<double> y = line(0.0, 1.7, 10, 0.2, 7u);
  auto a = Regression::slope(y);
  auto b = Regression::slope(y);
  ASSERT_TRUE(a.is_ok() && b.is_ok());
  EXPECT_EQ(a.value(), b.value());
}

TEST(RegressionDeterminism, CorrelationRepeatedEqual) {
  std::vector<double> x = {0.0, 1.0, 2.0, 3.0, 4.0, 5.0};
  std::vector<double> y = line(1.0, -0.5, 6, 0.1, 3u);
  auto a = Regression::correlation(x, y);
  auto b = Regression::correlation(x, y);
  ASSERT_TRUE(a.is_ok() && b.is_ok());
  EXPECT_EQ(a.value(), b.value());
}
