"""Tests for application settings."""

from pulse_board.infrastructure.config.settings import Settings


class TestSettings:
    """Tests for Settings configuration."""

    def test_default_values(self) -> None:
        """Should have sensible defaults."""
        settings = Settings(
            _env_file=None  # type: ignore[call-arg]
        )
        assert settings.postgres_user == "pulse"
        assert settings.postgres_db == "pulse_board"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000

    def test_effective_database_url_from_parts(self) -> None:
        """Should construct URL from individual components."""
        settings = Settings(
            postgres_user="testuser",
            postgres_password="testpass",
            postgres_host="testhost",
            postgres_port=5433,
            postgres_db="testdb",
            _env_file=None,  # type: ignore[call-arg]
        )
        expected = "postgresql+psycopg2://testuser:testpass@testhost:5433/testdb"
        assert settings.effective_database_url == expected

    def test_effective_database_url_explicit_override(self) -> None:
        """Should use explicit DATABASE_URL when provided."""
        settings = Settings(
            database_url="postgresql+psycopg2://explicit:url@host/db",
            _env_file=None,  # type: ignore[call-arg]
        )
        assert (
            settings.effective_database_url
            == "postgresql+psycopg2://explicit:url@host/db"
        )

    def test_cors_origins_default(self) -> None:
        """Should default to localhost origins."""
        settings = Settings(_env_file=None)  # type: ignore[call-arg]
        origins = settings.cors_origins.split(",")
        assert "http://localhost:5173" in origins
