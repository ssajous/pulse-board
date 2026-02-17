"""Topic request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateTopicRequest(BaseModel):
    """Request body for creating a topic."""

    content: str = Field(
        min_length=1,
        max_length=255,
        description="The topic text content",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Should we adopt async standup meetings?",
                }
            ]
        }
    }


class TopicResponse(BaseModel):
    """Single topic in API responses."""

    id: str = Field(
        description="Unique topic identifier",
    )
    content: str = Field(
        description="The topic text content",
    )
    score: int = Field(
        description="Net vote score",
    )
    created_at: datetime = Field(
        description="Topic creation timestamp",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "content": "Should we adopt async standup meetings?",
                    "score": 5,
                    "created_at": "2026-02-17T12:00:00Z",
                }
            ]
        }
    }


class TopicListResponse(BaseModel):
    """Response wrapper for topic lists."""

    topics: list[TopicResponse] = Field(
        description="List of active topics",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "topics": [
                        {
                            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                            "content": "Should we adopt async standups?",
                            "score": 5,
                            "created_at": "2026-02-17T12:00:00Z",
                        }
                    ]
                }
            ]
        }
    }
