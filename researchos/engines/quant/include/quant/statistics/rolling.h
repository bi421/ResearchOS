#ifndef QUANT_STATISTICS_ROLLING_H
#define QUANT_STATISTICS_ROLLING_H

#include "quant/core/result.h"
#include <vector>
#include <cmath>
#include <numeric>

namespace quant {

/**
 * Rolling window statistics.
 *
 * Provides O(n) incremental rolling statistics plus an O(n*w) reference
 * implementation that preserves the exact per-window formula for numerical
 * comparison and backward compatibility.
 *
 * Determinism: pure functions of their inputs; no randomness, no wall-clock
 * dependence. Every output series has length ``data.size() - window + 1``.
 */
struct RollingWindow {
  /**
   * Rolling arithmetic mean over a sliding window.  O(n).
   *
   * @param data   Input series (oldest → newest).
   * @param window Sliding window size (must be > 0 and <= data.size()).
   * @return Series of length ``n - window + 1``.
   */
  static Result<std::vector<double>> mean(const std::vector<double>& data,
                                           size_t window);

  /**
   * Rolling volatility (standard deviation) over a sliding window.  O(n).
   *
   * Uses an incremental running-sum / running-sum-of-squares formulation with
   * the requested delta degrees of freedom (default ddof=1 → sample std).
   *
   * @param data   Input series (e.g. periodic returns).
   * @param window Sliding window size.
   * @param ddof   Delta degrees of freedom (must be < window).
   * @return Series of length ``n - window + 1``.
   */
static Result<std::vector<double>> volatility(const std::vector<double>& data,
                                                 size_t window,
                                                 int ddof = 1);

  /**
   * Rolling variance over a sliding window.  O(n).
   *
   * Uses the same incremental one-pass running-sum / running-sum-of-squares
   * formulation as ``volatility``, returning the variance (the square of the
   * standard deviation) with the requested delta degrees of freedom
   * (default ddof=1 → sample variance).
   *
   * @param data   Input series.
   * @param window Sliding window size.
   * @param ddof   Delta degrees of freedom (must be < window).
   * @return Series of length ``n - window + 1``.
   */
  static Result<std::vector<double>> variance(const std::vector<double>& data,
                                               size_t window,
                                               int ddof = 1);

  /**
   * Rolling volatility reference implementation.  O(n*w).
   *
   * Computes the exact per-window standard deviation (mean first, then sum of
   * squared deviations) — the same formula the deprecated
   * ``quant_engine::market_data::rolling_volatility_series`` uses. Retained
   * for numerical comparison and backward compatibility.
   *
   * @param data   Input series.
   * @param window Sliding window size.
   * @param ddof   Delta degrees of freedom (must be < window).
   * @return Series of length ``n - window + 1``.
   */
  static Result<std::vector<double>> volatility_reference(
      const std::vector<double>& data, size_t window, int ddof = 1);
};

}  // namespace quant
#endif  // QUANT_STATISTICS_ROLLING_H
