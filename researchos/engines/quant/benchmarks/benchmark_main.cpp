// quant_engine_bench - native benchmark harness for the C++ backtest engine.
//
// Measures, for candle counts {100k, 1M, 10M}:
//   * data ingestion (OHLCVContainer::append)
//   * event replay throughput (EventReplayEngine)
//   * full backtest engine run
//   * PerformanceAnalyzer computation
//   * peak working-set memory
//
// All numbers are printed as CSV rows suitable for the project report.

#include "quant/backtest/backtest_engine.h"
#include "quant/backtest/event_replay.h"
#include "quant/backtest/market_data.h"
#include "quant/backtest/performance_analyzer.h"
#include "quant/market/ohlcv_container.h"
#include "quant/research/optimization_result.h"
#include "quant/research/optimizer.h"
#include "quant/research/parameter_space.h"
#include "quant/strategy/strategy_kernel.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <random>
#include <string>
#include <vector>

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <psapi.h>
#endif

namespace {

using clock_t = std::chrono::steady_clock;

double seconds(clock_t::duration d) {
  return std::chrono::duration<double>(d).count();
}

// Peak working-set size of the current process in MiB (Windows).
double peak_memory_mib() {
#ifdef _WIN32
  PROCESS_MEMORY_COUNTERS pmc{};
  if (GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc)))
    return static_cast<double>(pmc.PeakWorkingSetSize) / (1024.0 * 1024.0);
#endif
  return 0.0;
}

// Deterministic geometric-random-walk candle generator.
std::vector<quant::Candle> generate_candles(size_t count, uint32_t seed = 12345U) {
  std::vector<quant::Candle> out;
  out.reserve(count);
  std::mt19937 rng(seed);
  std::normal_distribution<double> ret(0.0001, 0.01);
  std::uniform_real_distribution<double> jitter(0.9, 1.1);

  const auto epoch = std::chrono::system_clock::from_time_t(0);
  double price = 100.0;
  auto step = std::chrono::minutes(1);
  quant::Candle c;
  c.timeframe = quant::Timeframe::M1;
  for (size_t i = 0; i < count; ++i) {
    price = price * std::exp(ret(rng));
    c.timestamp = epoch + step * static_cast<int64_t>(i);
    double o = price * jitter(rng);
    double cl = price * jitter(rng);
    double hi = std::max(o, cl) * (1.0 + std::abs(ret(rng)) * 0.01);
    double lo = std::min(o, cl) * (1.0 - std::abs(ret(rng)) * 0.01);
    c.open = o;
    c.high = hi;
    c.low = lo;
    c.close = cl;
    c.volume = 1000.0 + ret(rng) * 200.0;
    c.trade_count = 10;
    out.push_back(c);
  }
  return out;
}

void print_row(const std::string& label, size_t candles, double seconds,
               double mem_mib) {
  std::printf("%s,%zu,%.6f,%.2f\n", label.c_str(), candles, seconds, mem_mib);
}

struct Result {
  double seconds = 0.0;
  double mem = 0.0;
};

template <typename Fn>
Result measure(Fn&& fn) {
  const auto start = clock_t::now();
  fn();
  const auto end = clock_t::now();
  return Result{seconds(end - start), peak_memory_mib()};
}

quant::SignalResult trivial_signal(size_t /*bar_index*/,
                                   const std::vector<quant::OHLCV>& history) {
  quant::SignalResult s;
  if (history.empty()) return s;
  const auto& last = history.back();
  if (last.close > last.open) {
    s.direction = quant::TradeDirection::Buy;
    s.quantity = 1.0;
  }
  return s;
}

std::vector<quant::OHLCV> to_bars(const std::vector<quant::Candle>& candles) {
  std::vector<quant::OHLCV> bars;
  bars.reserve(candles.size());
  for (const auto& c : candles) bars.push_back(static_cast<quant::OHLCV>(c));
  return bars;
}

std::vector<quant::strategy::StrategySignal>
sparse_signals(size_t count, size_t stride) {
  std::vector<quant::strategy::StrategySignal> signals;
  for (size_t i = 0; i + 1 < count; i += stride) {
    quant::strategy::StrategySignal s;
    s.bar_index = static_cast<int64_t>(i);
    s.action = quant::strategy::SignalAction::Open;
    s.side = quant::strategy::TradeSide::Long;
    signals.push_back(s);
  }
  return signals;
}

