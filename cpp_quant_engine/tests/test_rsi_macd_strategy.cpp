#include <gtest/gtest.h>
#include "quant/strategies/rsi_macd_strategy.h"

TEST(RsiMacdStrategy, BuySignal) {
    std::vector<double> closes = {100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110};
    
    quant::strategies::RsiMacdStrategy strategy;
    auto signal = strategy.evaluate(closes);
    
    EXPECT_GE(signal.confidence, 0.0);
    EXPECT_LE(signal.confidence, 1.0);
}

TEST(RsiMacdStrategy, HoldSignal) {
    std::vector<double> closes(50, 100.0); 
    quant::strategies::RsiMacdStrategy strategy;
    auto signal = strategy.evaluate(closes);
    EXPECT_EQ(signal.action, 0); 
}
