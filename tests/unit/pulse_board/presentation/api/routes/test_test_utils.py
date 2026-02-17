"""Tests for the test reset endpoint security guards."""

from unittest.mock import MagicMock, patch

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from pulse_board.presentation.api.routes.test_utils import router


def _create_test_app() -> TestClient:
    """Create a minimal test app with the test router."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


_SETTINGS_PATH = "pulse_board.presentation.api.routes.test_utils.get_settings"
_SESSION_FACTORY_PATH = (
    "pulse_board.presentation.api.routes.test_utils.get_session_factory"
)


class TestResetEndpointProductionGuard:
    """Tests for production database detection."""

    @patch(_SESSION_FACTORY_PATH)
    @patch(_SETTINGS_PATH)
    def test_blocks_rds_database(
        self,
        mock_gs: MagicMock,
        mock_sf: MagicMock,
    ) -> None:
        """Should return 403 for RDS database URLs."""
        mock_gs.return_value.effective_database_url = (
            "postgresql://user:pass@mydb.rds.amazonaws.com:5432/prod"
        )
        mock_gs.return_value.test_mode_secret = ""
        client = _create_test_app()

        response = client.post("/api/test/reset")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_sf.assert_not_called()

    @patch(_SESSION_FACTORY_PATH)
    @patch(_SETTINGS_PATH)
    def test_blocks_production_in_url(
        self,
        mock_gs: MagicMock,
        mock_sf: MagicMock,
    ) -> None:
        """Should return 403 when URL contains 'production'."""
        mock_gs.return_value.effective_database_url = (
            "postgresql://user:pass@production-db:5432/app"
        )
        mock_gs.return_value.test_mode_secret = ""
        client = _create_test_app()

        response = client.post("/api/test/reset")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch(_SESSION_FACTORY_PATH)
    @patch(_SETTINGS_PATH)
    def test_blocks_prod_db_in_url(
        self,
        mock_gs: MagicMock,
        mock_sf: MagicMock,
    ) -> None:
        """Should return 403 when URL contains 'prod-db'."""
        mock_gs.return_value.effective_database_url = (
            "postgresql://user:pass@prod-db:5432/app"
        )
        mock_gs.return_value.test_mode_secret = ""
        client = _create_test_app()

        response = client.post("/api/test/reset")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestResetEndpointTokenGuard:
    """Tests for X-Test-Token header validation."""

    @patch(_SESSION_FACTORY_PATH)
    @patch(_SETTINGS_PATH)
    def test_rejects_missing_token(
        self,
        mock_gs: MagicMock,
        mock_sf: MagicMock,
    ) -> None:
        """Should return 403 when token is required but missing."""
        mock_gs.return_value.effective_database_url = "postgresql://localhost/test"
        mock_gs.return_value.test_mode_secret = "my-secret"
        client = _create_test_app()

        response = client.post("/api/test/reset")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch(_SESSION_FACTORY_PATH)
    @patch(_SETTINGS_PATH)
    def test_rejects_wrong_token(
        self,
        mock_gs: MagicMock,
        mock_sf: MagicMock,
    ) -> None:
        """Should return 403 when token does not match secret."""
        mock_gs.return_value.effective_database_url = "postgresql://localhost/test"
        mock_gs.return_value.test_mode_secret = "my-secret"
        client = _create_test_app()

        response = client.post(
            "/api/test/reset",
            headers={"X-Test-Token": "wrong-token"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch(_SESSION_FACTORY_PATH)
    @patch(_SETTINGS_PATH)
    def test_accepts_correct_token(
        self,
        mock_gs: MagicMock,
        mock_sf: MagicMock,
    ) -> None:
        """Should return 200 when correct token is provided."""
        mock_gs.return_value.effective_database_url = "postgresql://localhost/test"
        mock_gs.return_value.test_mode_secret = "my-secret"
        mock_session = MagicMock()
        mock_sf.return_value.return_value = mock_session
        client = _create_test_app()

        response = client.post(
            "/api/test/reset",
            headers={"X-Test-Token": "my-secret"},
        )

        assert response.status_code == status.HTTP_200_OK

    @patch(_SESSION_FACTORY_PATH)
    @patch(_SETTINGS_PATH)
    def test_allows_request_when_no_secret_configured(
        self,
        mock_gs: MagicMock,
        mock_sf: MagicMock,
    ) -> None:
        """Should skip token check when no secret is configured."""
        mock_gs.return_value.effective_database_url = "postgresql://localhost/test"
        mock_gs.return_value.test_mode_secret = ""
        mock_session = MagicMock()
        mock_sf.return_value.return_value = mock_session
        client = _create_test_app()

        response = client.post("/api/test/reset")

        assert response.status_code == status.HTTP_200_OK
