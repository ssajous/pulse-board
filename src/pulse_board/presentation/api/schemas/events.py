"""Event request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateEventRequest(BaseModel):
    """Request body for creating a new event session."""

    title: str = Field(
        min_length=1,
        max_length=200,
        description="Event title",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional event description",
    )
    start_date: datetime | None = Field(
        default=None,
        description="Optional scheduled start date",
    )
    end_date: datetime | None = Field(
        default=None,
        description="Optional scheduled end date",
    )
    creator_fingerprint: str | None = Field(
        default=None,
        max_length=255,
        description="Browser fingerprint of the event creator",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Team Retrospective",
                    "description": "Q1 retrospective meeting",
                }
            ]
        }
    }


class EventResponse(BaseModel):
    """Single event in API responses."""

    id: str = Field(
        description="Unique event identifier",
    )
    title: str = Field(
        description="Event title",
    )
    code: str = Field(
        description="6-digit join code",
    )
    description: str | None = Field(
        description="Optional event description",
    )
    start_date: datetime | None = Field(
        default=None,
        description="Optional scheduled start date",
    )
    end_date: datetime | None = Field(
        default=None,
        description="Optional scheduled end date",
    )
    status: str = Field(
        description="Event lifecycle status",
    )
    created_at: datetime = Field(
        description="Event creation timestamp",
    )
    creator_token: str | None = Field(
        default=None,
        description=(
            "Server-issued token identifying the event creator. "
            "Only returned on event creation."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "title": "Team Retrospective",
                    "code": "123456",
                    "description": "Q1 retrospective meeting",
                    "start_date": None,
                    "end_date": None,
                    "status": "active",
                    "created_at": "2026-03-02T12:00:00Z",
                }
            ]
        }
    }


class CheckCreatorResponse(BaseModel):
    """Response for the check-creator endpoint."""

    is_creator: bool = Field(
        description="Whether the provided token matches the event creator.",
    )


class EventListResponse(BaseModel):
    """Response wrapper for event lists."""

    events: list[EventResponse] = Field(
        description="List of events",
    )


class EventStatsResponse(BaseModel):
    """Aggregated statistics for a live event (host dashboard)."""

    participant_count: int = Field(
        description="Number of currently connected participants",
    )
    topic_count: int = Field(
        description="Total number of topics submitted for the event",
    )
    active_topic_count: int = Field(
        description="Number of topics with active status",
    )
    poll_count: int = Field(
        description="Total number of polls created for the event",
    )
    has_active_poll: bool = Field(
        description="Whether any poll is currently active",
    )
    total_poll_responses: int = Field(
        description="Total poll responses across all polls",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "participant_count": 42,
                    "topic_count": 15,
                    "active_topic_count": 10,
                    "poll_count": 3,
                    "has_active_poll": True,
                    "total_poll_responses": 120,
                }
            ]
        }
    }


class CloseEventResponse(BaseModel):
    """Response for a successful event closure."""

    event_id: str = Field(
        description="Unique event identifier",
    )
    status: str = Field(
        description="Final event status (always 'closed')",
    )
