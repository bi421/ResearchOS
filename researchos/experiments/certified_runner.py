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
    """Base runner plus mandatory runtime evidence certification.

    The normal ``run`` return value remains ``(ExperimentRun, ExperimentResult)``.
    The corresponding certification is retained on ``last_certification`` so
    callers can inspect or verify the immutable evidence chain without changing
    existing experiment APIs.
    """

    def __init__(
        self,
        backend: Any | None = None,
        router: Any | None = None,
        evidence_repository: EvidenceRepository | None = None,
    ) -> None:
        super().__init__(backend=backend, router=router)
        self.evidence_repository = evidence_repository or EvidenceRepository()
        self.last_certification: RuntimeCertification | None = None

    def _certify(
        self,
        experiment: Experiment,
        run: ExperimentRun,
        result: ExperimentResult,
    ) -> None:
        self.last_certification = certify_runtime(
            experiment,
            run,
            result,
            self.evidence_repository,
            backend_identity={
                "backend": result.statistics.get("backend_id", ""),
                "version": result.statistics.get("backend_version", ""),
            },
        )

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


__all__ = ["EvidenceAwareExperimentRunner"]
