"""Topic request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateTopicRequest(BaseModel):
    """Request body for creating a topic."""

    content: str = Field(min_length=1, max_length=255)


class TopicResponse(BaseModel):
    """Single topic in API responses."""

    id: str
    content: str
    score: int
    created_at: datetime


class TopicListResponse(BaseModel):
    """Response wrapper for topic lists."""

    topics: list[TopicResponse]
