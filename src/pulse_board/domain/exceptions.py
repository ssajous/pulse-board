"""Domain exception classes for the Pulse Board application."""


class DomainError(Exception):
    """Base exception for all domain-level errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ValidationError(DomainError):
    """Raised when a domain validation rule is violated."""


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist."""


class DuplicateVoteError(DomainError):
    """Raised when a duplicate vote is detected."""


class EventNotFoundError(DomainError):
    """Raised when a requested event does not exist."""


class EventNotActiveError(DomainError):
    """Raised when an operation requires an active event."""


class CodeGenerationError(DomainError):
    """Raised when a unique join code cannot be generated."""
