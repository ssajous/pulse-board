"""Port interface for database connectivity."""

from abc import ABC, abstractmethod


class DatabasePort(ABC):
    """Abstract interface for database operations."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the database connection is active."""
        ...
