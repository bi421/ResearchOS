#include "statistics.h"
#include <cmath>
#include <algorithm>
#include <random>
#include <numeric>
#include <stdexcept>

namespace cpp_quant {

double Statistics::mean(const std::vector<double>& data) {
    if (data.empty()) return 0.0;
    double sum = std::accumulate(data.begin(), data.end(), 0.0);
    return sum / data.size();
}

double Statistics::stddev(const std::vector<double>& data) {
    if (data.size() < 2) return 0.0;
    double m = mean(data);
    double sum = 0.0;
    for (double v : data) {
        sum += (v - m) * (v - m);
    }
    return std::sqrt(sum / data.size()); // Популяцийн стандарт хазайлт
}

double Statistics::correlation(const std::vector<double>& x, const std::vector<double>& y) {
    if (x.size() != y.size() || x.size() < 2) return 0.0;
    double mean_x = mean(x);
    double mean_y = mean(y);
    double num = 0.0, den_x = 0.0, den_y = 0.0;
    for (size_t i = 0; i < x.size(); ++i) {
        double dx = x[i] - mean_x;
        double dy = y[i] - mean_y;
        num += dx * dy;
        den_x += dx * dx;
        den_y += dy * dy;
    }
    if (den_x == 0.0 || den_y == 0.0) return 0.0;
    return num / std::sqrt(den_x * den_y);
}

double Statistics::quantile(const std::vector<double>& data, double q) {
    if (data.empty()) return 0.0;
    if (q < 0.0 || q > 1.0) q = 0.5;
    std::vector<double> sorted = data;
    std::sort(sorted.begin(), sorted.end());
    size_t idx = static_cast<size_t>(q * (sorted.size() - 1));
    return sorted[idx];
}

std::pair<double, double> Statistics::bootstrap_ci(
    const std::vector<double>& data, 
    int num_iterations, 
    double ci
) {
    if (data.size() < 2) return {0.0, 0.0};
    
    std::random_device rd;
    std::mt19937_64 gen(rd());
    std::uniform_int_distribution<size_t> dist(0, data.size() - 1);
    
    std::vector<double> means;
    means.reserve(num_iterations);
    
    for (int iter = 0; iter < num_iterations; ++iter) {
        double sum = 0.0;
        for (size_t i = 0; i < data.size(); ++i) {
            sum += data[dist(gen)];
        }
        means.push_back(sum / data.size());
    }
    std::sort(means.begin(), means.end());
    
    double lower = means[static_cast<size_t>((1.0 - ci) / 2.0 * num_iterations)];
    double upper = means[static_cast<size_t>((1.0 + ci) / 2.0 * num_iterations)];
    return {lower, upper};
}

std::pair<double, double> Statistics::bootstrap_winrate_ci(
    const std::vector<double>& pnls, 
    int num_iterations, 
    double ci
) {
    if (pnls.empty()) return {0.0, 0.0};
    
    // Winrate тооцоолох: pnl > 0 байвал win
    std::vector<double> outcomes;
    outcomes.reserve(pnls.size());
    for (double p : pnls) {
        outcomes.push_back((p > 0) ? 1.0 : 0.0);
    }
    return bootstrap_ci(outcomes, num_iterations, ci);
}

} // namespace cpp_quant
