"""
ResearchOS Macro Intelligence Layer - Exceptions
"""



class MILException(Exception):
    """Base exception for Macro Intelligence Layer."""
    pass


class ContractValidationError(MILException):
    """Raised when contract validation fails."""
    pass


class StorageError(MILException):
    """Raised on storage operations failure."""
    pass


class AdapterError(MILException):
    """Raised on adapter operations failure."""
    pass


class EvidenceNotFoundError(MILException):
    """Raised when evidence is not found."""
    pass


class QuarantineError(MILException):
    """Raised on quarantine operations failure."""
    pass


class AlertError(MILException):
    """Raised on alert operations failure."""
    pass
