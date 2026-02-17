"""Vote management routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from pulse_board.application.use_cases.cast_vote import CastVoteUseCase
from pulse_board.domain.exceptions import (
    DuplicateVoteError,
    EntityNotFoundError,
    ValidationError,
)
from pulse_board.presentation.api.dependencies import (
    get_cast_vote_use_case,
)
from pulse_board.presentation.api.schemas.votes import (
    CastVoteRequest,
    CastVoteResponse,
)

router = APIRouter(prefix="/api/topics", tags=["votes"])


@router.post(
    "/{topic_id}/votes",
    response_model=CastVoteResponse,
)
def cast_vote(
    topic_id: UUID,
    request: CastVoteRequest,
    use_case: CastVoteUseCase = Depends(get_cast_vote_use_case),
) -> CastVoteResponse:
    """Cast an upvote or downvote on a topic.

    If the user already voted in the same direction, the vote
    is cancelled. If they voted in the opposite direction, the
    vote is toggled.
    """
    direction = 1 if request.direction == "up" else -1
    try:
        result = use_case.execute(
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
    return CastVoteResponse(
        topic_id=str(result.topic_id),
        new_score=result.new_score,
        vote_status=result.vote_status,
        user_vote=result.vote_direction,
        censured=result.censured,
    )
