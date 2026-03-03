"""ParticipantCounter port."""

from abc import ABC, abstractmethod


class ParticipantCounter(ABC):
    """Port for counting active WebSocket connections per channel."""

    @abstractmethod
    def get_channel_count(self, channel: str) -> int:
        """Return the number of active connections in a named channel."""
