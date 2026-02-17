"""SQLAlchemy implementation of the TopicRepository port."""

import uuid

from sqlalchemy.orm import Session, sessionmaker

from pulse_board.domain.entities.topic import Topic
from pulse_board.domain.ports.topic_repository_port import (
    TopicRepository,
)
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
        """Return topics with score > -5."""
        with self._session_factory() as session:
            models = session.query(TopicModel).filter(TopicModel.score > -5).all()
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
        """Update a topic's score by a relative delta."""
        with self._session_factory() as session:
            model = session.get(TopicModel, id)
            if model is None:
                return None
            model.score += delta
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    @staticmethod
    def _to_model(entity: Topic) -> TopicModel:
        return TopicModel(
            id=entity.id,
            content=entity.content,
            score=entity.score,
            created_at=entity.created_at,
        )

    @staticmethod
    def _to_entity(model: TopicModel) -> Topic:
        return Topic(
            id=model.id,
            content=model.content,
            score=model.score,
            created_at=model.created_at,
        )
