"""
Walk-Forward Validation — chronological splitter.

Produces strictly chronological, non-overlapping training / validation
folds.  Training always precedes validation; the walk-forward window slides
forward by ``step_size`` each fold.  There is never any shuffling and never
any random split.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import ValidationError

DEFAULT_MAX_FOLDS = 10_000


@dataclass(frozen=True)
class Fold:
    """A single chronological fold.

    Attributes:
        fold_id: 1-based fold identifier.
        train_start: First training index (inclusive).
        train_end: Last training index (inclusive).
        validation_start: First validation index (inclusive).
        validation_end: Last validation index (inclusive).
    """

    fold_id: int
    train_start: int
    train_end: int
    validation_start: int
    validation_end: int

    @property
    def train_range(self) -> tuple[int, int]:
        return (self.train_start, self.train_end)

    @property
    def validation_range(self) -> tuple[int, int]:
        return (self.validation_start, self.validation_end)

    @property
    def train_size(self) -> int:
        return self.train_end - self.train_start + 1

    @property
    def validation_size(self) -> int:
        return self.validation_end - self.validation_start + 1


class WalkForwardSplitter:
    """Split a dataset of ``dataset_length`` samples into chronological
    walk-forward folds.

    Parameters:
        train_size: Number of samples in each training window.
        validation_size: Number of samples in each validation window.
        step_size: Number of samples the combined window slides forward
            between consecutive folds.
    """

    def __init__(
        self,
        train_size: int,
        validation_size: int,
        step_size: int,
    ) -> None:
        if not isinstance(train_size, int) or train_size <= 0:
            raise ValidationError("train_size must be a positive integer")
        if not isinstance(validation_size, int) or validation_size <= 0:
            raise ValidationError("validation_size must be a positive integer")
        if not isinstance(step_size, int) or step_size <= 0:
            raise ValidationError("step_size must be a positive integer")

        self.train_size = train_size
        self.validation_size = validation_size
        self.step_size = step_size

    def _validate_length(self, dataset_length: int) -> None:
        if not isinstance(dataset_length, int) or dataset_length < 0:
            raise ValidationError("dataset_length must be a non-negative integer")

    def split(self, dataset_length: int) -> list[Fold]:
        """Return the chronological folds for a dataset of the given length.

        Raises:
            ValidationError: if the length is negative, the pseudo-test set is
                empty, or a fold would contain an empty validation window.
        """
        self._validate_length(dataset_length)

        folds: list[Fold] = []

        # Guarantee at least one complete validation window fits.  A dataset
        # that cannot satisfy this is rejected rather than silently producing
        # zero (empty) folds.
        if dataset_length < self.train_size + self.validation_size:
            raise ValidationError(
                "dataset too small: need at least train_size + validation_size samples to form a single fold"
            )

        for k in range(DEFAULT_MAX_FOLDS):
            train_start = k * self.step_size
            validation_start = self.train_size + k * self.step_size
            train_end = validation_start - 1
            validation_end = validation_start + self.validation_size - 1

            # Stop when the validation window overflows the available data.
            if validation_end >= dataset_length:
                break

            folds.append(
                Fold(
                    fold_id=k + 1,
                    train_start=train_start,
                    train_end=train_end,
                    validation_start=validation_start,
                    validation_end=validation_end,
                )
            )

        if not folds:
            raise ValidationError("no folds could be constructed")

        return folds


__all__ = ["Fold", "WalkForwardSplitter"]
