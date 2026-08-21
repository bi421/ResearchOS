"""Bridge exception hierarchy.

Numeric codes are stable and shared with C++ (``BridgeErrorCode`` in
``python/bridge_interface.h``) and with the pybind11 adapter
(``cpp_quant_backend.BridgeError.code``).
"""

from __future__ import annotations


class BridgeError(RuntimeError):
    """Base error for all bridge failures."""

    code: int | None = None
    name: str | None = None

    def __init__(self, message: str, code: int | None = None, name: str | None = None) -> None:
        if code is not None:
            self.code = code
        if name is not None:
            self.name = name
        super().__init__(message)


class InvalidArgumentError(BridgeError):
    code = 100
    name = "InvalidArgument"


class InvalidParameterError(BridgeError):
    code = 101
    name = "InvalidParameter"


class InvalidTypeError(BridgeError):
    code = 102
    name = "InvalidType"


class InsufficientDataError(BridgeError):
    code = 200
    name = "InsufficientData"


class EmptyDataError(BridgeError):
    code = 201
    name = "EmptyData"


class MalformedDataError(BridgeError):
    code = 202
    name = "MalformedData"


class OutOfBoundsError(BridgeError):
    code = 203
    name = "OutOfBounds"


class UnsupportedVersionError(BridgeError):
    code = 300
    name = "UnsupportedVersion"


class ValidationFailedError(BridgeError):
    code = 301
    name = "ValidationFailed"


class HashMismatchError(BridgeError):
    code = 302
    name = "HashMismatch"


class InternalError(BridgeError):
    code = 500
    name = "InternalError"


_ERROR_CLASSES: dict[int, type[BridgeError]] = {
    cls.code: cls
    for cls in (
        InvalidArgumentError,
        InvalidParameterError,
        InvalidTypeError,
        InsufficientDataError,
        EmptyDataError,
        MalformedDataError,
        OutOfBoundsError,
        UnsupportedVersionError,
        ValidationFailedError,
        HashMismatchError,
        InternalError,
    )
}


def error_from_code(code: int, message: str, name: str | None = None) -> BridgeError:
    """Build the typed bridge error for a stable numeric code."""
    cls = _ERROR_CLASSES.get(code, BridgeError)
    return cls(message, code=code, name=name)


def error_from_native(exc: BaseException) -> BridgeError:
    """Translate a native C++ bridge exception into the Python hierarchy."""
    code = getattr(exc, "code", None)
    name = getattr(exc, "name", None)
    if code is None:
        if isinstance(exc, BridgeError):
            return exc
        return InvalidTypeError(str(exc), code=102, name="InvalidType")
    return error_from_code(int(code), str(exc), name=name)


__all__ = [
    "BridgeError",
    "InvalidArgumentError",
    "InvalidParameterError",
    "InvalidTypeError",
    "InsufficientDataError",
    "EmptyDataError",
    "MalformedDataError",
    "OutOfBoundsError",
    "UnsupportedVersionError",
    "ValidationFailedError",
    "HashMismatchError",
    "InternalError",
    "error_from_code",
    "error_from_native",
]
