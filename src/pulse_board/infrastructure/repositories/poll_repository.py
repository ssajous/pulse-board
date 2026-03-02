"""SQLAlchemy implementation of the PollRepository port."""

import uuid

from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from pulse_board.domain.entities.poll import Poll, PollOption
from pulse_board.domain.ports.poll_repository_port import PollRepository
from pulse_board.infrastructure.database.models.poll_model import (
    PollModel,
)


class SQLAlchemyPollRepository(PollRepository):
    """PostgreSQL-backed poll repository."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def create(self, poll: Poll) -> Poll:
        """Persist a new poll."""
        with self._session_factory() as session:
            model = self._to_model(poll)
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def save(self, poll: Poll) -> Poll:
        """Persist a new or updated poll."""
        with self._session_factory() as session:
            model = self._to_model(poll)
            merged = session.merge(model)
            session.commit()
            session.refresh(merged)
            return self._to_entity(merged)

    def get_by_id(self, id: uuid.UUID) -> Poll | None:
        """Look up a poll by its unique identifier."""
        with self._session_factory() as session:
            model = session.get(PollModel, id)
            return self._to_entity(model) if model else None

    def list_by_event(
        self,
        event_id: uuid.UUID,
    ) -> list[Poll]:
        """Return all polls belonging to a given event."""
        with self._session_factory() as session:
            models = (
                session.query(PollModel)
                .filter(PollModel.event_id == event_id)
                .order_by(PollModel.created_at)
                .all()
            )
            return [self._to_entity(m) for m in models]

    def update_active_status(
        self,
        id: uuid.UUID,
        is_active: bool,
    ) -> Poll | None:
        """Update the active status of a poll."""
        with self._session_factory() as session:
            result = session.execute(
                update(PollModel).where(PollModel.id == id).values(is_active=is_active)
            )
            session.commit()
            if result.rowcount == 0:  # type: ignore[union-attr]
                return None
            model = session.get(PollModel, id)
            return self._to_entity(model) if model else None

    def find_active_by_event(
        self,
        event_id: uuid.UUID,
    ) -> Poll | None:
        """Find the currently active poll for an event."""
        with self._session_factory() as session:
            model = (
                session.query(PollModel)
                .filter(
                    PollModel.event_id == event_id,
                    PollModel.is_active.is_(True),
                )
                .first()
            )
            return self._to_entity(model) if model else None

    @staticmethod
    def _to_model(entity: Poll) -> PollModel:
        return PollModel(
            id=entity.id,
            event_id=entity.event_id,
            question=entity.question,
            poll_type=entity.poll_type,
            options=[{"id": str(opt.id), "text": opt.text} for opt in entity.options],
            is_active=entity.is_active,
            created_at=entity.created_at,
        )

    @staticmethod
    def _to_entity(model: PollModel) -> Poll:
        raw_options: list[dict[str, str]] = model.options  # type: ignore[assignment]
        return Poll(
            id=model.id,
            event_id=model.event_id,
            question=model.question,
            poll_type=model.poll_type,
            options=[
                PollOption(
                    id=uuid.UUID(opt["id"]),
                    text=opt["text"],
                )
                for opt in raw_options
            ],
            is_active=model.is_active,
            created_at=model.created_at,
        )
