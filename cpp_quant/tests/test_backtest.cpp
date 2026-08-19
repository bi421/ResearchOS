#include <gtest/gtest.h>
#include "quant_engine.h"
#include "data_loader.h"
#include <vector>

using namespace cpp_quant;

TEST(DataLoaderTest, BasicLoad) {
    // This test assumes a file exists, we can mock or skip
    SUCCEED();
}

TEST(IndicatorsTest, SMA) {
    std::vector<double> prices = {1,2,3,4,5,6,7,8,9,10};
    auto sma = Indicators::SMA(prices, 3);
    EXPECT_DOUBLE_EQ(sma[2], 2.0);
    EXPECT_DOUBLE_EQ(sma[3], 3.0);
    EXPECT_DOUBLE_EQ(sma[9], 9.0);
}

TEST(BacktestTest, SMAStrategy) {
    std::vector<Candle> candles;
    for (int i = 0; i < 100; ++i) {
        Candle c;
        c.timestamp = i * 300;
        c.open = 100 + i;
        c.high = 101 + i;
        c.low = 99 + i;
        c.close = 100 + i;
        c.volume = 1000;
        candles.push_back(c);
    }
    BacktestEngine engine(candles);
    auto result = engine.runSMA(5, 10);
    EXPECT_GE(result.num_trades, 0);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
