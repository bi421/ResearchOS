#include <gtest/gtest.h>
#include "quant/indicators/macd.h"
#include <cmath>

TEST(MACD, EmptyInput) {
    std::vector<double> closes;
    auto result = quant::indicators::macd(closes);
    EXPECT_TRUE(result.macd_line.empty());
    EXPECT_TRUE(result.signal_line.empty());
    EXPECT_TRUE(result.histogram.empty());
}

TEST(MACD, ShortInput) {
    std::vector<double> closes = {100.0, 101.0, 102.0};
    auto result = quant::indicators::macd(closes, 12, 26, 9);
    EXPECT_EQ(result.macd_line.size(), 3u);
    for (size_t i = 0; i < 3; ++i) {
        EXPECT_TRUE(std::isnan(result.macd_line[i]));
    }
}

TEST(MACD, ConstantPrice) {
    std::vector<double> closes(50, 100.0);
    auto result = quant::indicators::macd(closes, 12, 26, 9);
    // Тогтмол үнэтэй бол MACD = 0
    for (size_t i = 25; i < 50; ++i) {
        if (!std::isnan(result.macd_line[i])) {
            EXPECT_NEAR(result.macd_line[i], 0.0, 1e-6);
        }
    }
}

TEST(MACD, Uptrend) {
    std::vector<double> closes;
    for (size_t i = 0; i < 50; ++i) {
        closes.push_back(100.0 + i);
    }
    auto result = quant::indicators::macd(closes, 12, 26, 9);
    // Өсөлтийн чиг хандлагатай бол MACD > 0
    bool has_positive = false;
    for (size_t i = 25; i < 50; ++i) {
        if (!std::isnan(result.macd_line[i]) && result.macd_line[i] > 0) {
            has_positive = true;
            break;
        }
    }
    EXPECT_TRUE(has_positive);
}

TEST(EMA, BasicCalculation) {
    std::vector<double> data = {100, 101, 102, 103, 104, 105};
    auto result = quant::indicators::ema(data, 3);
    EXPECT_EQ(result.size(), 6u);
    // Эхний 2 утга NaN
    EXPECT_TRUE(std::isnan(result[0]));
    EXPECT_TRUE(std::isnan(result[1]));
    // 3 дахь утга = (100+101+102)/3 = 101
    EXPECT_NEAR(result[2], 101.0, 1e-6);
}
