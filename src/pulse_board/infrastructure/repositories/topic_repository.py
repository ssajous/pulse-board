"""SQLAlchemy implementation of the TopicRepository port."""

import uuid

from sqlalchemy import func, update
from sqlalchemy.orm import Session, sessionmaker

from pulse_board.domain.entities.topic import Topic, TopicStatus
from pulse_board.domain.ports.topic_repository_port import (
    TopicRepository,
)
from pulse_board.domain.services.voting_service import CENSURE_THRESHOLD
from pulse_board.infrastructure.database.models.topic_model import (
    TopicModel,
)


class SQLAlchemyTopicRepository(TopicRepository):
    """PostgreSQL-backed topic repository."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(self, topic: Topic) -> Topic:
        """Persist a new topic."""
        with self._session_factory() as session:
            model = self._to_model(topic)
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def list_active(self) -> list[Topic]:
        """Return single-board topics above the censure threshold.

        Only returns topics that are not associated with any
        event (``event_id IS NULL``).
        """
        with self._session_factory() as session:
            models = (
                session.query(TopicModel)
                .filter(
                    TopicModel.score > CENSURE_THRESHOLD,
                    TopicModel.event_id.is_(None),
                )
                .all()
            )
            return [self._to_entity(m) for m in models]

    def list_by_event(self, event_id: uuid.UUID) -> list[Topic]:
        """Return non-archived topics for a specific event above threshold."""
        with self._session_factory() as session:
            models = (
                session.query(TopicModel)
                .filter(
                    TopicModel.event_id == event_id,
                    TopicModel.score > CENSURE_THRESHOLD,
                    TopicModel.status != TopicStatus.ARCHIVED.value,
                )
                .all()
            )
            return [self._to_entity(m) for m in models]

    def list_all_by_event(self, event_id: uuid.UUID) -> list[Topic]:
        """Return all topics for a specific event regardless of status."""
        with self._session_factory() as session:
            models = (
                session.query(TopicModel).filter(TopicModel.event_id == event_id).all()
            )
            return [self._to_entity(m) for m in models]

    def get_by_id(self, id: uuid.UUID) -> Topic | None:
        """Look up a topic by its unique identifier."""
        with self._session_factory() as session:
            model = session.get(TopicModel, id)
            return self._to_entity(model) if model else None

    def delete(self, id: uuid.UUID) -> None:
        """Remove a topic by its unique identifier."""
        with self._session_factory() as session:
            model = session.get(TopicModel, id)
            if model:
                session.delete(model)
                session.commit()

    def update_score(self, id: uuid.UUID, delta: int) -> Topic | None:
        """Update a topic's score by a relative delta.

        Uses an atomic SQL expression to avoid lost updates
        under concurrent access.
        """
        with self._session_factory() as session:
            result = session.execute(
                update(TopicModel)
                .where(TopicModel.id == id)
                .values(score=TopicModel.score + delta)
            )
            session.commit()
            if result.rowcount == 0:  # type: ignore[union-attr]
                return None
            model = session.get(TopicModel, id)
            return self._to_entity(model) if model else None

    def update_status(self, id: uuid.UUID, status: TopicStatus) -> Topic | None:
        """Update the lifecycle status of a topic."""
        with self._session_factory() as session:
            result = session.execute(
                update(TopicModel)
                .where(TopicModel.id == id)
                .values(status=status.value)
            )
            session.commit()
            if result.rowcount == 0:  # type: ignore[union-attr]
                return None
            model = session.get(TopicModel, id)
            return self._to_entity(model) if model else None

    def count_by_event(self, event_id: uuid.UUID) -> int:
        """Count all topics belonging to a specific event."""
        with self._session_factory() as session:
            count: int = (
                session.query(func.count(TopicModel.id))
                .filter(TopicModel.event_id == event_id)
                .scalar()
                or 0
            )
            return count

    def count_by_event_and_status(
        self, event_id: uuid.UUID, status: TopicStatus
    ) -> int:
        """Count topics for an event filtered by status."""
        with self._session_factory() as session:
            count: int = (
                session.query(func.count(TopicModel.id))
                .filter(
                    TopicModel.event_id == event_id,
                    TopicModel.status == status.value,
                )
                .scalar()
                or 0
            )
            return count

    @staticmethod
    def _to_model(entity: Topic) -> TopicModel:
        return TopicModel(
            id=entity.id,
            content=entity.content,
            score=entity.score,
            created_at=entity.created_at,
            event_id=entity.event_id,
            status=entity.status.value,
        )

    @staticmethod
    def _to_entity(model: TopicModel) -> Topic:
        return Topic(
            id=model.id,
            content=model.content,
            score=model.score,
            created_at=model.created_at,
            event_id=model.event_id,
            status=TopicStatus(model.status),
        )
