"""SQLAlchemy ORM model for votes."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from pulse_board.infrastructure.database.base import Base


class VoteModel(Base):
    """ORM representation of a Vote entity."""

    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint(
            "topic_id",
            "fingerprint_id",
            name="uq_votes_topic_fingerprint",
        ),
        CheckConstraint(
            "value IN (-1, 1)",
            name="ck_votes_value",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fingerprint_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
