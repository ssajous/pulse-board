"""Vote request/response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class CastVoteRequest(BaseModel):
    """Request body for casting a vote."""

    fingerprint_id: str = Field(
        min_length=1,
        max_length=255,
        description="Browser fingerprint identifier",
    )
    direction: Literal["up", "down"] = Field(
        description="Vote direction",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fingerprint_id": "fp_abc123def456",
                    "direction": "up",
                }
            ]
        }
    }


class CastVoteResponse(BaseModel):
    """Response after casting a vote."""

    topic_id: str = Field(
        description="The topic that was voted on",
    )
    new_score: int = Field(
        description="Updated net vote score",
    )
    vote_status: str = Field(
        description="Result of the vote action",
    )
    user_vote: int | None = Field(
        description=("Current user vote direction: 1 (up), -1 (down), or null"),
    )
    censured: bool = Field(
        description=("Whether the topic was censured due to low score"),
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "topic_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "new_score": 6,
                    "vote_status": "voted",
                    "user_vote": 1,
                    "censured": False,
                }
            ]
        }
    }