std::vector<quant::strategy::StrategySignal>
signal_per_bar(size_t count) {
  std::vector<quant::strategy::StrategySignal> signals;
  signals.reserve(count);
  for (size_t i = 0; i < count; ++i) {
    quant::strategy::StrategySignal s;
    s.bar_index = static_cast<int64_t>(i);
    s.action = quant::strategy::SignalAction::Open;
    s.side = (i % 2 == 0) ? quant::strategy::TradeSide::Long
                          : quant::strategy::TradeSide::Short;
    signals.push_back(s);
  }
  return signals;
}

quant::strategy::StrategyConfig kernel_cfg(bool force_close) {
  quant::strategy::StrategyConfig cfg;
  cfg.trade.sizing = quant::strategy::PositionSizing::FixedLot;
  cfg.trade.fixed_lot = 1.0;
  cfg.trade.commission_pct = 0.0;
  cfg.trade.spread_pct = 0.0;
  cfg.trade.slippage_pct = 0.0;
  cfg.trade.stop_loss = 2.0;
  cfg.trade.take_profit = 3.0;
  if (force_close) {
    cfg.trade.stop_loss = 0.0;
    cfg.trade.take_profit = 0.0;
    cfg.trade.max_bars_in_trade = 1; // deterministic one round trip per bar
  }
  return cfg;
}

// Hourly OHLCV bars for `count` hours (10 years = 87,660 bars).
std::vector<quant::OHLCV> generate_research_bars(size_t count,
                                                 uint32_t seed = 20260U) {
  std::vector<quant::OHLCV> out;
  out.reserve(count);
  std::mt19937 rng(seed);
  std::normal_distribution<double> ret(0.0001, 0.01);
  std::uniform_real_distribution<double> jitter(0.9, 1.1);
  const auto epoch = std::chrono::system_clock::from_time_t(0);
  double price = 100.0;
  for (size_t i = 0; i < count; ++i) {
    price *= std::exp(ret(rng));
    quant::OHLCV b;
    b.timestamp = epoch + std::chrono::hours(static_cast<int64_t>(i));
    const double o = price * jitter(rng);
    const double cl = price * jitter(rng);
    b.open = o;
    b.close = cl;
    b.high = std::max(o, cl) * (1.0 + std::abs(ret(rng)) * 0.01);
    b.low = std::min(o, cl) * (1.0 - std::abs(ret(rng)) * 0.01);
    b.volume = 1000.0 + ret(rng) * 200.0;
    out.push_back(b);
  }
  return out;
}

// Linear-time SMA crossover signal stream (rolling sums, O(1) extra memory).
quant::research::FunctionSignalGenerator research_cross_gen() {
  return quant::research::FunctionSignalGenerator(
      [](const std::vector<quant::OHLCV>& bars,
         const quant::research::ParamSet& p) {
        const int fast = static_cast<int>(p.get_int("fast", 10));
        const int slow = static_cast<int>(p.get_int("slow", 30));
        const size_t n = bars.size();
        std::vector<quant::strategy::StrategySignal> sigs;
        bool in_long = false;
        double f_sum = 0.0, s_sum = 0.0;
        double f_prev = 0.0, s_prev = 0.0, f_cur = 0.0, s_cur = 0.0;
        for (size_t i = 0; i < n; ++i) {
          const double c = bars[i].close;
          f_sum += c;
          s_sum += c;
          if (i >= static_cast<size_t>(fast)) f_sum -= bars[i - fast].close;
          if (i >= static_cast<size_t>(slow)) s_sum -= bars[i - slow].close;
          f_cur = (i + 1 >= static_cast<size_t>(fast))
                      ? f_sum / static_cast<double>(fast)
                      : 0.0;
          s_cur = (i + 1 >= static_cast<size_t>(slow))
                      ? s_sum / static_cast<double>(slow)
                      : 0.0;
          if (i >= 1 && f_cur > 0.0 && s_cur > 0.0) {
            const bool up = f_cur > s_cur && f_prev <= s_prev;
            const bool dn = f_cur < s_cur && f_prev >= s_prev;
            if (up && !in_long) {
              quant::strategy::StrategySignal sig;
              sig.bar_index = static_cast<int64_t>(i);
              sig.action = quant::strategy::SignalAction::Open;
              sig.side = quant::strategy::TradeSide::Long;
              sigs.push_back(sig);
              in_long = true;
            } else if (dn && in_long) {
              quant::strategy::StrategySignal sig;
              sig.bar_index = static_cast<int64_t>(i);
              sig.action = quant::strategy::SignalAction::Close;
              sig.side = quant::strategy::TradeSide::Long;
              sigs.push_back(sig);
              in_long = false;
            }
          }
          f_prev = f_cur;
          s_prev = s_cur;
        }
        return sigs;
      });
}

