"""SigmaShake Python SDK -- agent-first, async-native, type-safe."""

from ._version import __version__
from .client import SigmaShake
from .pulse import PulseResource
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    SigmaShakeError,
    ValidationError,
)

__all__ = [
    "__version__",
    "SigmaShake",
    "SigmaShakeError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
]
