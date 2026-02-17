"""Vote management routes."""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from pulse_board.application.use_cases.cast_vote import CastVoteUseCase
from pulse_board.domain.entities.vote import DOWNVOTE, UPVOTE
from pulse_board.domain.exceptions import (
    DuplicateVoteError,
    EntityNotFoundError,
    ValidationError,
)
from pulse_board.domain.ports.event_publisher_port import EventPublisher
from pulse_board.presentation.api.dependencies import (
    get_cast_vote_use_case,
    get_event_publisher,
)
from pulse_board.presentation.api.schemas.votes import (
    CastVoteRequest,
    CastVoteResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/topics", tags=["votes"])


@router.post(
    "/{topic_id}/votes",
    response_model=CastVoteResponse,
    summary="Cast a vote on a topic",
    description=(
        "Cast an upvote or downvote on a topic. "
        "If the user already voted in the same direction, "
        "the vote is cancelled. If they voted in the "
        "opposite direction, the vote is toggled."
    ),
    responses={
        200: {"description": "Vote cast successfully"},
        404: {"description": "Topic not found"},
        409: {"description": "Duplicate vote conflict"},
        422: {"description": "Validation error"},
    },
)
async def cast_vote(
    topic_id: UUID,
    request: CastVoteRequest,
    use_case: CastVoteUseCase = Depends(get_cast_vote_use_case),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> CastVoteResponse:
    """Cast an upvote or downvote on a topic.

    If the user already voted in the same direction, the vote
    is cancelled. If they voted in the opposite direction, the
    vote is toggled.
    """
    direction = UPVOTE if request.direction == "up" else DOWNVOTE
    try:
        result = await asyncio.to_thread(
            use_case.execute,
            topic_id=topic_id,
            fingerprint_id=request.fingerprint_id,
            direction=direction,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.message,
        ) from exc
    except DuplicateVoteError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc

    try:
        await publisher.publish_score_update(topic_id, result.new_score)
        if result.censured:
            await publisher.publish_topic_censured(topic_id)
    except Exception:
        logger.warning(
            "Failed to broadcast vote update",
            exc_info=True,
        )

    return CastVoteResponse(
        topic_id=str(result.topic_id),
        new_score=result.new_score,
        vote_status=result.vote_status,
        user_vote=result.vote_direction,
        censured=result.censured,
    )
