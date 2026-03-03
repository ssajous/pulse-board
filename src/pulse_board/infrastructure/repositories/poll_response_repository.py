"""SQLAlchemy implementation of the PollResponseRepository port."""

import uuid

from sqlalchemy import func
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
        return self.count_all_by_poll(poll_id).get(option_id, 0)

    def count_all_by_poll(
        self,
        poll_id: uuid.UUID,
    ) -> dict[uuid.UUID, int]:
        """Count responses grouped by option for a poll."""
        with self._session_factory() as session:
            option_id_col = PollResponseModel.response_data["option_id"].astext
            rows = (
                session.query(
                    option_id_col,
                    func.count(),
                )
                .filter(PollResponseModel.poll_id == poll_id)
                .filter(PollResponseModel.response_data.has_key("option_id"))  # type: ignore[attr-defined]
                .group_by(option_id_col)
                .all()
            )
            return {uuid.UUID(option_id_str): count for option_id_str, count in rows}

    def get_rating_aggregate(
        self,
        poll_id: uuid.UUID,
    ) -> tuple[float | None, dict[str, int]]:
        """Return (average_rating, distribution) for a rating poll.

        Args:
            poll_id: The UUID of the poll.

        Returns:
            A tuple of (average_rating, distribution) where
            average_rating is None when no responses exist and
            distribution maps rating string ("1"-"5") to count.
        """
        with self._session_factory() as session:
            rating_expr = PollResponseModel.response_data["rating"].astext
            rows = (
                session.query(rating_expr, func.count())
                .filter(PollResponseModel.poll_id == poll_id)
                .filter(PollResponseModel.response_data.has_key("rating"))  # type: ignore[attr-defined]
                .group_by(rating_expr)
                .all()
            )
            if not rows:
                return None, {}
            distribution = {str(r): int(c) for r, c in rows}
            total = sum(distribution.values())
            total_rating = sum(int(r) * int(c) for r, c in rows)
            avg = round(total_rating / total, 2) if total > 0 else None
            return avg, distribution

    def list_open_text_by_poll(
        self,
        poll_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[PollResponse], int]:
        """Return paginated open-text responses for a poll.

        Args:
            poll_id: The UUID of the poll.
            page: 1-based page number.
            page_size: Number of responses per page.

        Returns:
            A tuple of (responses, total_count) ordered newest first.
        """
        with self._session_factory() as session:
            base_query = (
                session.query(PollResponseModel)
                .filter(PollResponseModel.poll_id == poll_id)
                .filter(PollResponseModel.response_data.has_key("text"))  # type: ignore[attr-defined]
            )
            total = base_query.count()
            offset = (page - 1) * page_size
            models = (
                base_query.order_by(PollResponseModel.created_at.desc())
                .offset(offset)
                .limit(page_size)
                .all()
            )
            return [self._to_entity(m) for m in models], total

    @staticmethod
    def _to_model(entity: PollResponse) -> PollResponseModel:
        return PollResponseModel(
            id=entity.id,
            poll_id=entity.poll_id,
            fingerprint_id=entity.fingerprint_id,
            response_data=entity.response_data,
            created_at=entity.created_at,
        )

    @staticmethod
    def _to_entity(model: PollResponseModel) -> PollResponse:
        raw_data: dict[str, object] = model.response_data  # type: ignore[assignment]
        option_id_str = raw_data.get("option_id")
        option_id = uuid.UUID(str(option_id_str)) if option_id_str is not None else None
        return PollResponse(
            id=model.id,
            poll_id=model.poll_id,
            fingerprint_id=model.fingerprint_id,
            option_id=option_id,
            response_data=raw_data,
            created_at=model.created_at,
        )
