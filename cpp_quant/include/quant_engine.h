#pragma once
#include <vector>
#include <string>
#include <map>
#include "data_loader.h"
#include "indicators.h"
#include "backtest.h"
#include "statistics.h"
#include "monte_carlo.h"
#include "optimizer.h"

namespace cpp_quant {

class QuantEngine {
public:
    QuantEngine();
    ~QuantEngine();
    
    // 1. Өгөгдөл ачаалах
    bool loadData(const std::vector<std::string>& csv_files);
    bool loadDataFromVectors(
        const std::vector<int64_t>& timestamps,
        const std::vector<double>& opens,
        const std::vector<double>& highs,
        const std::vector<double>& lows,
        const std::vector<double>& closes,
        const std::vector<double>& volumes
    );
    void setTimeframe(int minutes); // 1, 5, 15, 30, 60
    
    // 2. Бэктест хийх
    BacktestResult runSMA(int short_period, int long_period);
    BacktestResult runRSI(int period, double oversold=30.0, double overbought=70.0);
    BacktestResult runMACD(int fast=12, int slow=26, int signal=9, int sma_filter=200);
    
    // 3. Олон стратегийг нэг дор ажиллуулах
    std::map<std::string, BacktestResult> runAllStrategies();
    
    // 4. Монте Карло
    double monteCarloPValue(const BacktestResult& result, int num_simulations = 10000);
    
    // 5. Оптимизаци
    std::map<std::string, double> optimizeSMA(int short_min=5, int short_max=30, int long_min=20, int long_max=100);
    
    // 6. Мэдээлэл авах
    size_t getDataSize() const { return data_.size(); }
    std::string getDataInfo() const;

private:
    std::vector<Candle> raw_data_;
    std::vector<Candle> data_;
    int timeframe_minutes_ = 1;
    bool data_loaded_ = false;
    
    void aggregateData();
};

} // namespace cpp_quant
