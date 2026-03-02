"""SQLAlchemy ORM model for polls."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from pulse_board.infrastructure.database.base import Base


class PollModel(Base):
    """ORM representation of a Poll entity."""

    __tablename__ = "polls"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    poll_type: Mapped[str] = mapped_column(String(50), nullable=False)
    options: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSONB, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
