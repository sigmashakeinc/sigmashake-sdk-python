"""Custom exceptions for the SigmaShake SDK.

All exceptions carry structured error information including HTTP status codes
and API error codes when available.
"""

from __future__ import annotations

from typing import Any, Optional


class SigmaShakeError(Exception):
    """Base exception for all SigmaShake SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        response_body: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.response_body = response_body


class AuthenticationError(SigmaShakeError):
    """Raised on HTTP 401 -- invalid or missing credentials."""


class AuthorizationError(SigmaShakeError):
    """Raised on HTTP 403 -- insufficient permissions."""


class NotFoundError(SigmaShakeError):
    """Raised on HTTP 404 -- requested resource does not exist."""


class ValidationError(SigmaShakeError):
    """Raised on HTTP 422 -- request body failed server-side validation."""


class RateLimitError(SigmaShakeError):
    """Raised on HTTP 429 -- too many requests."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: Optional[float] = None,
        status_code: Optional[int] = 429,
        error_code: Optional[str] = None,
        response_body: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            error_code=error_code,
            response_body=response_body,
        )
        self.retry_after = retry_after


class ServerError(SigmaShakeError):
    """Raised on HTTP 5xx -- server-side failure."""


_STATUS_TO_EXCEPTION: dict[int, type[SigmaShakeError]] = {
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    422: ValidationError,
    429: RateLimitError,
    500: ServerError,
    502: ServerError,
    503: ServerError,
    504: ServerError,
}


def raise_for_status(status_code: int, body: dict[str, Any] | None = None) -> None:
    """Map an HTTP status code to the appropriate SDK exception and raise it.

    Does nothing for 2xx status codes.
    """
    if 200 <= status_code < 300:
        return

    body = body or {}
    message = body.get("message") or body.get("error") or f"HTTP {status_code}"
    error_code = body.get("code")
    exc_cls = _STATUS_TO_EXCEPTION.get(status_code, SigmaShakeError)

    kwargs: dict[str, Any] = {
        "status_code": status_code,
        "error_code": error_code,
        "response_body": body,
    }

    if exc_cls is RateLimitError:
        kwargs["retry_after"] = body.get("retry_after")

    raise exc_cls(message, **kwargs)
