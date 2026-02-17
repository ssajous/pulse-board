"""Vote request/response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class CastVoteRequest(BaseModel):
    """Request body for casting a vote."""

    fingerprint_id: str = Field(min_length=1, max_length=255)
    direction: Literal["up", "down"]


class CastVoteResponse(BaseModel):
    """Response after casting a vote."""

    topic_id: str
    new_score: int
    vote_status: str
    user_vote: int | None  # 1, -1, or null
    censured: bool
