"""
Custom exceptions for ldlinkpy.

These exceptions provide clear, user-friendly error messages and preserve key
context (HTTP status codes, endpoint, etc.) for debugging.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class LDlinkError(Exception):
    """Base exception for all ldlinkpy errors."""

    def __init__(self, message: str = "An LDlink error occurred.") -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


class TokenMissingError(LDlinkError):
    """Raised when no LDlink API token is provided or discoverable."""

    def __init__(
        self,
        message: str = (
            "LDlink API token is missing. Provide `token=...` or set the "
            "LDLINK_TOKEN environment variable."
        ),
    ) -> None:
        super().__init__(message)


class ValidationError(LDlinkError):
    """Raised when user input fails validation."""

    def __init__(self, message: str = "Input validation failed.") -> None:
        super().__init__(message)


@dataclass(frozen=True)
class APIError(LDlinkError):
    """
    Raised when the LDlink REST API returns an error response or an unexpected status.

    Fields:
        status_code: HTTP status code if available (None if not).
        message: A human-readable error message.
        endpoint: The endpoint path (e.g., "/ldproxy") if available.
    """

    status_code: Optional[int] = None
    message: str = "LDlink API request failed."
    endpoint: Optional[str] = None

    def __post_init__(self) -> None:
        # Ensure Exception args are set to a meaningful string, while keeping dataclass frozen.
        Exception.__init__(self, self.__str__())

    def __str__(self) -> str:
        parts: list[str] = []
        if self.status_code is not None:
            parts.append(f"HTTP {self.status_code}")
        if self.endpoint:
            parts.append(f"endpoint={self.endpoint}")
        prefix = " ".join(parts).strip()

        if prefix:
            return f"LDlink API error ({prefix}): {self.message}"
        return f"LDlink API error: {self.message}"


class ParseError(LDlinkError):
    """Raised when the response cannot be parsed into the expected format."""

    def __init__(self, message: str = "Failed to parse LDlink API response.") -> None:
        super().__init__(message)