// Maps `stop`/`tp` parameters onto the trade configuration.
quant::research::FunctionConfigProvider research_provider() {
  return quant::research::FunctionConfigProvider(
      [](const quant::research::ParamSet& p) {
        quant::strategy::StrategyConfig cfg;
        cfg.trade.sizing = quant::strategy::PositionSizing::FixedLot;
        cfg.trade.fixed_lot = 1.0;
        cfg.trade.commission_pct = 0.0;
        cfg.trade.spread_pct = 0.0;
        cfg.trade.slippage_pct = 0.0;
        cfg.trade.stop_loss = p.get("stop", 2.0);
        cfg.trade.take_profit = p.get("tp", 4.0);
        return cfg;
      });
}

// Exactly 5 x 10 x 5 x 4 = 1000 parameter combinations.
quant::research::ParameterSpace research_space() {
  quant::research::ParameterSpace s;
  s.add_grid("fast", {5.0, 10.0, 15.0, 20.0, 30.0});
  s.add_grid("slow",
             {20.0, 30.0, 40.0, 50.0, 60.0, 80.0, 100.0, 120.0, 150.0, 200.0});
  s.add_grid("stop", {0.5, 1.0, 2.0, 4.0, 8.0});
  s.add_grid("tp", {2.0, 4.0, 8.0, 16.0});
  return s;
}

} // namespace

