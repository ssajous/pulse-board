"""Poll management routes."""

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, Response, status

from pulse_board.application.use_cases.activate_poll import (
    ActivatePollUseCase,
)
from pulse_board.application.use_cases.create_poll import (
    CreatePollUseCase,
)
from pulse_board.application.use_cases.get_event import (
    GetEventUseCase,
)
from pulse_board.application.use_cases.get_poll_results import (
    GetPollResultsUseCase,
)
from pulse_board.application.use_cases.submit_poll_response import (
    SubmitPollResponseUseCase,
)
from pulse_board.domain.entities.poll import Poll
from pulse_board.domain.ports.event_publisher_port import (
    EventPublisher,
)
from pulse_board.domain.ports.poll_repository_port import (
    PollRepository,
)
from pulse_board.presentation.api.dependencies import (
    get_activate_poll_use_case,
    get_create_poll_use_case,
    get_event_publisher,
    get_get_event_use_case,
    get_get_poll_results_use_case,
    get_poll_repository,
    get_submit_poll_response_use_case,
)
from pulse_board.presentation.api.schemas.polls import (
    ActivatePollRequest,
    CreatePollRequest,
    PollListResponse,
    PollOptionResultSchema,
    PollOptionSchema,
    PollResultsResponse,
    PollSchema,
    SubmitPollResponseRequest,
    SubmitPollResponseSchema,
)

logger = logging.getLogger(__name__)

events_polls_router = APIRouter(
    prefix="/api/events",
    tags=["polls"],
)
polls_router = APIRouter(
    prefix="/api/polls",
    tags=["polls"],
)


def _poll_entity_to_schema(poll: Poll) -> PollSchema:
    """Convert a domain Poll entity to its API schema."""
    return PollSchema(
        id=str(poll.id),
        event_id=str(poll.event_id),
        question=poll.question,
        poll_type=poll.poll_type,
        options=[
            PollOptionSchema(id=str(opt.id), text=opt.text) for opt in poll.options
        ],
        is_active=poll.is_active,
        created_at=poll.created_at,
    )


@events_polls_router.post(
    "/{event_id}/polls",
    response_model=PollSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a poll for an event",
    description="Create a new multiple-choice poll within an event.",
    responses={
        201: {"description": "Poll created successfully"},
        404: {"description": "Event not found"},
        422: {"description": "Validation error"},
    },
)
async def create_poll(
    event_id: uuid.UUID,
    request: CreatePollRequest,
    use_case: CreatePollUseCase = Depends(
        get_create_poll_use_case,
    ),
) -> PollSchema:
    """Create a new poll within an event."""
    result = await asyncio.to_thread(
        use_case.execute,
        event_id,
        request.question,
        request.options,
    )

    return PollSchema(
        id=str(result.id),
        event_id=str(result.event_id),
        question=result.question,
        poll_type=result.poll_type,
        options=[
            PollOptionSchema(id=opt["id"], text=opt["text"]) for opt in result.options
        ],
        is_active=result.is_active,
        created_at=result.created_at,
    )


@events_polls_router.get(
    "/{event_id}/polls",
    response_model=PollListResponse,
    summary="List polls for an event",
    description="Retrieve all polls belonging to an event.",
    responses={
        200: {"description": "List of polls"},
    },
)
async def list_polls(
    event_id: uuid.UUID,
    poll_repo: PollRepository = Depends(get_poll_repository),
) -> PollListResponse:
    """List all polls for an event."""
    polls = await asyncio.to_thread(
        poll_repo.list_by_event,
        event_id,
    )
    return PollListResponse(
        polls=[_poll_entity_to_schema(p) for p in polls],
    )


@events_polls_router.get(
    "/{event_id}/polls/active",
    response_model=PollSchema,
    summary="Get the active poll for an event",
    description=(
        "Retrieve the currently active poll. Returns 204 if no poll is active."
    ),
    responses={
        200: {"description": "Active poll found"},
        204: {"description": "No active poll"},
    },
)
async def get_active_poll(
    event_id: uuid.UUID,
    poll_repo: PollRepository = Depends(get_poll_repository),
) -> PollSchema | Response:
    """Get the currently active poll for an event."""
    poll = await asyncio.to_thread(
        poll_repo.find_active_by_event,
        event_id,
    )
    if poll is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return _poll_entity_to_schema(poll)


