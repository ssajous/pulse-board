"""Integration test fixtures."""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from pulse_board.infrastructure.database.base import Base

_DEFAULT_DATABASE_URL = (
    "postgresql+psycopg2://pulse:pulse_dev_password@localhost:5433/pulse_board"
)


@pytest.fixture(scope="session")
def integration_engine() -> Engine:
    """Create a test database engine."""
    url = os.environ.get("DATABASE_URL", _DEFAULT_DATABASE_URL)
    return create_engine(url)


@pytest.fixture(scope="session")
def create_tables(integration_engine: Engine) -> None:
    """Create all tables for the test session."""
    Base.metadata.create_all(integration_engine)


@pytest.fixture(scope="session")
def integration_session_factory(
    integration_engine: Engine, create_tables: None
) -> sessionmaker:
    """Provide a session factory bound to the test engine."""
    return sessionmaker(bind=integration_engine)


@pytest.fixture
def cleanup_topics(integration_session_factory: sessionmaker):  # type: ignore[type-arg]
    """Delete all topics after each test."""
    yield
    with integration_session_factory() as session:
        session.execute(text("DELETE FROM topics"))
        session.commit()
