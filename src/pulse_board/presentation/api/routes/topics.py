"""Topic management routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from pulse_board.application.use_cases.create_topic import (
    CreateTopicUseCase,
)
from pulse_board.application.use_cases.list_topics import (
    ListTopicsUseCase,
)
from pulse_board.domain.exceptions import ValidationError
from pulse_board.presentation.api.dependencies import (
    get_create_topic_use_case,
    get_list_topics_use_case,
)
from pulse_board.presentation.api.schemas.topics import (
    CreateTopicRequest,
    TopicListResponse,
    TopicResponse,
)

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.post(
    "",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_topic(
    request: CreateTopicRequest,
    use_case: CreateTopicUseCase = Depends(get_create_topic_use_case),
) -> TopicResponse:
    """Create a new topic."""
    try:
        result = use_case.execute(request.content)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.message,
        ) from exc
    return TopicResponse(
        id=str(result.id),
        content=result.content,
        score=result.score,
        created_at=result.created_at,
    )


@router.get("", response_model=TopicListResponse)
def list_topics(
    use_case: ListTopicsUseCase = Depends(get_list_topics_use_case),
) -> TopicListResponse:
    """List all active topics sorted by popularity."""
    summaries = use_case.execute()
    return TopicListResponse(
        topics=[
            TopicResponse(
                id=str(s.id),
                content=s.content,
                score=s.score,
                created_at=s.created_at,
            )
            for s in summaries
        ]
    )
