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
    status: str = Field(
        default="active",
        description="Lifecycle status of the topic",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "content": "Should we adopt async standup meetings?",
                    "score": 5,
                    "created_at": "2026-02-17T12:00:00Z",
                    "status": "active",
                }
            ]
        }
    }


class UpdateTopicStatusRequest(BaseModel):
    """Request body for updating a topic's lifecycle status."""

    status: str = Field(
        description=(
            "New lifecycle status. One of: active, highlighted, answered, archived."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"status": "answered"},
            ]
        }
    }


class TopicStatusResponse(BaseModel):
    """Response for a successful topic status update."""

    topic_id: str = Field(
        description="Unique topic identifier",
    )
    new_status: str = Field(
        description="The status the topic was transitioned to",
    )


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
