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


@dataclass(frozen=True)
class EventStatusChangedEvent(DomainEvent):
    """Raised when a live event's status changes.

    Attributes:
        event_id: The unique identifier of the event.
        new_status: The status the event transitioned to.
    """

    event_id: uuid.UUID = field(
        default_factory=uuid.uuid4,
    )
    new_status: str = ""


@dataclass(frozen=True)
class PollActivatedEvent(DomainEvent):
    """Raised when a poll is activated within an event.

    Attributes:
        poll_id: The unique identifier of the activated poll.
        event_id: The unique identifier of the parent event.
    """

    poll_id: uuid.UUID = field(
        default_factory=uuid.uuid4,
    )
    event_id: uuid.UUID = field(
        default_factory=uuid.uuid4,
    )


@dataclass(frozen=True)
class PollDeactivatedEvent(DomainEvent):
    """Raised when a poll is deactivated within an event.

    Attributes:
        poll_id: The unique identifier of the deactivated poll.
        event_id: The unique identifier of the parent event.
    """

    poll_id: uuid.UUID = field(
        default_factory=uuid.uuid4,
    )
    event_id: uuid.UUID = field(
        default_factory=uuid.uuid4,
    )


@dataclass(frozen=True)
class PollResponseReceivedEvent(DomainEvent):
    """Raised when a participant submits a poll response.

    Attributes:
        poll_id: The unique identifier of the poll.
        fingerprint_id: The identifier of the respondent.
    """

    poll_id: uuid.UUID = field(
        default_factory=uuid.uuid4,
    )
    fingerprint_id: str = ""
