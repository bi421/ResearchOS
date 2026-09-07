"""Evidence-aware ExperimentRunner integration.

This adapter composes the existing ``BaseExperimentRunner`` with the runtime
certification trust layer.  It deliberately does not change computation,
backend routing, or the existing runner return contract.
"""

from __future__ import annotations

from typing import Any

from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.runtime_certification import (
    RuntimeCertification,
    certify_runtime,
)
from researchos.experiments.experiment import Experiment
from researchos.experiments.result import ExperimentResult, ExperimentRun
from researchos.experiments.runner import BaseExperimentRunner


class EvidenceAwareExperimentRunner(BaseExperimentRunner):
    """Base runner plus runtime evidence certification for every run mode.

    The normal runner return values remain unchanged.  Certifications are
    retained for inspection and verification without changing existing
    experiment APIs.
    """

    def __init__(
        self,
        backend: Any | None = None,
        router: Any | None = None,
        evidence_repository: EvidenceRepository | None = None,
    ) -> None:
        super().__init__(backend=backend, router=router)
        self.evidence_repository = evidence_repository or EvidenceRepository()
        self.certifications: list[RuntimeCertification] = []
        self.last_certification: RuntimeCertification | None = None

    def _certify(
        self,
        experiment: Experiment,
        run: ExperimentRun,
        result: ExperimentResult,
    ) -> RuntimeCertification:
        certification = certify_runtime(
            experiment,
            run,
            result,
            self.evidence_repository,
            backend_identity={
                "backend": result.statistics.get("backend_id", ""),
                "version": result.statistics.get("backend_version", ""),
            },
        )
        self.certifications.append(certification)
        self.last_certification = certification
        return certification

    def run(
        self,
        experiment: Experiment,
        dataset: Any,
    ) -> tuple[ExperimentRun, ExperimentResult]:
        """Execute normally, then certify Experiment → Run → Result."""
        run, result = super().run(experiment, dataset)
        self._certify(experiment, run, result)
        return run, result

    def run_with_parameters(
        self,
        experiment: Experiment,
        dataset: Any,
        parameter_overrides: dict[str, Any],
        run_number: int = 1,
    ) -> tuple[ExperimentRun, ExperimentResult]:
        """Execute a parameterised run, then certify its evidence chain."""
        run, result = super().run_with_parameters(
            experiment,
            dataset,
            parameter_overrides,
            run_number,
        )
        self._certify(experiment, run, result)
        return run, result

    def run_walk_forward(
        self,
        experiment: Experiment,
        dataset: Any,
        window_size: int = 252,
        step_size: int = 63,
    ) -> list[tuple[ExperimentRun, ExperimentResult]]:
        """Execute walk-forward runs and certify every successful run."""
        results = super().run_walk_forward(
            experiment,
            dataset,
            window_size,
            step_size,
        )
        for run, result in results:
            if run.status.value == "Completed":
                self._certify(experiment, run, result)
        return results

    def run_monte_carlo(
        self,
        experiment: Experiment,
        dataset: Any,
        num_simulations: int = 1000,
        seed: int | None = None,
    ) -> list[tuple[ExperimentRun, ExperimentResult]]:
        """Execute Monte Carlo runs and certify every successful run."""
        results = super().run_monte_carlo(
            experiment,
            dataset,
            num_simulations,
            seed,
        )
        for run, result in results:
            if run.status.value == "Completed":
                self._certify(experiment, run, result)
        return results


__all__ = ["EvidenceAwareExperimentRunner"]
