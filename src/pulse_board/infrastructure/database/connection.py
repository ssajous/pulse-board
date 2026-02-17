"""Database connection management."""

from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from pulse_board.domain.ports.database_port import DatabasePort
from pulse_board.infrastructure.config.settings import get_settings


class SQLAlchemyDatabase(DatabasePort):
    """SQLAlchemy implementation of the database port."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def is_connected(self) -> bool:
        """Check if the database connection is active."""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False


@lru_cache(maxsize=1)
def get_database() -> SQLAlchemyDatabase:
    """Get cached database instance."""
    settings = get_settings()
    engine = create_engine(settings.effective_database_url)
    return SQLAlchemyDatabase(engine)
