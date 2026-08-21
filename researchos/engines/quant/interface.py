"""
QuantComputationInterface — abstract interface for computation backends.

Purpose:
    Provide a clean abstraction boundary between ResearchOS upper layers and
    the numerical computation backend. Upper layers (Experiment Framework,
    Market Memory, Validation) depend ONLY on this interface.

    A future C++ backend (C++20 + CMake + pybind11) can implement this same
    interface, replacing the Python backend without any changes to upper layers.

Design:
    - Minimal: Only the methods needed for research computation
    - Stateless: No internal state — all parameters are passed explicitly
    - Deterministic: Same inputs → same outputs (seeded RNG, versioned formulas)
    - Serializable: Input/output types are JSON-serializable

Certification contract (Phase 4.1):
    Every conforming backend MUST guarantee:
        - deterministic execution: identical inputs → identical outputs
        - no hidden mutable state affecting computation
        - no timestamps in computation results
        - no randomness consumed during computation
        - explicit typing: declared signatures, no implicit value coercion
    These guarantees are machine-checkable via ``capabilities()``, and the
    ``BackendRouter`` refuses to route work to a backend that does not
    advertise them.

Based on Article XVII: Object Model — Quant Engine Layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List

from researchos.engines.quant.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)

if TYPE_CHECKING:  # pragma: no cover - annotation-only import
    from researchos.engines.quant.capabilities import BackendCapabilities


class QuantComputationInterface(ABC):
    """
    Abstract interface for the Quant Computation Engine.

    All computation backends (Python, future C++) must implement this interface.
    Upper layers interact only with this abstract class.

    This is NOT a trading engine. This is NOT execution logic.
    This is a NUMERICAL COMPUTATION LAYER for research analytics.
    """

    # ── identity / certification ─────────────────────────────────────────

    def get_version(self) -> str:
        """Return a stable backend version string.

        The default returns the backend class name.  Concrete backends
        override this with a meaningful version (e.g. ``"1.0.0"``).
        """
        return type(self).__name__

    def capabilities(self) -> "BackendCapabilities":
        """Return the backend's advertised certification capabilities.

        The default declaration advertises the full interface operation set
        with the ResearchOS trust-boundary guarantees.  Concrete backends
        override this to declare a precise name, version, and operation set.
        """
        from researchos.engines.quant.capabilities import default_capabilities

        return default_capabilities(self)

    @abstractmethod
    def calculate_returns(
        self,
        prices: List[float],
        return_type: str = "percentage",
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> List[float]:
        """
        Calculate returns from a price series.

        Args:
            prices: Ordered list of prices (oldest to newest).
            return_type: One of "absolute", "percentage", "log".
            calculation_version: Which version of the calculation to use.

        Returns:
            List of return values (length = len(prices) - 1).

        Raises:
            ValueError: If prices has fewer than 2 elements.
            ValueError: If return_type is not recognized.
        """
        ...

    @abstractmethod
    def calculate_volatility(
        self,
        returns: List[float],
        method: str = "standard_deviation",
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> float:
        """
        Calculate volatility from a return series.

        Args:
            returns: List of periodic returns.
            method: One of "standard_deviation", "rolling", "change".
            calculation_version: Which version of the calculation to use.

        Returns:
            Volatility value.

        Raises:
            ValueError: If returns is empty.
        """
        ...

    @abstractmethod
    def calculate_drawdown(
        self,
        equity_curve: List[float],
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, Any]:
        """
        Calculate drawdown metrics from an equity curve.

        Args:
            equity_curve: Ordered list of equity values (oldest to newest).
            calculation_version: Which version of the calculation to use.

        Returns:
            Dict with keys:
                - max_drawdown: Maximum drawdown as a decimal (e.g., -0.25).
                - max_drawdown_pct: Maximum drawdown as a percentage.
                - recovery_period: Number of periods to recover from max drawdown.
                - downside_deviation: Standard deviation of negative returns only.

        Raises:
            ValueError: If equity_curve has fewer than 2 elements.
        """
        ...

    @abstractmethod
    def calculate_statistics(
        self,
        returns: List[float],
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, Any]:
        """
        Calculate statistical summaries of a return series.

        Args:
            returns: List of periodic returns.
            calculation_version: Which version of the calculation to use.

        Returns:
            Dict with keys:
                - mean: Arithmetic mean return.
                - std: Standard deviation of returns.
                - variance: Variance of returns.
                - skewness: Skewness of return distribution.
                - kurtosis: Kurtosis of return distribution.
                - min: Minimum return.
                - max: Maximum return.
                - count: Number of return observations.
                - sum: Sum of returns.

        Raises:
            ValueError: If returns is empty.
        """
        ...

    @abstractmethod
    def run_simulation(
        self,
        request: SimulationRequest,
        dataset: Any,
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> SimulationResult:
        """
        Execute a historical simulation.

        The backend owns all dataset-contract normalisation (Candle / OHLCV /
        HistoricalDataset -> price series). The caller passes the raw dataset
        contract through untouched.

        Args:
            request: Complete simulation request with all parameters.
            dataset: Dataset contract (None, HistoricalDataset, List[Candle],
                     List[float], or any iterable with ``close`` attributes).
            calculation_version: Which version of the calculation to use.

        Returns:
            SimulationResult with all computed metrics and provenance.

        Raises:
            ValueError: If dataset is empty or has insufficient data.
        """
        ...

    @abstractmethod
    def calculate_metrics(
        self,
        returns: List[float],
        equity_curve: List[float],
        risk_free_rate: float = 0.0,
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, float]:
        """
        Calculate a comprehensive set of performance metrics.

        Args:
            returns: List of periodic returns.
            equity_curve: List of equity values over time.
            risk_free_rate: Annual risk-free rate (decimal, e.g., 0.05 for 5%).
            calculation_version: Which version of the calculation to use.

        Returns:
            Dict of metric_name -> computed_value.

        Raises:
            ValueError: If returns is empty or equity_curve has fewer than 2 elements.
        """
        ...

    @abstractmethod
    def calculate_performance_analytics(
        self,
        returns: List[float],
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, Any]:
        """
        Calculate research performance analytics from a return series.

        This is research-only analysis — NOT trading signals or decisions.

        Args:
            returns: List of periodic returns.
            calculation_version: Which version of the calculation to use.

        Returns:
            Dict with keys:
                - win_rate: Percentage of positive returns.
                - loss_rate: Percentage of negative returns.
                - average_win: Average positive return.
                - average_loss: Average negative return (negative value).
                - win_loss_ratio: |avg_win / avg_loss|.
                - profit_factor: Sum of wins / |sum of losses|.
                - consistency: Percentage of periods with positive returns.
                - max_consecutive_wins: Longest streak of positive returns.
                - max_consecutive_losses: Longest streak of negative returns.

        Raises:
            ValueError: If returns is empty.
        """
        ...
