"""SQLAlchemy implementation of the VoteRepository port."""

import uuid

from sqlalchemy.orm import Session, sessionmaker

from pulse_board.domain.entities.vote import Vote
from pulse_board.domain.ports.vote_repository_port import VoteRepository
from pulse_board.infrastructure.database.models.vote_model import (
    VoteModel,
)


class SQLAlchemyVoteRepository(VoteRepository):
    """PostgreSQL-backed vote repository."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(self, vote: Vote) -> Vote:
        """Persist a new or updated vote.

        Uses session.merge for upsert-like behaviour so the
        same call handles both inserts and updates.
        """
        with self._session_factory() as session:
            model = self._to_model(vote)
            merged = session.merge(model)
            session.commit()
            session.refresh(merged)
            return self._to_entity(merged)

    def find_by_topic_and_fingerprint(
        self,
        topic_id: uuid.UUID,
        fingerprint_id: str,
    ) -> Vote | None:
        """Look up a vote by topic and fingerprint."""
        with self._session_factory() as session:
            model = (
                session.query(VoteModel)
                .filter(
                    VoteModel.topic_id == topic_id,
                    VoteModel.fingerprint_id == fingerprint_id,
                )
                .first()
            )
            return self._to_entity(model) if model else None

    def delete(self, vote_id: uuid.UUID) -> None:
        """Remove a vote by its unique identifier."""
        with self._session_factory() as session:
            model = session.get(VoteModel, vote_id)
            if model:
                session.delete(model)
                session.commit()

    def count_by_topic(self, topic_id: uuid.UUID) -> int:
        """Count total votes for a topic."""
        with self._session_factory() as session:
            return (
                session.query(VoteModel).filter(VoteModel.topic_id == topic_id).count()
            )

    @staticmethod
    def _to_model(entity: Vote) -> VoteModel:
        return VoteModel(
            id=entity.id,
            topic_id=entity.topic_id,
            fingerprint_id=entity.fingerprint_id,
            value=entity.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def _to_entity(model: VoteModel) -> Vote:
        return Vote(
            id=model.id,
            topic_id=model.topic_id,
            fingerprint_id=model.fingerprint_id,
            value=model.value,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
