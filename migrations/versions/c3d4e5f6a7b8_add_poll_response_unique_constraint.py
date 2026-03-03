"""add unique constraint on poll_responses (poll_id, fingerprint_id)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-02 16:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_poll_responses_poll_fingerprint",
        "poll_responses",
        ["poll_id", "fingerprint_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_poll_responses_poll_fingerprint",
        "poll_responses",
        type_="unique",
    )
