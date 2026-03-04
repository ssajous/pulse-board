"""Poll request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CreatePollRequest(BaseModel):
    """Request body for creating a new poll."""

    question: str = Field(
        min_length=1,
        max_length=500,
        description="The poll question text",
    )
    poll_type: str = Field(
        default="multiple_choice",
        description=("Type of poll: multiple_choice, rating, open_text, or word_cloud"),
    )
    options: list[str] = Field(
        default=[],
        description="List of option texts (2-10 items for multiple choice)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "What topic should we discuss?",
                    "poll_type": "multiple_choice",
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
    option_id: str | None = Field(
        default=None,
        description="UUID of the selected option (multiple_choice polls)",
    )
    response_value: int | str | None = Field(
        default=None,
        description=(
            "Rating integer 1-5 (rating polls), text string "
            "(open_text polls), or 1-3 word phrase (word_cloud polls)"
        ),
    )

    @field_validator("response_value")
    @classmethod
    def limit_string_length(cls, v: int | str | None) -> int | str | None:
        """Reject oversized string payloads at the API boundary."""
        if isinstance(v, str) and len(v) > 500:
            msg = "response_value must be 500 characters or fewer"
            raise ValueError(msg)
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fingerprint_id": "fp_abc123def456",
                    "option_id": "a1b2c3d4-...",
                },
                {
                    "fingerprint_id": "fp_abc123def456",
                    "response_value": 4,
                },
                {
                    "fingerprint_id": "fp_abc123def456",
                    "response_value": "Great session!",
                },
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
    option_id: str | None = Field(
        description="The selected option (None for rating/open_text)",
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
    """Aggregated multiple-choice poll results."""

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


class RatingPollResultsResponse(BaseModel):
    """Aggregated rating poll results."""

    poll_id: str = Field(
        description="Unique poll identifier",
    )
    question: str = Field(
        description="The poll question text",
    )
    total_votes: int = Field(
        description="Total number of rating responses",
    )
    average_rating: float | None = Field(
        description="Average rating value, or null if no votes",
    )
    distribution: dict[str, int] = Field(
        description='Rating distribution mapping ("1"-"5") to count',
    )


class OpenTextResponseSchema(BaseModel):
    """A single open-text response in API output."""

    id: str = Field(
        description="Unique response identifier",
    )
    text: str = Field(
        description="The submitted text content",
    )
    created_at: datetime = Field(
        description="Response submission timestamp",
    )


class OpenTextPollResultsResponse(BaseModel):
    """Paginated open-text poll results."""

    poll_id: str = Field(
        description="Unique poll identifier",
    )
    question: str = Field(
        description="The poll question text",
    )
    total_responses: int = Field(
        description="Total number of text responses",
    )
    responses: list[OpenTextResponseSchema] = Field(
        description="Current page of responses (newest first)",
    )
    page: int = Field(
        description="Current page number (1-based)",
    )
    page_size: int = Field(
        description="Number of responses per page",
    )
    total_pages: int = Field(
        description="Total number of pages",
    )


class WordFrequencySchema(BaseModel):
    """A single word frequency in word cloud results."""

    text: str = Field(
        description="The normalized word or phrase",
    )
    count: int = Field(
        description="Number of times this word was submitted",
    )


class WordCloudPollResultsResponse(BaseModel):
    """Aggregated word cloud poll results."""

    poll_id: str = Field(
        description="Unique poll identifier",
    )
    question: str = Field(
        description="The poll question text",
    )
    total_responses: int = Field(
        description="Total number of word cloud submissions",
    )
    words: list[WordFrequencySchema] = Field(
        description="Word frequencies sorted by count descending",
    )
