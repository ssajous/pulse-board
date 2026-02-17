"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Database
    postgres_user: str = "pulse"
    postgres_password: str = "pulse_dev_password"
    postgres_db: str = "pulse_board"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str | None = None

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    log_level: str = "INFO"

    # Security
    test_mode_secret: str = ""

    # WebSocket
    ws_max_size: int = 1024
    ws_max_connections: int = 1000
    ws_max_connections_per_ip: int = 10

    @property
    def allowed_ws_origins(self) -> set[str]:
        """Get the set of allowed WebSocket origins from cors_origins."""
        return {o.strip() for o in self.cors_origins.split(",")}

    @property
    def effective_database_url(self) -> str:
        """Get the database URL, constructing from parts if not explicitly set."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
