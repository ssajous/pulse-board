"""FastAPI dependency injection wiring."""

from pulse_board.application.use_cases.create_topic import (
    CreateTopicUseCase,
)
from pulse_board.application.use_cases.health_check import HealthCheckUseCase
from pulse_board.application.use_cases.list_topics import (
    ListTopicsUseCase,
)
from pulse_board.infrastructure.database.connection import (
    get_database,
    get_session_factory,
)
from pulse_board.infrastructure.repositories.topic_repository import (
    SQLAlchemyTopicRepository,
)


def get_health_check_use_case() -> HealthCheckUseCase:
    """Provide a HealthCheckUseCase instance."""
    database = get_database()
    return HealthCheckUseCase(database=database)


def _get_topic_repository() -> SQLAlchemyTopicRepository:
    """Provide a SQLAlchemyTopicRepository instance."""
    return SQLAlchemyTopicRepository(session_factory=get_session_factory())


def get_create_topic_use_case() -> CreateTopicUseCase:
    """Provide a CreateTopicUseCase instance."""
    return CreateTopicUseCase(repository=_get_topic_repository())


def get_list_topics_use_case() -> ListTopicsUseCase:
    """Provide a ListTopicsUseCase instance."""
    return ListTopicsUseCase(repository=_get_topic_repository())
