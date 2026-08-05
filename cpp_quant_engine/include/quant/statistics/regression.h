#ifndef QUANT_STATISTICS_REGRESSION_H
#define QUANT_STATISTICS_REGRESSION_H

#include "quant/core/result.h"
#include <vector>
#include <cmath>

namespace quant {
namespace statistics {

/**
 * Linear regression and trend statistics.
 *
 * Implements classical ordinary least-squares (OLS) routines over a
 * deterministic, single-precision-agnostic (double) pipeline. All functions
 * are pure functions of their inputs: no randomness, no wall-clock dependence.
 *
 * Two forms are provided:
 *   - Trend form: `slope(y)` / `intercept(y)` regress y against the implicit
 *     index x = 0, 1, ..., n-1 (a time-series trendline).
 *   - Pairwise form: `correlation(x, y)` / `r_squared(x, y)` /
 *     `standard_error(x, y)` operate on an explicit (x, y) sample.
 *
 * Mathematical definitions (classical least squares):
 *   slope       beta  = sum((x_i - xbar)(y_i - ybar)) / sum((x_i - xbar)^2)
 *   intercept   alpha = ybar - beta * xbar
 *   correlation Pearson coefficient
 *   r_squared          r^2
 *   std_error          sqrt( sum(e_i^2) / (n - 2) ),  e_i = residual
 *
 * Complexity: O(n) for every routine. No O(n^2) work.
 */
class Regression {
public:
  /**
   * Least-squares slope of y as a function of the implicit index
   * x = 0, 1, ..., n-1.  O(n).
   *
   * @param y Dependent series (must contain >= 2 finite observations).
   * @return The OLS slope coefficient.
   */
  static Result<double> slope(const std::vector<double>& y);

  /**
   * Least-squares intercept of y against the implicit index
   * x = 0, 1, ..., n-1.  O(n).
   *
   * @param y Dependent series (must contain >= 2 finite observations).
   * @return The OLS intercept coefficient.
   */
  static Result<double> intercept(const std::vector<double>& y);

  /**
   * Pearson correlation coefficient between x and y.  O(n).
   *
   * @param x Independent series.
   * @param y Dependent series (same length as x).
   * @return r in [-1, 1].
   */
  static Result<double> correlation(const std::vector<double>& x,
                                    const std::vector<double>& y);

  /**
   * Coefficient of determination R^2 = r^2 for the (x, y) fit.  O(n).
   *
   * @param x Independent series.
   * @param y Dependent series (same length as x).
   * @return R^2 in [0, 1].
   */
  static Result<double> r_squared(const std::vector<double>& x,
                                  const std::vector<double>& y);

  /**
   * Residual standard error of the (x, y) least-squares fit.  O(n).
   *
   *   se = sqrt( sum(e_i^2) / (n - 2) ),  e_i = y_i - (alpha + beta * x_i)
   *
   * @param x Independent series.
   * @param y Dependent series (same length as x).
   * @return Standard error (0 for a perfect fit).
   */
  static Result<double> standard_error(const std::vector<double>& x,
                                       const std::vector<double>& y);
};

}  // namespace statistics
}  // namespace quant
#endif  // QUANT_STATISTICS_REGRESSION_H
