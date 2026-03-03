"""SQLAlchemy implementation of the EventRepository port."""

import uuid

from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from pulse_board.domain.entities.event import Event, EventStatus
from pulse_board.domain.ports.event_repository_port import (
    EventRepository,
)
from pulse_board.infrastructure.database.models.event_model import (
    EventModel,
)


class SQLAlchemyEventRepository(EventRepository):
    """PostgreSQL-backed event repository."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(self, event: Event) -> Event:
        """Persist a new event."""
        with self._session_factory() as session:
            model = self._to_model(event)
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def get_by_id(self, id: uuid.UUID) -> Event | None:
        """Look up an event by its unique identifier."""
        with self._session_factory() as session:
            model = session.get(EventModel, id)
            return self._to_entity(model) if model else None

    def get_by_code(self, code: str) -> Event | None:
        """Look up an active event by its join code."""
        with self._session_factory() as session:
            model = (
                session.query(EventModel)
                .filter(
                    EventModel.code == code,
                    EventModel.status == EventStatus.ACTIVE.value,
                )
                .first()
            )
            return self._to_entity(model) if model else None

    def list_active(self) -> list[Event]:
        """Return all events with ACTIVE status."""
        with self._session_factory() as session:
            models = (
                session.query(EventModel)
                .filter(EventModel.status == EventStatus.ACTIVE.value)
                .all()
            )
            return [self._to_entity(m) for m in models]

    def update_status(
        self,
        id: uuid.UUID,
        status: EventStatus,
    ) -> Event | None:
        """Update the status of an existing event.

        Uses an atomic SQL UPDATE to avoid race conditions.
        """
        with self._session_factory() as session:
            result = session.execute(
                update(EventModel)
                .where(EventModel.id == id)
                .values(status=status.value)
            )
            session.commit()
            if result.rowcount == 0:  # type: ignore[union-attr]
                return None
            model = session.get(EventModel, id)
            return self._to_entity(model) if model else None

    def is_code_unique(self, code: str) -> bool:
        """Check whether a join code is not yet in use."""
        with self._session_factory() as session:
            exists = session.query(
                session.query(EventModel)
                .filter(
                    EventModel.code == code,
                    EventModel.status == EventStatus.ACTIVE.value,
                )
                .exists()
            ).scalar()
            return not exists

    @staticmethod
    def _to_model(entity: Event) -> EventModel:
        return EventModel(
            id=entity.id,
            title=entity.title,
            code=entity.code,
            description=entity.description,
            start_date=entity.start_date,
            end_date=entity.end_date,
            status=entity.status.value,
            created_at=entity.created_at,
            creator_fingerprint=entity.creator_fingerprint,
            creator_token=entity.creator_token,
        )

    @staticmethod
    def _to_entity(model: EventModel) -> Event:
        return Event(
            id=model.id,
            title=model.title,
            code=model.code,
            description=model.description,
            start_date=model.start_date,
            end_date=model.end_date,
            status=EventStatus(model.status),
            created_at=model.created_at,
            creator_fingerprint=model.creator_fingerprint,
            creator_token=model.creator_token,
        )
