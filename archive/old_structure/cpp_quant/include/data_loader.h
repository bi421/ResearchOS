#pragma once
#include <vector>
#include <string>
#include <cstdint>

namespace cpp_quant {

struct Candle {
    int64_t timestamp;  // Unix timestamp (seconds)
    double open;
    double high;
    double low;
    double close;
    double volume;
};

struct OHLCV {
    std::vector<int64_t> timestamps;
    std::vector<double> opens;
    std::vector<double> highs;
    std::vector<double> lows;
    std::vector<double> closes;
    std::vector<double> volumes;
};

class DataLoader {
public:
    // CSV файлаас унших (формат: 20210103 180000;open;high;low;close;volume)
    static std::vector<Candle> loadCSV(const std::string& filename);

    // Олон файлыг нэгтгэх
    static std::vector<Candle> mergeFiles(const std::vector<std::string>& files);

    // Агрегацлах (жишээ нь 1мин -> 5мин)
    static std::vector<Candle> aggregate(const std::vector<Candle>& data, int minutes);

    // Candle-ийг OHLCV болгон хувиргах (Python-д илгээхэд хялбар)
    static OHLCV toOHLCV(const std::vector<Candle>& candles);
};

} // namespace cpp_quant
