"""SQLAlchemy ORM model for poll responses."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from pulse_board.infrastructure.database.base import Base


class PollResponseModel(Base):
    """ORM representation of a PollResponse entity."""

    __tablename__ = "poll_responses"
    __table_args__ = (
        UniqueConstraint(
            "poll_id",
            "fingerprint_id",
            name="uq_poll_responses_poll_fingerprint",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    poll_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("polls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fingerprint_id: Mapped[str] = mapped_column(String(255), nullable=False)
    response_data: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSONB, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
