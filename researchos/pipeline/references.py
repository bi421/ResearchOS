"""
Reference validation for ResearchOS pipeline.

Validates that object ID references point to existing objects
in the repository. Pure function — no side effects, no mutations.

This module enforces referential integrity without modifying
any object model classes.
"""

from typing import List, Optional

from researchos.repository.interface import RepositoryInterface
from researchos.core.base_object import BaseObject


class ReferenceValidator:
    """
    Validates that object references exist in the repository.

    This is an external validation layer. Objects remain pure
    (they carry string IDs without checking them). The pipeline
    uses this validator before creating new objects.
    """

    def __init__(self, repository: RepositoryInterface):
        self._repo = repository

    def exists(self, obj_id: str) -> bool:
        """Check whether an object ID exists in the repository."""
        if not obj_id:
            return False
        return self._repo.get(obj_id) is not None

    def require_exists(self, obj_id: str, label: str = "object") -> str:
        """
        Verify an ID exists in the repository.

        Returns:
            The ID if it exists.

        Raises:
            ValueError: If the ID is empty or not found.
        """
        if not obj_id:
            raise ValueError(f"{label} ID is empty — cannot validate reference")
        obj = self._repo.get(obj_id)
        if obj is None:
            raise ValueError(
                f"{label} with ID '{obj_id}' not found in repository — "
                "create it before referencing it"
            )
        return obj_id

    def require_all_exist(self, ids: List[str], label: str = "object") -> List[str]:
        """
        Verify all IDs in a list exist in the repository.

        Returns:
            The list of IDs if all exist.

        Raises:
            ValueError: If any ID is missing.
        """
        missing = [i for i in ids if not self.exists(i)]
        if missing:
            raise ValueError(
                f"{len(missing)} {label}(s) not found in repository: {missing}"
            )
        return ids