@polls_router.patch(
    "/{poll_id}/activate",
    response_model=PollSchema,
    summary="Activate or deactivate a poll",
    description=(
        "Toggle the active status of a poll. "
        "Activating deactivates any other active poll "
        "in the same event."
    ),
    responses={
        200: {"description": "Poll status updated"},
        404: {"description": "Poll not found"},
    },
)
async def activate_poll(
    poll_id: uuid.UUID,
    request: ActivatePollRequest,
    use_case: ActivatePollUseCase = Depends(
        get_activate_poll_use_case,
    ),
    get_event: GetEventUseCase = Depends(
        get_get_event_use_case,
    ),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> PollSchema:
    """Activate or deactivate a poll."""
    result = await asyncio.to_thread(
        use_case.execute,
        poll_id,
        activate=request.activate,
    )

    try:
        event = await asyncio.to_thread(
            get_event.execute,
            result.event_id,
        )
        channel = f"event:{event.code}"
        if result.is_active:
            await publisher.publish_poll_activated_to_channel(
                channel,
                result.id,
                result.question,
                result.options,
            )
        else:
            await publisher.publish_poll_deactivated_to_channel(
                channel,
                result.id,
            )
    except Exception:
        logger.warning(
            "Failed to broadcast poll activation",
            exc_info=True,
        )

    return PollSchema(
        id=str(result.id),
        event_id=str(result.event_id),
        question=result.question,
        poll_type=result.poll_type,
        options=[
            PollOptionSchema(id=opt["id"], text=opt["text"]) for opt in result.options
        ],
        is_active=result.is_active,
        created_at=result.created_at,
    )


@polls_router.post(
    "/{poll_id}/respond",
    response_model=SubmitPollResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a response to a poll",
    description="Submit a vote for a specific option in a poll.",
    responses={
        201: {"description": "Response submitted"},
        404: {"description": "Poll not found"},
        409: {"description": ("Already responded or poll is inactive")},
        422: {"description": "Invalid option"},
    },
)
async def submit_poll_response(
    poll_id: uuid.UUID,
    request: SubmitPollResponseRequest,
    use_case: SubmitPollResponseUseCase = Depends(
        get_submit_poll_response_use_case,
    ),
    results_use_case: GetPollResultsUseCase = Depends(
        get_get_poll_results_use_case,
    ),
    get_event: GetEventUseCase = Depends(
        get_get_event_use_case,
    ),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> SubmitPollResponseSchema:
    """Submit a response to a poll."""
    option_uuid = uuid.UUID(request.option_id)
    result = await asyncio.to_thread(
        use_case.execute,
        poll_id,
        request.fingerprint_id,
        option_uuid,
    )

    try:
        event = await asyncio.to_thread(
            get_event.execute,
            result.event_id,
        )
        channel = f"event:{event.code}"
        poll_results = await asyncio.to_thread(
            results_use_case.execute,
            poll_id,
        )
        await publisher.publish_poll_results_updated_to_channel(
            channel,
            poll_id,
            [
                {
                    "option_id": str(opt.option_id),
                    "text": opt.text,
                    "count": opt.count,
                    "percentage": opt.percentage,
                }
                for opt in poll_results.options
            ],
        )
    except Exception:
        logger.warning(
            "Failed to broadcast poll results",
            exc_info=True,
        )

    return SubmitPollResponseSchema(
        id=str(result.id),
        poll_id=str(result.poll_id),
        option_id=str(result.option_id),
        created_at=result.created_at,
    )


@polls_router.get(
    "/{poll_id}/results",
    response_model=PollResultsResponse,
    summary="Get poll results",
    description="Retrieve aggregated results for a poll.",
    responses={
        200: {"description": "Poll results"},
        404: {"description": "Poll not found"},
    },
)
async def get_poll_results(
    poll_id: uuid.UUID,
    use_case: GetPollResultsUseCase = Depends(
        get_get_poll_results_use_case,
    ),
) -> PollResultsResponse:
    """Get aggregated results for a poll."""
    result = await asyncio.to_thread(
        use_case.execute,
        poll_id,
    )
    return PollResultsResponse(
        poll_id=str(result.poll_id),
        question=result.question,
        total_votes=result.total_votes,
        options=[
            PollOptionResultSchema(
                option_id=str(opt.option_id),
                text=opt.text,
                count=opt.count,
                percentage=opt.percentage,
            )
            for opt in result.options
        ],
    )
