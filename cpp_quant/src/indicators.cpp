#include "indicators.h"
#include "data_loader.h"
#include <cmath>
#include <algorithm>

namespace cpp_quant {

std::vector<double> Indicators::SMA(const std::vector<double>& prices, int period) {
    std::vector<double> result(prices.size(), 0.0);
    if (prices.empty() || period <= 0) return result;
    
    double sum = 0.0;
    for (size_t i = 0; i < prices.size(); ++i) {
        sum += prices[i];
        if (i >= (size_t)period) sum -= prices[i - period];
        if (i >= (size_t)period - 1) {
            result[i] = sum / period;
        }
    }
    return result;
}

std::vector<double> Indicators::RSI(const std::vector<double>& prices, int period) {
    std::vector<double> result(prices.size(), 50.0);
    if (prices.size() < 2) return result;
    
    std::vector<double> gains(prices.size(), 0.0);
    std::vector<double> losses(prices.size(), 0.0);
    
    for (size_t i = 1; i < prices.size(); ++i) {
        double diff = prices[i] - prices[i-1];
        if (diff > 0) gains[i] = diff;
        else losses[i] = -diff;
    }
    
    double avg_gain = 0.0, avg_loss = 0.0;
    for (int i = 1; i <= period; ++i) {
        avg_gain += gains[i];
        avg_loss += losses[i];
    }
    avg_gain /= period;
    avg_loss /= period;
    
    for (size_t i = period + 1; i < prices.size(); ++i) {
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period;
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period;
        if (avg_loss == 0) result[i] = 100.0;
        else {
            double rs = avg_gain / avg_loss;
            result[i] = 100.0 - (100.0 / (1.0 + rs));
        }
    }
    return result;
}

Indicators::MACDResult Indicators::MACD(const std::vector<double>& prices, int fast, int slow, int signal) {
    MACDResult result;
    if (prices.empty()) return result;
    
    auto ema = [](const std::vector<double>& data, int period) {
        std::vector<double> res(data.size(), 0.0);
        if (data.empty()) return res;
        double k = 2.0 / (period + 1);
        res[0] = data[0];
        for (size_t i = 1; i < data.size(); ++i) {
            res[i] = data[i] * k + res[i-1] * (1 - k);
        }
        return res;
    };
    
    std::vector<double> ema_fast = ema(prices, fast);
    std::vector<double> ema_slow = ema(prices, slow);
    
    result.macd.resize(prices.size());
    for (size_t i = 0; i < prices.size(); ++i) {
        result.macd[i] = ema_fast[i] - ema_slow[i];
    }
    result.signal = ema(result.macd, signal);
    
    result.histogram.resize(prices.size());
    for (size_t i = 0; i < prices.size(); ++i) {
        result.histogram[i] = result.macd[i] - result.signal[i];
    }
    return result;
}

std::vector<double> Indicators::ATR(const std::vector<Candle>& candles, int period) {
    std::vector<double> result(candles.size(), 0.0);
    if (candles.size() < 2) return result;
    
    std::vector<double> tr(candles.size(), 0.0);
    for (size_t i = 1; i < candles.size(); ++i) {
        double hl = candles[i].high - candles[i].low;
        double hc = std::abs(candles[i].high - candles[i-1].close);
        double lc = std::abs(candles[i].low - candles[i-1].close);
        tr[i] = std::max({hl, hc, lc});
    }
    
    double sum = 0.0;
    for (int i = 1; i <= period && i < (int)candles.size(); ++i) sum += tr[i];
    for (size_t i = period; i < candles.size(); ++i) {
        if (i == (size_t)period) result[i] = sum / period;
        else result[i] = (result[i-1] * (period - 1) + tr[i]) / period;
    }
    return result;
}

Indicators::BBResult Indicators::BollingerBands(const std::vector<double>& prices, int period, double num_std) {
    BBResult result;
    if (prices.empty()) return result;
    
    std::vector<double> sma = SMA(prices, period);
    result.middle = sma;
    result.upper.resize(prices.size(), 0.0);
    result.lower.resize(prices.size(), 0.0);
    
    for (size_t i = 0; i < prices.size(); ++i) {
        if (i < (size_t)period - 1) continue;
        double sum = 0.0;
        for (int j = i - period + 1; j <= (int)i; ++j) {
            sum += (prices[j] - sma[i]) * (prices[j] - sma[i]);
        }
        double stddev = std::sqrt(sum / period);
        result.upper[i] = sma[i] + num_std * stddev;
        result.lower[i] = sma[i] - num_std * stddev;
    }
    return result;
}

} // namespace cpp_quant
