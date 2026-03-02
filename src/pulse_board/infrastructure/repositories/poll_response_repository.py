"""SQLAlchemy implementation of the PollResponseRepository port."""

import uuid
from collections import Counter

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from pulse_board.domain.entities.poll_response import PollResponse
from pulse_board.domain.exceptions import DuplicateResponseError
from pulse_board.domain.ports.poll_response_repository_port import (
    PollResponseRepository,
)
from pulse_board.infrastructure.database.models.poll_response_model import (
    PollResponseModel,
)


class SQLAlchemyPollResponseRepository(PollResponseRepository):
    """PostgreSQL-backed poll response repository."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def create(
        self,
        poll_response: PollResponse,
    ) -> PollResponse:
        """Persist a new poll response.

        Raises:
            DuplicateResponseError: If a unique constraint is
                violated due to a concurrent duplicate response.
        """
        with self._session_factory() as session:
            model = self._to_model(poll_response)
            session.add(model)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise DuplicateResponseError(
                    "A response already exists for this poll and fingerprint"
                ) from exc
            session.refresh(model)
            return self._to_entity(model)

    def list_by_poll(
        self,
        poll_id: uuid.UUID,
    ) -> list[PollResponse]:
        """Return all responses for a given poll."""
        with self._session_factory() as session:
            models = (
                session.query(PollResponseModel)
                .filter(PollResponseModel.poll_id == poll_id)
                .order_by(PollResponseModel.created_at)
                .all()
            )
            return [self._to_entity(m) for m in models]

    def find_by_poll_and_fingerprint(
        self,
        poll_id: uuid.UUID,
        fingerprint_id: str,
    ) -> PollResponse | None:
        """Look up a response by poll and fingerprint."""
        with self._session_factory() as session:
            model = (
                session.query(PollResponseModel)
                .filter(
                    PollResponseModel.poll_id == poll_id,
                    PollResponseModel.fingerprint_id == fingerprint_id,
                )
                .first()
            )
            return self._to_entity(model) if model else None

    def count_by_option(
        self,
        poll_id: uuid.UUID,
        option_id: uuid.UUID,
    ) -> int:
        """Count responses for a specific option."""
        responses = self.list_by_poll(poll_id)
        return sum(
            1 for r in responses if r.response_data.get("option_id") == str(option_id)
        )

    def count_all_by_poll(
        self,
        poll_id: uuid.UUID,
    ) -> dict[uuid.UUID, int]:
        """Count responses grouped by option for a poll.

        Queries all responses and aggregates in Python since
        JSONB grouping across databases is complex.
        """
        responses = self.list_by_poll(poll_id)
        counter: Counter[uuid.UUID] = Counter()
        for response in responses:
            option_id_str = response.response_data.get("option_id")
            if option_id_str:
                counter[uuid.UUID(option_id_str)] += 1
        return dict(counter)

    @staticmethod
    def _to_model(entity: PollResponse) -> PollResponseModel:
        return PollResponseModel(
            id=entity.id,
            poll_id=entity.poll_id,
            fingerprint_id=entity.fingerprint_id,
            response_data={
                "option_id": str(entity.option_id),
            },
            created_at=entity.created_at,
        )

    @staticmethod
    def _to_entity(model: PollResponseModel) -> PollResponse:
        raw_data: dict[str, str] = model.response_data  # type: ignore[assignment]
        option_id = uuid.UUID(raw_data["option_id"])
        return PollResponse(
            id=model.id,
            poll_id=model.poll_id,
            fingerprint_id=model.fingerprint_id,
            option_id=option_id,
            response_data=raw_data,
            created_at=model.created_at,
        )
