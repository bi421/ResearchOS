#ifndef QUANT_RESEARCH_PARAMETER_SPACE_H
#define QUANT_RESEARCH_PARAMETER_SPACE_H

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace quant {
namespace research {

// A concrete assignment of one value to every parameter of a strategy. Values
// are stored as doubles (integer parameters are represented exactly, e.g.
// `atr_period = 14.0`) and read back with `get_int()`.
class ParamSet {
public:
  ParamSet() = default;

  // Sets (or overwrites) the value for `name`.
  void set(const std::string& name, double value);

  bool has(const std::string& name) const;
  double get(const std::string& name, double fallback = 0.0) const;
  // Returns the value rounded to the nearest integer (suitable for integer
  // parameters such as SMA periods).
  int64_t get_int(const std::string& name, int64_t fallback = 0) const;

  const std::vector<std::string>& names() const { return names_; }
  const std::vector<double>& values() const { return values_; }
  size_t size() const { return names_.size(); }

  bool operator==(const ParamSet& other) const;
  bool operator!=(const ParamSet& other) const { return !(*this == other); }

  // Human-readable canonical form: "fast=5 slow=20 stop=2".
  std::string to_string() const;

private:
  size_t find(const std::string& name) const;
  std::vector<std::string> names_;
  std::vector<double> values_;
};

// A named parameter space for optimization. Each parameter contributes a
// discrete set of candidate values; the full grid is the cartesian product.
// Combination indices decode deterministically (first parameter varies
// fastest) via `combo(index)`, so grid search and seeded random search are
// reproducible for identical inputs.
class ParameterSpace {
public:
  // Adds a parameter with an explicit candidate-value list (kept in order).
  void add_grid(const std::string& name, std::vector<double> values);

  // Adds an arithmetic range min, min+step, ... while <= max.
  // `log_scale == true` interprets `step` as a multiplicative factor and emits
  // a geometric progression min, min*step, min*step^2, ... (step must be > 1).
  void add_range(const std::string& name, double min, double max, double step,
                 bool log_scale = false);

  // Adds an integer range with an integer step.
  void add_int_range(const std::string& name, int64_t min, int64_t max,
                     int64_t step = 1);

  size_t parameter_count() const { return names_.size(); }
  bool empty() const { return names_.empty(); }

  // Total number of parameter combinations (cartesian product). Capped at
  // SIZE_MAX on overflow.
  size_t combo_count() const;

  const std::vector<std::string>& names() const { return names_; }
  size_t index_of(const std::string& name) const;
  bool contains(const std::string& name) const;

  // Candidate values for parameter at `param_index` (0 .. parameter_count-1).
  size_t value_count(size_t param_index) const;
  const std::vector<double>& values(size_t param_index) const;

  // Deterministically decodes `index` (0 .. combo_count-1) into a ParamSet.
  // Out-of-range indices return an empty ParamSet.
  ParamSet combo(size_t index) const;

  bool operator==(const ParameterSpace& other) const;
  bool operator!=(const ParameterSpace& other) const { return !(*this == other); }

private:
  size_t find(const std::string& name) const;
  std::vector<std::string> names_;
  std::vector<std::vector<double>> grids_;
};

} // namespace research
} // namespace quant
#endif