int main() {
  std::printf("benchmark,count,seconds,peak_mem_mib\n");

  // ── research optimizer: 1000 strategies x 10 years (hourly bars) ─────────
  {
    const size_t h1_count = 10 * 365 * 24; // 87,660 hourly bars / 10 years
    const auto bars = generate_research_bars(h1_count);
    const auto space = research_space();
    if (space.combo_count() != 1000) {
      std::printf("# research space expected 1000 combos, got %zu\n",
                  space.combo_count());
      return 1;
    }
    const auto gen = research_cross_gen();
    const auto provider = research_provider();

    auto run_and_print = [&](const std::string& label,
                             quant::research::OptimizerConfig cfg) {
      quant::research::Optimizer opt({}, cfg);
      auto r = measure([&] {
        auto res = opt.optimize(bars, space, gen, &provider);
        if (res.is_err())
          std::printf("# %s error: %s\n", label.c_str(),
                      res.error().message().c_str());
      });
      print_row(label, h1_count, r.seconds, r.mem);
    };

    quant::research::OptimizerConfig grid1;
    grid1.search_type = quant::research::SearchType::Grid;
    grid1.max_parallelism = 1;
    grid1.top_n = 10;
    run_and_print("research.grid.1000x10y", grid1);

    quant::research::OptimizerConfig grid_auto;
    grid_auto.search_type = quant::research::SearchType::Grid;
    grid_auto.max_parallelism = 0; // std::thread::hardware_concurrency()
    grid_auto.top_n = 10;
    run_and_print("research.grid.1000x10y.auto", grid_auto);

    quant::research::OptimizerConfig seeded;
    seeded.search_type = quant::research::SearchType::Seeded;
    seeded.seed = 42;
    seeded.random_samples = 250;
    seeded.max_parallelism = 1;
    seeded.top_n = 10;
    run_and_print("research.seeded.250x10y", seeded);

    quant::research::OptimizerConfig random;
    random.search_type = quant::research::SearchType::Random;
    random.random_samples = 250;
    random.max_parallelism = 1;
    random.top_n = 10;
    run_and_print("research.random.250x10y", random);
  }

  std::printf("# research rows above use 10 years of hourly candles; remaining "
              "rows reuse the peak-memory process from the large sweeps\n");

  const std::vector<size_t> counts{100'000, 1'000'000, 10'000'000};

  for (size_t count : counts) {
    const std::string label = std::to_string(count / 1000) + "k";

    // ── data generation (not timed as part of the harness itself) ──────────
    const auto candles = generate_candles(count);

    // ── ingestion: OHLCVContainer::append ──────────────────────────────────
    {
      auto r = measure([&] {
        quant::OHLCVContainer container("BENCH", quant::Timeframe::M1);
        for (const auto& c : candles) {
          auto res = container.append(c);
          if (res.is_err()) return;
        }
      });
      print_row("ingest.append", count, r.seconds, r.mem);
    }

    // ── MarketData load ────────────────────────────────────────────────────
    {
      auto r = measure([&] {
        quant::MarketData md;
        auto res = md.load("BENCH", quant::Timeframe::M1, candles);
        (void)res;
      });
      print_row("marketdata.load", count, r.seconds, r.mem);
    }

    // ── event replay ───────────────────────────────────────────────────────
    {
      quant::MarketData md;
      auto res = md.load("BENCH", quant::Timeframe::M1, candles);
      if (res.is_err()) return 1;
      auto r = measure([&] {
        quant::EventReplayEngine replay(md);
        size_t n = 0;
        while (replay.advance()) {
          const auto& ev = replay.current_event();
          n += ev.timestamp.time_since_epoch().count() != 0 ? 1 : 0;
        }
        if (n == 0) std::printf("# replay produced zero events\n");
      });
      print_row("replay.candle", count, r.seconds, r.mem);
    }

    // ── backtest engine ────────────────────────────────────────────────────
    {
      quant::InMemoryOHLCVSource source;
      source.data.reserve(candles.size());
      for (const auto& c : candles) source.data.push_back(static_cast<quant::OHLCV>(c));
      quant::BacktestEngine engine;
      quant::BacktestConfig cfg;
      cfg.initial_capital = 1'000'000.0;
      engine.set_config(cfg);
      auto r = measure([&] {
        auto result = engine.run(source, trivial_signal);
        if (result.is_err()) std::printf("# backtest error: %s\n",
                                         result.error().message().c_str());
      });
      print_row("backtest.run", count, r.seconds, r.mem);
    }

    // ── performance analyzer ───────────────────────────────────────────────
    {
      quant::InMemoryOHLCVSource source;
      source.data.reserve(candles.size());
      for (const auto& c : candles) source.data.push_back(static_cast<quant::OHLCV>(c));
      quant::BacktestEngine engine;
      auto result = engine.run(source, trivial_signal);
      if (result.is_err()) return 1;
      auto r = measure([&] {
        auto report = quant::PerformanceAnalyzer::analyze(result.value());
        (void)report;
      });
      print_row("analyzer.analyze", count, r.seconds, r.mem);
    }

    // ── strategy kernel: full sweep over the whole series ──────────────────
    {
      auto bars = to_bars(candles);
      auto signals = sparse_signals(count, count / 10'000);
      auto cfg = kernel_cfg(false);
      auto r = measure([&] {
        quant::strategy::StrategyKernel k(cfg);
        auto res = k.run(bars, signals, /*compute_hash=*/false);
        if (res.is_err()) std::printf("# kernel error: %s\n",
                                      res.error().message().c_str());
      });
      print_row("strategy.kernel.run", count, r.seconds, r.mem);
    }

    // ── strategy kernel: 1M-signal and 1M-trade streaming rows ─────────────
    if (count == 1'000'000) {
      {
        auto bars = to_bars(candles);
        auto signals = signal_per_bar(count);
        auto cfg = kernel_cfg(false);
        auto r = measure([&] {
          quant::strategy::StrategyKernel k(cfg);
          auto res = k.run(bars, signals, /*compute_hash=*/false);
          if (res.is_err()) std::printf("# kernel error: %s\n",
                                        res.error().message().c_str());
        });
        print_row("strategy.kernel.signals_1m", count, r.seconds, r.mem);
      }
      {
        auto bars = to_bars(candles);
        auto signals = signal_per_bar(count);
        auto cfg = kernel_cfg(true);
        auto r = measure([&] {
          quant::strategy::StrategyKernel k(cfg);
          auto res = k.run(bars, signals, /*compute_hash=*/false);
          if (res.is_err()) std::printf("# kernel error: %s\n",
                                        res.error().message().c_str());
        });
        print_row("strategy.kernel.trades_1m", count, r.seconds, r.mem);
      }
    }
  }

  std::printf("# peak process memory overall: %.2f MiB\n", peak_memory_mib());
  return 0;
}
