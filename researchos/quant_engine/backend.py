"""
PythonQuantBackend — pure Python implementation of QuantComputationInterface.

This is the reference implementation for the Quant Computation Engine.
All computations are:
    - Deterministic: Same inputs → same outputs
    - Versioned: CalculationVersion controls formula selection
    - Pure Python: No external dependencies

Future C++ Quant Engine can replace this backend by implementing the same
QuantComputationInterface without changing any upper layers.

Based on Article XVII: Object Model — Quant Engine Layer.
"""

from __future__ import annotations

from typing import Any, Dict, List

from researchos.core.timestamp import utc_now
from researchos.quant_engine.capabilities import (
    QUANT_OPERATIONS,
    REFERENCE_BACKEND_NAME,
    REFERENCE_BACKEND_VERSION,
    BackendCapabilities,
)
from researchos.quant_engine.interface import QuantComputationInterface
from researchos.quant_engine.metrics import (
    compute_all_metrics,
    max_drawdown,
)
from researchos.quant_engine.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)
from researchos.quant_engine.performance import (
    compute_performance_analytics,
)
from researchos.quant_engine.statistics import (
    calculate_returns_from_prices,
    compute_statistics,
    rolling_volatility,
    volatility_change,
)


class PythonQuantBackend(QuantComputationInterface):
    """
    Pure Python reference implementation of the Quant Computation Engine.

    This backend implements all QuantComputationInterface methods using
    only the Python standard library. It is designed to be:
        - A reference for the future C++ backend
        - Deterministic and reproducible
        - Safe for all edge cases (empty data, zero variance, etc.)

    The Python backend can be swapped for a C++ backend by implementing
    the same QuantComputationInterface.
    """

    def __init__(self) -> None:
        # Stateless and deterministic: no RNG, no hidden mutable state.
        # All computation depends only on the explicit inputs passed to
        # each method, so identical inputs always produce identical outputs.
        pass

    # ── Certification identity (Phase 4.1) ───────────────────────────────

    BACKEND_NAME = REFERENCE_BACKEND_NAME
    BACKEND_VERSION = REFERENCE_BACKEND_VERSION

    def capabilities(self) -> BackendCapabilities:
        """Advertise the certified capability declaration.

        The Python reference backend is the scientific source of truth and
        therefore advertises the full operation set with every ResearchOS
        trust-boundary guarantee enabled.
        """
        return BackendCapabilities(
            backend_name=self.BACKEND_NAME,
            version=self.BACKEND_VERSION,
            supported_operations=QUANT_OPERATIONS,
            deterministic=True,
            stateless=True,
            no_timestamps=True,
            no_randomness=True,
            explicit_typing=True,
        )

    # ──────────────────────────────────────────────
    # Dataset Contract Normalization
    # ──────────────────────────────────────────────

    def _extract_prices(self, dataset: Any) -> List[float]:
        """
        Normalize a dataset contract into a deterministic close-price series.

        This is the ONLY place where data-record knowledge (Candles / OHLCV /
        dict shapes) lives in the computation layer. The Experiment Framework
        never sees these structures — it passes the dataset contract through
        untouched.

        Supported dataset contracts:
            - ``List[float]``: used directly as the price series.
            - ``HistoricalDataset``: ``close`` prices from Candle records.
            - ``List[Candle]``: ``close`` prices from candle objects.
            - ``List[dict]`` with ``close`` key: close prices from dict records.
            - ``None``: deterministic synthetic prices (252 periods) for
              testing / demo when no dataset is provided.

        Args:
            dataset: The dataset contract to normalize.

        Returns:
            List of float prices (oldest to newest).
        """
        if dataset is None:
            # Deterministic default prices for testing when no dataset provided.
            base = 100.0
            return [base * (1.0 + 0.0001 * i) for i in range(252)]

        if isinstance(dataset, list):
            if not dataset:
                return [100.0]
            # List of Candle objects (duck-typed via 'close' attribute).
            if hasattr(dataset[0], "close"):
                return [float(c.close) for c in dataset]
            # List of floats — use directly.
            if isinstance(dataset[0], (int, float)):
                return [float(p) for p in dataset]
            # List of dicts with a 'close' key.
            if isinstance(dataset[0], dict) and "close" in dataset[0]:
                return [float(d["close"]) for d in dataset]

        # HistoricalDataset via duck typing (records + symbol).
        if hasattr(dataset, "records") and hasattr(dataset, "symbol"):
            records = dataset.records
            if records and hasattr(records[0], "close"):
                return [float(r.close) for r in records]

        # Any iterable of Candle-like objects.
        if hasattr(dataset, "__iter__"):
            try:
                items = list(dataset)
                if items and hasattr(items[0], "close"):
                    return [float(c.close) for c in items]
            except (TypeError, IndexError):
                pass

        # Fallback: deterministic default.
        return [100.0]

    # ──────────────────────────────────────────────
    # Returns
    # ──────────────────────────────────────────────

    def calculate_returns(
        self,
        prices: List[float],
        return_type: str = "percentage",
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> List[float]:
        return calculate_returns_from_prices(prices, return_type, calculation_version)

    # ──────────────────────────────────────────────
    # Volatility
    # ──────────────────────────────────────────────

    def calculate_volatility(
        self,
        returns: List[float],
        method: str = "standard_deviation",
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> float:
        if calculation_version != CalculationVersion.CALCULATION_V1:
            raise ValueError(f"Unsupported calculation version: {calculation_version}")

        if not returns:
            raise ValueError("Cannot compute volatility on empty dataset")

        if method == "standard_deviation":
            from researchos.quant_engine.statistics import standard_deviation

            return standard_deviation(returns)
        elif method == "rolling":
            rolling = rolling_volatility(returns)
            if not rolling:
                return 0.0
            return rolling[-1]  # Return the most recent rolling volatility
        elif method == "change":
            return volatility_change(returns)
        else:
            raise ValueError(
                f"Unrecognized method '{method}'. "
                "Expected 'standard_deviation', 'rolling', or 'change'."
            )

    # ──────────────────────────────────────────────
    # Drawdown
    # ──────────────────────────────────────────────

    def calculate_drawdown(
        self,
        equity_curve: List[float],
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, Any]:
        if calculation_version != CalculationVersion.CALCULATION_V1:
            raise ValueError(f"Unsupported calculation version: {calculation_version}")

        return max_drawdown(equity_curve)

    # ──────────────────────────────────────────────
    # Statistics
    # ──────────────────────────────────────────────

    def calculate_statistics(
        self,
        returns: List[float],
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, Any]:
        return compute_statistics(returns, calculation_version)

    # ──────────────────────────────────────────────
    # Metrics
    # ──────────────────────────────────────────────

    def calculate_metrics(
        self,
        returns: List[float],
        equity_curve: List[float],
        risk_free_rate: float = 0.0,
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, float]:
        metrics = compute_all_metrics(
            returns,
            equity_curve,
            risk_free_rate,
            calculation_version=calculation_version,
        )
        if "max_drawdown" in metrics:
            metrics["max_drawdown"] = round(float(metrics["max_drawdown"]), 8)
            if metrics["max_drawdown"] != 0.0 and "mean_return" in metrics:
                metrics["calmar_ratio"] = (
                    float(metrics["mean_return"]) * 252 / abs(metrics["max_drawdown"])
                )
        return metrics

    # ──────────────────────────────────────────────
    # Performance Analytics
    # ──────────────────────────────────────────────

    def calculate_performance_analytics(
        self,
        returns: List[float],
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, Any]:
        return compute_performance_analytics(returns, calculation_version)

    # ──────────────────────────────────────────────
    # Simulation
    # ──────────────────────────────────────────────

    def run_simulation(
        self,
        request: SimulationRequest,
        dataset: Any,
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
        strategy: Any = None,
    ) -> SimulationResult:
        if calculation_version != CalculationVersion.CALCULATION_V1:
            raise ValueError(f"Unsupported calculation version: {calculation_version}")

        # MODE B: Real bar-by-bar backtest via ReplayEngine + ExecutionSimulationLayer.
        # Activated by request.parameters["mode"] == "backtest". Uses the existing
        # StrategyEvaluationInterface / ExecutionSimulationLayer / ReplayEngine —
        # no duplicate engine code lives here.
        mode = str(request.parameters.get("mode", "passive")).lower()
        if mode == "backtest":
            return self._run_backtest(request, dataset, calculation_version, strategy)

        # ── MODE A: passive (returns-based) simulation — backward compatible ──
        # Normalize the dataset contract into a close-price series. This is
        # the ONLY data-parsing point in the computation layer — the upper
        # layers (Experiment Framework) never see Candle/OHLCV structures.
        prices = self._extract_prices(dataset)

        if len(prices) < 2:
            raise ValueError(f"Need at least 2 prices for simulation, got {len(prices)}")

        # Compute input hash for provenance
        input_hash = request.compute_input_hash()

        # Generate simulation ID from request
        sim_id = f"sim_{input_hash[:16]}"

        # Calculate returns
        returns = self.calculate_returns(
            prices, return_type="percentage", calculation_version=calculation_version
        )

        # Build equity curve from returns
        initial_capital = request.parameters.get("initial_capital", 100000.0)
        equity_curve = self._build_equity_curve(returns, initial_capital)

        # Compute metrics
        risk_free_rate = request.parameters.get("risk_free_rate", 0.0)
        metrics = self.calculate_metrics(returns, equity_curve, risk_free_rate, calculation_version)

        # Compute statistics
        statistics = self.calculate_statistics(returns, calculation_version)

        # Compute performance analytics
        performance = self.calculate_performance_analytics(returns, calculation_version)

        # Build result
        result = SimulationResult(
            simulation_id=sim_id,
            dataset_reference=request.dataset_reference,
            dataset_version=request.dataset_version,
            calculation_version=calculation_version,
            parameters=dict(request.parameters),
            start_time=request.start_time,
            end_time=request.end_time,
            input_hash=input_hash,
            execution_timestamp=utc_now().isoformat(),
            returns=returns,
            equity_curve=equity_curve,
            metrics=metrics,
            statistics=statistics,
            performance=performance,
        )

        # Compute result hash
        result.result_hash = result.compute_result_hash()

        return result

    def _run_backtest(
        self,
        request: SimulationRequest,
        dataset: Any,
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
        strategy: Any = None,
    ) -> SimulationResult:
        """
        Execute a real bar-by-bar backtest (Mode B).

        Pipeline (existing components, no duplication):
            dataset
              ↓
            ReplayEngine
              ↓
            StrategyEvaluationInterface → Signal
              ↓
            ExecutionSimulationLayer (orders / fills / positions / trades)
              ↓
            SimulationResult

        The ``strategy`` argument defaults to ``BuyAndHoldStrategy``. It is
        passed through from the caller (e.g. the Experiment Runner) — the
        backend never imports decision/execution/strategy top-level modules.

        Args:
            request: SimulationRequest (mode == "backtest").
            dataset: The dataset contract (same formats as Mode A).
            calculation_version: Must be CALCULATION_V1.
            strategy: Optional StrategyEvaluationInterface instance.

        Returns:
            SimulationResult fully populated with trades, signals, positions,
            execution_stats, equity_curve, returns, metrics, and provenance.
        """
        from researchos.quant_engine.execution import ExecutionSimulationLayer
        from researchos.quant_engine.replay import ReplayEngine
        from researchos.quant_engine.strategy import BuyAndHoldStrategy

        strategy = strategy or BuyAndHoldStrategy()

        prices = self._extract_prices(dataset)
        if len(prices) < 2:
            raise ValueError(f"Need at least 2 prices for backtest, got {len(prices)}")

        # Fresh execution layer per call → no shared state, fully deterministic.
        execution = ExecutionSimulationLayer(
            initial_capital=float(request.parameters.get("initial_capital", 100000.0)),
            commission=str(request.parameters.get("commission", "fixed:0.0")),
            slippage=str(request.parameters.get("slippage", "fixed:0.0")),
            symbol=request.dataset_reference,
            position_size=float(request.parameters.get("position_size", 1.0)),
        )

        engine = ReplayEngine(strategy=strategy, execution=execution)
        output = engine.run(dataset)

        returns = self.calculate_returns(
            prices,
            return_type="percentage",
            calculation_version=calculation_version,
        )
        equity_curve = output["equity_curve"] or self._build_equity_curve(
            returns, float(request.parameters.get("initial_capital", 100000.0))
        )

        risk_free_rate = float(request.parameters.get("risk_free_rate", 0.0))
        metrics = self.calculate_metrics(returns, equity_curve, risk_free_rate, calculation_version)
        statistics = self.calculate_statistics(returns, calculation_version)
        performance = self.calculate_performance_analytics(returns, calculation_version)

        input_hash = request.compute_input_hash()
        sim_id = f"sim_{input_hash[:16]}"

        result = SimulationResult(
            simulation_id=sim_id,
            dataset_reference=request.dataset_reference,
            dataset_version=request.dataset_version,
            calculation_version=calculation_version,
            parameters=dict(request.parameters),
            start_time=request.start_time,
            end_time=request.end_time,
            input_hash=input_hash,
            execution_timestamp=utc_now().isoformat(),
            returns=returns,
            equity_curve=equity_curve,
            metrics=metrics,
            statistics=statistics,
            performance=performance,
            trades=output["trades"],
            signals=output["signals"],
            positions=output["positions"],
            execution_stats=output["execution_stats"],
        )

        # Compute result hash (includes trades/signals/positions/execution_stats).
        result.result_hash = result.compute_result_hash()

        return result

    def _build_equity_curve(
        self,
        returns: List[float],
        initial_capital: float = 100000.0,
    ) -> List[float]:
        """
        Build an equity curve from a series of percentage returns.

        Args:
            returns: List of periodic percentage returns.
            initial_capital: Starting capital value.

        Returns:
            List of equity values (same length as returns + 1 for initial capital).
        """
        equity = [initial_capital]
        for r in returns:
            equity.append(equity[-1] * (1.0 + r))
        return equity
