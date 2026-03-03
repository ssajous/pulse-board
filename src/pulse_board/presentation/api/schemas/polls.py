"""Poll request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreatePollRequest(BaseModel):
    """Request body for creating a new poll."""

    question: str = Field(
        min_length=1,
        max_length=500,
        description="The poll question text",
    )
    options: list[str] = Field(
        min_length=2,
        max_length=10,
        description="List of option texts (2-10 items)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "What topic should we discuss?",
                    "options": [
                        "Architecture",
                        "Testing",
                        "Performance",
                    ],
                }
            ]
        }
    }


class PollOptionSchema(BaseModel):
    """A single poll option in API responses."""

    id: str = Field(
        description="Unique option identifier",
    )
    text: str = Field(
        description="Option display text",
    )


class PollSchema(BaseModel):
    """Single poll in API responses."""

    id: str = Field(
        description="Unique poll identifier",
    )
    event_id: str = Field(
        description="Parent event identifier",
    )
    question: str = Field(
        description="The poll question text",
    )
    poll_type: str = Field(
        description="Type of poll",
    )
    options: list[PollOptionSchema] = Field(
        description="Available options",
    )
    is_active: bool = Field(
        description="Whether the poll is currently active",
    )
    created_at: datetime = Field(
        description="Poll creation timestamp",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "a1b2c3d4-...",
                    "event_id": "e5f6a7b8-...",
                    "question": "What topic?",
                    "poll_type": "multiple_choice",
                    "options": [
                        {"id": "opt1-...", "text": "A"},
                        {"id": "opt2-...", "text": "B"},
                    ],
                    "is_active": False,
                    "created_at": "2026-03-02T12:00:00Z",
                }
            ]
        }
    }


class PollListResponse(BaseModel):
    """Response wrapper for poll lists."""

    polls: list[PollSchema] = Field(
        description="List of polls",
    )


class ActivatePollRequest(BaseModel):
    """Request body for activating/deactivating a poll."""

    activate: bool = Field(
        description="True to activate, False to deactivate",
    )

    model_config = {"json_schema_extra": {"examples": [{"activate": True}]}}


class SubmitPollResponseRequest(BaseModel):
    """Request body for submitting a poll response."""

    fingerprint_id: str = Field(
        min_length=1,
        max_length=255,
        description="Browser fingerprint identifier",
    )
    option_id: str = Field(
        description="UUID of the selected option",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fingerprint_id": "fp_abc123def456",
                    "option_id": "a1b2c3d4-...",
                }
            ]
        }
    }


class SubmitPollResponseSchema(BaseModel):
    """Response after submitting a poll response."""

    id: str = Field(
        description="Unique response identifier",
    )
    poll_id: str = Field(
        description="The poll that was responded to",
    )
    option_id: str = Field(
        description="The selected option",
    )
    created_at: datetime = Field(
        description="Response submission timestamp",
    )


class PollOptionResultSchema(BaseModel):
    """Vote count and percentage for a single option."""

    option_id: str = Field(
        description="Unique option identifier",
    )
    text: str = Field(
        description="Option display text",
    )
    count: int = Field(
        description="Number of votes for this option",
    )
    percentage: float = Field(
        description="Percentage of total votes (0.0-100.0)",
    )


class PollResultsResponse(BaseModel):
    """Aggregated poll results."""

    poll_id: str = Field(
        description="Unique poll identifier",
    )
    question: str = Field(
        description="The poll question text",
    )
    total_votes: int = Field(
        description="Total number of responses",
    )
    options: list[PollOptionResultSchema] = Field(
        description="Per-option results",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "poll_id": "a1b2c3d4-...",
                    "question": "What topic?",
                    "total_votes": 42,
                    "options": [
                        {
                            "option_id": "opt1-...",
                            "text": "A",
                            "count": 25,
                            "percentage": 59.5,
                        },
                        {
                            "option_id": "opt2-...",
                            "text": "B",
                            "count": 17,
                            "percentage": 40.5,
                        },
                    ],
                }
            ]
        }
    }
