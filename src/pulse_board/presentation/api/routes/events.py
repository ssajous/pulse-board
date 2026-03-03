"""Event management routes."""

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, Query, status

from pulse_board.application.use_cases.check_event_creator import (
    CheckEventCreatorUseCase,
)
from pulse_board.application.use_cases.create_event import (
    CreateEventUseCase,
)
from pulse_board.application.use_cases.create_topic import (
    CreateTopicUseCase,
)
from pulse_board.application.use_cases.get_event import (
    GetEventUseCase,
)
from pulse_board.application.use_cases.join_event import (
    JoinEventUseCase,
)
from pulse_board.application.use_cases.list_event_topics import (
    ListEventTopicsUseCase,
)
from pulse_board.domain.ports.event_publisher_port import (
    EventPublisher,
)
from pulse_board.presentation.api.dependencies import (
    get_check_event_creator_use_case,
    get_create_event_use_case,
    get_create_topic_use_case,
    get_event_publisher,
    get_get_event_use_case,
    get_join_event_use_case,
    get_list_event_topics_use_case,
)
from pulse_board.presentation.api.schemas.events import (
    CheckCreatorResponse,
    CreateEventRequest,
    EventResponse,
)
from pulse_board.presentation.api.schemas.topics import (
    CreateTopicRequest,
    TopicListResponse,
    TopicResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event",
    description="Create a new live event session with a generated join code.",
    responses={
        201: {"description": "Event created successfully"},
        422: {"description": "Validation error"},
    },
)
async def create_event(
    request: CreateEventRequest,
    use_case: CreateEventUseCase = Depends(
        get_create_event_use_case,
    ),
) -> EventResponse:
    """Create a new event session."""
    result = await asyncio.to_thread(
        use_case.execute,
        request.title,
        description=request.description,
        start_date=request.start_date,
        end_date=request.end_date,
        creator_fingerprint=request.creator_fingerprint,
    )

    return EventResponse(
        id=str(result.id),
        title=result.title,
        code=result.code,
        description=result.description,
        start_date=result.start_date,
        end_date=result.end_date,
        status=result.status.value,
        created_at=result.created_at,
        creator_token=result.creator_token,
    )


@router.get(
    "/join/{code}",
    response_model=EventResponse,
    summary="Join an event by code",
    description="Look up an active event using its 6-digit join code.",
    responses={
        200: {"description": "Event found and active"},
        404: {"description": "No event found with given code"},
        409: {"description": "Event is no longer active"},
    },
)
async def join_event(
    code: str,
    use_case: JoinEventUseCase = Depends(
        get_join_event_use_case,
    ),
) -> EventResponse:
    """Join an event by its join code."""
    result = await asyncio.to_thread(use_case.execute, code)

    return EventResponse(
        id=str(result.id),
        title=result.title,
        code=result.code,
        description=result.description,
        start_date=result.start_date,
        end_date=result.end_date,
        status=result.status.value,
        created_at=result.created_at,
        creator_token=None,
    )


@router.get(
    "/{event_id}/check-creator",
    response_model=CheckCreatorResponse,
    summary="Check if the caller is the event creator",
    description=(
        "Verify whether the provided creator token matches "
        "the server-issued token for this event."
    ),
    responses={
        200: {"description": "Creator check result"},
        404: {"description": "Event not found"},
    },
)
async def check_event_creator(
    event_id: uuid.UUID,
    creator_token: str = Query(
        description="Server-issued creator token to verify.",
    ),
    use_case: CheckEventCreatorUseCase = Depends(
        get_check_event_creator_use_case,
    ),
) -> CheckCreatorResponse:
    """Check whether the given creator token belongs to the event creator."""
    result = await asyncio.to_thread(
        use_case.execute,
        event_id,
        creator_token,
    )
    return CheckCreatorResponse(is_creator=result.is_creator)


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get event details",
    description="Retrieve an event by its unique identifier.",
    responses={
        200: {"description": "Event details"},
        404: {"description": "Event not found"},
    },
)
async def get_event(
    event_id: uuid.UUID,
    use_case: GetEventUseCase = Depends(
        get_get_event_use_case,
    ),
) -> EventResponse:
    """Get event details by ID."""
    result = await asyncio.to_thread(use_case.execute, event_id)

    return EventResponse(
        id=str(result.id),
        title=result.title,
        code=result.code,
        description=result.description,
        start_date=result.start_date,
        end_date=result.end_date,
        status=result.status.value,
        created_at=result.created_at,
        creator_token=None,
    )


@router.get(
    "/{event_id}/topics",
    response_model=TopicListResponse,
    summary="List event topics",
    description=("Retrieve all topics for an event, sorted by popularity score."),
    responses={
        200: {"description": "List of event topics"},
    },
)
async def list_event_topics(
    event_id: uuid.UUID,
    use_case: ListEventTopicsUseCase = Depends(
        get_list_event_topics_use_case,
    ),
) -> TopicListResponse:
    """List topics belonging to an event."""
    summaries = await asyncio.to_thread(use_case.execute, event_id)
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


@router.post(
    "/{event_id}/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a topic within an event",
    description=("Submit a new topic for an active event session."),
    responses={
        201: {"description": "Topic created successfully"},
        404: {"description": "Event not found"},
        409: {"description": "Event is not active"},
        422: {"description": "Validation error"},
    },
)
async def create_event_topic(
    event_id: uuid.UUID,
    request: CreateTopicRequest,
    use_case: CreateTopicUseCase = Depends(
        get_create_topic_use_case,
    ),
    get_event: GetEventUseCase = Depends(
        get_get_event_use_case,
    ),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> TopicResponse:
    """Create a topic scoped to a specific event."""
    result = await asyncio.to_thread(
        use_case.execute,
        request.content,
        event_id=event_id,
    )

    try:
        event = await asyncio.to_thread(get_event.execute, event_id)
        channel = f"event:{event.code}"
        await publisher.publish_new_topic_to_channel(
            channel,
            result.id,
            result.content,
            result.score,
            result.created_at,
        )
    except Exception:
        logger.warning(
            "Failed to broadcast to event channel",
            exc_info=True,
        )

    return TopicResponse(
        id=str(result.id),
        content=result.content,
        score=result.score,
        created_at=result.created_at,
    )
