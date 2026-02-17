"""Topic management routes."""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from pulse_board.application.use_cases.create_topic import (
    CreateTopicUseCase,
)
from pulse_board.application.use_cases.list_topics import (
    ListTopicsUseCase,
)
from pulse_board.domain.exceptions import ValidationError
from pulse_board.domain.ports.event_publisher_port import EventPublisher
from pulse_board.presentation.api.dependencies import (
    get_create_topic_use_case,
    get_event_publisher,
    get_list_topics_use_case,
)
from pulse_board.presentation.api.schemas.topics import (
    CreateTopicRequest,
    TopicListResponse,
    TopicResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.post(
    "",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new topic",
    description=("Submit a new topic for community discussion and voting."),
    responses={
        201: {"description": "Topic created successfully"},
        422: {"description": "Validation error"},
    },
)
async def create_topic(
    request: CreateTopicRequest,
    use_case: CreateTopicUseCase = Depends(get_create_topic_use_case),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> TopicResponse:
    """Create a new topic."""
    try:
        result = await asyncio.to_thread(use_case.execute, request.content)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.message,
        ) from exc

    try:
        await publisher.publish_new_topic(
            result.id,
            result.content,
            result.score,
            result.created_at,
        )
    except Exception:
        logger.warning(
            "Failed to broadcast new topic",
            exc_info=True,
        )

    return TopicResponse(
        id=str(result.id),
        content=result.content,
        score=result.score,
        created_at=result.created_at,
    )


@router.get(
    "",
    response_model=TopicListResponse,
    summary="List all topics",
    description=("Retrieve all active topics sorted by popularity score."),
    responses={
        200: {"description": "List of active topics"},
    },
)
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
