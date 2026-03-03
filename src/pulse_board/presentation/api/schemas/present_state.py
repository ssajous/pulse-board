"""Present state response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PresentPollOptionSchema(BaseModel):
    """Vote count and percentage for a single poll option."""

    option_id: uuid.UUID = Field(description="Option UUID")
    text: str = Field(description="Option display text")
    count: int = Field(description="Number of votes for this option")
    percentage: float = Field(description="Percentage of total votes (0.0–100.0)")


class PresentActivePollSchema(BaseModel):
    """Active poll summary for the present view."""

    poll_id: uuid.UUID = Field(description="Poll UUID")
    question: str = Field(description="Poll question text")
    total_votes: int = Field(description="Total vote count")
    options: list[PresentPollOptionSchema] = Field(description="Per-option results")


class PresentTopicSchema(BaseModel):
    """Topic summary for the present view."""

    id: uuid.UUID = Field(description="Topic UUID")
    content: str = Field(description="Topic content text")
    score: int = Field(description="Current vote score")
    created_at: datetime = Field(description="Creation timestamp")


class PresentStateResponse(BaseModel):
    """Full present mode state for an event."""

    event_id: uuid.UUID = Field(description="Event UUID")
    event_title: str = Field(description="Event title")
    event_code: str = Field(description="6-digit join code")
    active_poll: PresentActivePollSchema | None = Field(
        default=None,
        description="Currently active poll, or null if none",
    )
    top_topics: list[PresentTopicSchema] = Field(
        description="Top 10 topics by score descending",
    )
    participant_count: int = Field(
        description="Number of active WebSocket connections in this event channel",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "event_title": "Team Retrospective",
                    "event_code": "123456",
                    "active_poll": None,
                    "top_topics": [],
                    "participant_count": 0,
                }
            ]
        }
    }
