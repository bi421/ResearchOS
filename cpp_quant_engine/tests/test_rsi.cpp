#include <gtest/gtest.h>
#include "quant/indicators/rsi.h"
#include <cmath>

TEST(RSI, EmptyInput) {
    std::vector<double> closes;
    auto result = quant::indicators::rsi(closes, 14);
    EXPECT_TRUE(result.empty());
}

TEST(RSI, ShortInput) {
    std::vector<double> closes = {100.0, 101.0, 102.0};
    auto result = quant::indicators::rsi(closes, 14);
    EXPECT_EQ(result.size(), 3u);
    for (size_t i = 0; i < 3; ++i) {
        EXPECT_TRUE(std::isnan(result[i]));
    }
}

TEST(RSI, AllGains) {
    std::vector<double> closes = {100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114};
    auto result = quant::indicators::rsi(closes, 14);
    EXPECT_EQ(result.size(), 15u);
    // Эхний 14 утга NaN
    for (size_t i = 0; i < 14; ++i) {
        EXPECT_TRUE(std::isnan(result[i]));
    }
    // Бүх өсөлттэй бол RSI = 100
    EXPECT_DOUBLE_EQ(result[14], 100.0);
}

TEST(RSI, AllLosses) {
    std::vector<double> closes = {114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100};
    auto result = quant::indicators::rsi(closes, 14);
    EXPECT_EQ(result.size(), 15u);
    // Бүх уналттай бол RSI = 0
    EXPECT_DOUBLE_EQ(result[14], 0.0);
}

TEST(RSI, MixedMarket) {
    std::vector<double> closes = {100, 102, 101, 103, 100, 104, 99, 105, 98, 106, 97, 107, 96, 108, 95, 109};
    auto result = quant::indicators::rsi(closes, 14);
    EXPECT_EQ(result.size(), 16u);
    // RSI 0-100 хооронд байх ёстой
    EXPECT_GE(result[14], 0.0);
    EXPECT_LE(result[14], 100.0);
    EXPECT_GE(result[15], 0.0);
    EXPECT_LE(result[15], 100.0);
}
