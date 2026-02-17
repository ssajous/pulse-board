"""Domain events for the Pulse Board voting system."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    Frozen dataclass providing an immutable event record with
    an automatic timestamp.
    """

    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )


@dataclass(frozen=True)
class TopicCensuredEvent(DomainEvent):
    """Raised when a topic's score drops below the censure threshold.

    Attributes:
        topic_id: The unique identifier of the censured topic.
        final_score: The topic's score at the time of censure.
    """

    topic_id: uuid.UUID = field(
        default_factory=uuid.uuid4,
    )
    final_score: int = 0
