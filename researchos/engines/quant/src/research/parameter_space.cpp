#include "quant/research/parameter_space.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <limits>

namespace quant {
namespace research {

namespace {

constexpr double kRangeEps = 1e-9;

} // namespace

// ── ParamSet ────────────────────────────────────────────────────────────────

size_t ParamSet::find(const std::string& name) const {
  for (size_t i = 0; i < names_.size(); ++i) {
    if (names_[i] == name) return i;
  }
  return names_.size();
}

void ParamSet::set(const std::string& name, double value) {
  const size_t i = find(name);
  if (i < names_.size()) {
    values_[i] = value;
  } else {
    names_.push_back(name);
    values_.push_back(value);
  }
}

bool ParamSet::has(const std::string& name) const { return find(name) < names_.size(); }

double ParamSet::get(const std::string& name, double fallback) const {
  const size_t i = find(name);
  return i < names_.size() ? values_[i] : fallback;
}

int64_t ParamSet::get_int(const std::string& name, int64_t fallback) const {
  const size_t i = find(name);
  return i < names_.size() ? static_cast<int64_t>(std::llround(values_[i]))
                           : fallback;
}

bool ParamSet::operator==(const ParamSet& other) const {
  if (names_.size() != other.names_.size()) return false;
  for (size_t i = 0; i < names_.size(); ++i) {
    if (names_[i] != other.names_[i]) return false;
    if (values_[i] != other.values_[i]) return false;
  }
  return true;
}

std::string ParamSet::to_string() const {
  std::string out;
  for (size_t i = 0; i < names_.size(); ++i) {
    if (i) out += " ";
    out += names_[i];
    out += "=";
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%.6g", values_[i]);
    out += buf;
  }
  return out;
}

// ── ParameterSpace ──────────────────────────────────────────────────────────

size_t ParameterSpace::find(const std::string& name) const {
  for (size_t i = 0; i < names_.size(); ++i) {
    if (names_[i] == name) return i;
  }
  return names_.size();
}

void ParameterSpace::add_grid(const std::string& name, std::vector<double> values) {
  names_.push_back(name);
  grids_.push_back(std::move(values));
}

void ParameterSpace::add_range(const std::string& name, double min, double max,
                               double step, bool log_scale) {
  std::vector<double> out;
  if (step <= 0.0 || max < min) {
    names_.push_back(name);
    grids_.push_back(std::move(out));
    return;
  }
  if (log_scale) {
    if (step <= 1.0) {
      names_.push_back(name);
      grids_.push_back(std::move(out));
      return;
    }
    const double tol = kRangeEps * std::max(1.0, std::abs(max));
    for (double v = min; v <= max + tol; v *= step) out.push_back(v);
  } else {
    const double tol = kRangeEps * std::max(1.0, std::abs(max));
    for (double v = min; v <= max + tol; v += step) out.push_back(v);
  }
  names_.push_back(name);
  grids_.push_back(std::move(out));
}

void ParameterSpace::add_int_range(const std::string& name, int64_t min,
                                   int64_t max, int64_t step) {
  std::vector<double> out;
  if (step <= 0 || max < min) {
    names_.push_back(name);
    grids_.push_back(std::move(out));
    return;
  }
  for (int64_t v = min; v <= max; v += step) {
    out.push_back(static_cast<double>(v));
    if (v > max - step) break; // avoid int64 overflow on the last step
  }
  names_.push_back(name);
  grids_.push_back(std::move(out));
}

size_t ParameterSpace::combo_count() const {
  size_t total = 1;
  for (const auto& g : grids_) {
    if (g.empty()) return 0;
    if (total > std::numeric_limits<size_t>::max() / g.size())
      return std::numeric_limits<size_t>::max();
    total *= g.size();
  }
  return total;
}

size_t ParameterSpace::index_of(const std::string& name) const {
  return find(name);
}

bool ParameterSpace::contains(const std::string& name) const {
  return find(name) < names_.size();
}

size_t ParameterSpace::value_count(size_t param_index) const {
  return param_index < grids_.size() ? grids_[param_index].size() : 0;
}

const std::vector<double>& ParameterSpace::values(size_t param_index) const {
  static const std::vector<double> kEmpty;
  return param_index < grids_.size() ? grids_[param_index] : kEmpty;
}

ParamSet ParameterSpace::combo(size_t index) const {
  if (index >= combo_count()) return {};
  ParamSet out;
  size_t rem = index;
  for (size_t i = 0; i < names_.size(); ++i) {
    const std::vector<double>& grid = grids_[i];
    if (grid.empty()) return {};
    const size_t digit = grid.size() > 1 ? rem % grid.size() : 0;
    rem = grid.size() > 1 ? rem / grid.size() : rem;
    out.set(names_[i], grid[digit]);
  }
  return out;
}

bool ParameterSpace::operator==(const ParameterSpace& other) const {
  if (names_.size() != other.names_.size()) return false;
  for (size_t i = 0; i < names_.size(); ++i) {
    if (names_[i] != other.names_[i]) return false;
    if (grids_[i] != other.grids_[i]) return false;
  }
  return true;
}

} // namespace research
} // namespace quant
