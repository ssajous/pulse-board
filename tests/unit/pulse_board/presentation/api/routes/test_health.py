"""Tests for the health check route."""

import pytest
from fastapi.testclient import TestClient

from pulse_board.application.use_cases.health_check import HealthCheckUseCase
from pulse_board.domain.ports.database_port import DatabasePort
from pulse_board.presentation.api.app import create_app
from pulse_board.presentation.api.dependencies import get_health_check_use_case


class FakeDatabaseConnected(DatabasePort):
    def is_connected(self) -> bool:
        return True


class FakeDatabaseDisconnected(DatabasePort):
    def is_connected(self) -> bool:
        return False


@pytest.fixture
def healthy_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_health_check_use_case] = lambda: HealthCheckUseCase(
        database=FakeDatabaseConnected()
    )
    return TestClient(app)


@pytest.fixture
def unhealthy_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_health_check_use_case] = lambda: HealthCheckUseCase(
        database=FakeDatabaseDisconnected()
    )
    return TestClient(app)


class TestHealthRoute:
    def test_health_returns_200_when_db_connected(
        self, healthy_client: TestClient
    ) -> None:
        response = healthy_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "database": "connected",
        }

    def test_health_returns_503_when_db_disconnected(
        self, unhealthy_client: TestClient
    ) -> None:
        response = unhealthy_client.get("/health")
        assert response.status_code == 503
        assert response.json() == {
            "status": "degraded",
            "database": "disconnected",
        }
