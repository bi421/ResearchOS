#include "data_loader.h"
#include <fstream>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <iostream>

namespace cpp_quant {

std::vector<Candle> DataLoader::loadCSV(const std::string& filename) {
    std::vector<Candle> candles;
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Cannot open file: " << filename << std::endl;
        return candles;
    }

    std::string line;
    while (std::getline(file, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string datetime_str, open_str, high_str, low_str, close_str, volume_str;

        std::getline(ss, datetime_str, ';');
        std::getline(ss, open_str, ';');
        std::getline(ss, high_str, ';');
        std::getline(ss, low_str, ';');
        std::getline(ss, close_str, ';');
        std::getline(ss, volume_str, ';');

        try {
            // Parse datetime: 20210103 180000
            int year = std::stoi(datetime_str.substr(0, 4));
            int month = std::stoi(datetime_str.substr(4, 2));
            int day = std::stoi(datetime_str.substr(6, 2));
            int hour = std::stoi(datetime_str.substr(9, 2));
            int min = std::stoi(datetime_str.substr(11, 2));
            int sec = std::stoi(datetime_str.substr(13, 2));

            // Convert to Unix timestamp (C++20 compatible way)
            std::tm tm = {};
            tm.tm_year = year - 1900;
            tm.tm_mon = month - 1;
            tm.tm_mday = day;
            tm.tm_hour = hour;
            tm.tm_min = min;
            tm.tm_sec = sec;
            // timegm not standard, use mktime (assumes local time, but we treat as UTC)
            // In C++20 we could use std::chrono, but for simplicity, keep mktime
            // Better: use _mkgmtime on Windows
            #ifdef _WIN32
            int64_t timestamp = _mkgmtime(&tm);
            #else
            int64_t timestamp = timegm(&tm);
            #endif

            if (timestamp < 0) continue;

            Candle c;
            c.timestamp = timestamp;
            c.open = std::stod(open_str);
            c.high = std::stod(high_str);
            c.low = std::stod(low_str);
            c.close = std::stod(close_str);
            c.volume = std::stod(volume_str);
            candles.push_back(c);
        } catch (...) {
            // Skip malformed line
        }
    }
    return candles;
}

std::vector<Candle> DataLoader::mergeFiles(const std::vector<std::string>& files) {
    std::vector<Candle> all;
    for (const auto& f : files) {
        auto candles = loadCSV(f);
        all.insert(all.end(), candles.begin(), candles.end());
    }
    // Sort by timestamp
    std::sort(all.begin(), all.end(), [](const Candle& a, const Candle& b) {
        return a.timestamp < b.timestamp;
    });
    return all;
}

std::vector<Candle> DataLoader::aggregate(const std::vector<Candle>& data, int minutes) {
    if (data.empty() || minutes <= 1) return data;

    std::vector<Candle> result;
    int64_t interval = minutes * 60; // seconds

    size_t i = 0;
    while (i < data.size()) {
        int64_t start_ts = data[i].timestamp;
        int64_t end_ts = start_ts + interval;

        double open = data[i].open;
        double high = data[i].high;
        double low = data[i].low;
        double close = data[i].close;
        double volume = data[i].volume;

        i++;
        while (i < data.size() && data[i].timestamp < end_ts) {
            high = std::max(high, data[i].high);
            low = std::min(low, data[i].low);
            close = data[i].close;
            volume += data[i].volume;
            i++;
        }

        Candle c;
        c.timestamp = start_ts;
        c.open = open;
        c.high = high;
        c.low = low;
        c.close = close;
        c.volume = volume;
        result.push_back(c);
    }
    return result;
}

OHLCV DataLoader::toOHLCV(const std::vector<Candle>& candles) {
    OHLCV result;
    result.timestamps.reserve(candles.size());
    result.opens.reserve(candles.size());
    result.highs.reserve(candles.size());
    result.lows.reserve(candles.size());
    result.closes.reserve(candles.size());
    result.volumes.reserve(candles.size());

    for (const auto& c : candles) {
        result.timestamps.push_back(c.timestamp);
        result.opens.push_back(c.open);
        result.highs.push_back(c.high);
        result.lows.push_back(c.low);
        result.closes.push_back(c.close);
        result.volumes.push_back(c.volume);
    }
    return result;
}

} // namespace cpp_quant
