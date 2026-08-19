#pragma once
#include <vector>
#include <utility>
#include <cstdint>

namespace cpp_quant {

class Statistics {
public:
    // 1. Дундаж
    static double mean(const std::vector<double>& data);
    
    // 2. Стандарт хазайлт (популяци)
    static double stddev(const std::vector<double>& data);
    
    // 3. Пирсоны корреляци
    static double correlation(const std::vector<double>& x, const std::vector<double>& y);
    
    // 4. Квантиль (жишээ нь: 0.95)
    static double quantile(const std::vector<double>& data, double q);
    
    // 5. Bootstrap итгэх интервал (95% CI)
    //    statistic_func: "mean", "std", эсвэл "winrate" гэх мэт
    static std::pair<double, double> bootstrap_ci(
        const std::vector<double>& data, 
        int num_iterations = 1000,
        double ci = 0.95
    );
    
    // 6. Туслах функц: winrate-ийн bootstrap (binary outcomes)
    static std::pair<double, double> bootstrap_winrate_ci(
        const std::vector<double>& pnls, 
        int num_iterations = 1000,
        double ci = 0.95
    );
};

} // namespace cpp_quant
