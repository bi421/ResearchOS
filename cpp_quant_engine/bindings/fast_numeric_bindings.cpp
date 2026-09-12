#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include "quant/fast/fast_numeric.h"

namespace nb = nanobind;
namespace fast = quant::fast;

NB_MODULE(cpp_quant_fast_backend, m) {
  m.doc() = "ResearchOS high-throughput C++ numeric kernels";

  m.def("simple_returns", &fast::simple_returns,
        "Compute simple returns in a single C++ pass.");
  m.def("drawdown_pct", &fast::drawdown_pct,
        "Compute running percentage drawdown in a single C++ pass.");
  m.def("backtest_next_open", &fast::backtest_next_open,
        nb::arg("open"), nb::arg("close"), nb::arg("signal"), nb::arg("quantity"),
        nb::arg("initial_capital") = 100000.0,
        nb::arg("commission_pct") = 0.001,
        nb::arg("slippage_pct") = 0.0005,
        nb::arg("allow_short") = true,
        "Run a callback-free next-open backtest over complete vectors.");
  m.def("risk_scan", &fast::risk_scan,
        nb::arg("returns"), nb::arg("equity"),
        "Compute distribution and drawdown risk metrics in native C++.");
}
