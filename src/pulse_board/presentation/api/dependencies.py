"""FastAPI dependency injection wiring."""

from fastapi import Request

from pulse_board.application.use_cases.activate_poll import (
    ActivatePollUseCase,
)
from pulse_board.application.use_cases.cast_vote import (
    CastVoteUseCase,
)
from pulse_board.application.use_cases.create_event import (
    CreateEventUseCase,
)
from pulse_board.application.use_cases.create_poll import (
    CreatePollUseCase,
)
from pulse_board.application.use_cases.create_topic import (
    CreateTopicUseCase,
)
from pulse_board.application.use_cases.get_event import (
    GetEventUseCase,
)
from pulse_board.application.use_cases.get_poll_results import (
    GetPollResultsUseCase,
)
from pulse_board.application.use_cases.health_check import (
    HealthCheckUseCase,
)
from pulse_board.application.use_cases.join_event import (
    JoinEventUseCase,
)
from pulse_board.application.use_cases.list_event_topics import (
    ListEventTopicsUseCase,
)
from pulse_board.application.use_cases.list_topics import (
    ListTopicsUseCase,
)
from pulse_board.application.use_cases.submit_poll_response import (
    SubmitPollResponseUseCase,
)
from pulse_board.domain.ports.event_publisher_port import (
    EventPublisher,
)
from pulse_board.domain.services.join_code_generator import (
    JoinCodeGenerator,
)
from pulse_board.domain.services.voting_service import VotingService
from pulse_board.infrastructure.database.connection import (
    get_database,
    get_session_factory,
)
from pulse_board.infrastructure.repositories.event_repository import (
    SQLAlchemyEventRepository,
)
from pulse_board.infrastructure.repositories.poll_repository import (
    SQLAlchemyPollRepository,
)
from pulse_board.infrastructure.repositories.poll_response_repository import (
    SQLAlchemyPollResponseRepository,
)
from pulse_board.infrastructure.repositories.topic_repository import (
    SQLAlchemyTopicRepository,
)
from pulse_board.infrastructure.repositories.vote_repository import (
    SQLAlchemyVoteRepository,
)


def get_health_check_use_case() -> HealthCheckUseCase:
    """Provide a HealthCheckUseCase instance."""
    database = get_database()
    return HealthCheckUseCase(database=database)


def _get_topic_repository() -> SQLAlchemyTopicRepository:
    """Provide a SQLAlchemyTopicRepository instance."""
    return SQLAlchemyTopicRepository(
        session_factory=get_session_factory(),
    )


def _get_event_repository() -> SQLAlchemyEventRepository:
    """Provide a SQLAlchemyEventRepository instance."""
    return SQLAlchemyEventRepository(
        session_factory=get_session_factory(),
    )


def get_create_topic_use_case() -> CreateTopicUseCase:
    """Provide a CreateTopicUseCase instance."""
    return CreateTopicUseCase(
        repository=_get_topic_repository(),
        event_repository=_get_event_repository(),
    )


def get_list_topics_use_case() -> ListTopicsUseCase:
    """Provide a ListTopicsUseCase instance."""
    return ListTopicsUseCase(
        repository=_get_topic_repository(),
    )


def get_create_event_use_case() -> CreateEventUseCase:
    """Provide a CreateEventUseCase instance."""
    return CreateEventUseCase(
        event_repository=_get_event_repository(),
        code_generator=JoinCodeGenerator(),
    )


def get_join_event_use_case() -> JoinEventUseCase:
    """Provide a JoinEventUseCase instance."""
    return JoinEventUseCase(
        event_repository=_get_event_repository(),
    )


def get_get_event_use_case() -> GetEventUseCase:
    """Provide a GetEventUseCase instance."""
    return GetEventUseCase(
        event_repository=_get_event_repository(),
    )


def get_list_event_topics_use_case() -> ListEventTopicsUseCase:
    """Provide a ListEventTopicsUseCase instance."""
    return ListEventTopicsUseCase(
        repository=_get_topic_repository(),
    )


def _get_vote_repository() -> SQLAlchemyVoteRepository:
    """Provide a SQLAlchemyVoteRepository instance."""
    return SQLAlchemyVoteRepository(
        session_factory=get_session_factory(),
    )


def get_cast_vote_use_case() -> CastVoteUseCase:
    """Provide a CastVoteUseCase instance."""
    return CastVoteUseCase(
        vote_repo=_get_vote_repository(),
        topic_repo=_get_topic_repository(),
        voting_service=VotingService(),
    )


def get_event_publisher(request: Request) -> EventPublisher:
    """Provide the EventPublisher from app state."""
    return request.app.state.connection_manager


# ------------------------------------------------------------------
# Poll dependencies
# ------------------------------------------------------------------


def get_poll_repository() -> SQLAlchemyPollRepository:
    """Provide a SQLAlchemyPollRepository instance."""
    return SQLAlchemyPollRepository(
        session_factory=get_session_factory(),
    )


def _get_poll_response_repository() -> SQLAlchemyPollResponseRepository:
    """Provide a SQLAlchemyPollResponseRepository instance."""
    return SQLAlchemyPollResponseRepository(
        session_factory=get_session_factory(),
    )


def get_create_poll_use_case() -> CreatePollUseCase:
    """Provide a CreatePollUseCase instance."""
    return CreatePollUseCase(
        poll_repository=get_poll_repository(),
        event_repository=_get_event_repository(),
    )


def get_activate_poll_use_case() -> ActivatePollUseCase:
    """Provide an ActivatePollUseCase instance."""
    return ActivatePollUseCase(
        poll_repository=get_poll_repository(),
    )


def get_submit_poll_response_use_case() -> SubmitPollResponseUseCase:
    """Provide a SubmitPollResponseUseCase instance."""
    return SubmitPollResponseUseCase(
        poll_repository=get_poll_repository(),
        poll_response_repository=_get_poll_response_repository(),
    )


def get_get_poll_results_use_case() -> GetPollResultsUseCase:
    """Provide a GetPollResultsUseCase instance."""
    return GetPollResultsUseCase(
        poll_repository=get_poll_repository(),
        poll_response_repository=_get_poll_response_repository(),
    )
