"""Tests for centralized domain exception handlers."""

from unittest.mock import MagicMock, patch

import pytest

from pulse_board.domain.exceptions import (
    CodeGenerationError,
    DomainError,
    DuplicateVoteError,
    EntityNotFoundError,
    EventNotActiveError,
    EventNotFoundError,
    ValidationError,
)
from pulse_board.presentation.api.exception_handlers import (
    DOMAIN_EXCEPTION_STATUS_MAP,
    _domain_error_handler,
    register_exception_handlers,
)


class _UnmappedDomainError(DomainError):
    """A DomainError subclass not in DOMAIN_EXCEPTION_STATUS_MAP."""


MOCK_REQUEST = MagicMock()


class TestDomainErrorHandler:
    """Tests for the _domain_error_handler function."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("exception_class", "expected_status"),
        [
            (ValidationError, 422),
            (EntityNotFoundError, 404),
            (EventNotFoundError, 404),
            (EventNotActiveError, 409),
            (DuplicateVoteError, 409),
            (CodeGenerationError, 500),
        ],
        ids=[
            "validation_error_422",
            "entity_not_found_404",
            "event_not_found_404",
            "event_not_active_409",
            "duplicate_vote_409",
            "code_generation_500",
        ],
    )
    async def test_mapped_exception_returns_correct_status(
        self,
        exception_class: type[DomainError],
        expected_status: int,
    ) -> None:
        """Each mapped exception should return its configured
        HTTP status code and detail message."""
        msg = f"test {exception_class.__name__}"
        exc = exception_class(msg)

        response = await _domain_error_handler(MOCK_REQUEST, exc)

        assert response.status_code == expected_status
        assert response.body == (b'{"detail":"' + msg.encode() + b'"}')

    @pytest.mark.asyncio
    async def test_unmapped_domain_error_falls_back_to_500(
        self,
    ) -> None:
        """A DomainError subclass not in the map should get 500."""
        exc = _UnmappedDomainError("something unexpected")

        response = await _domain_error_handler(MOCK_REQUEST, exc)

        assert response.status_code == 500
        assert response.body == (b'{"detail":"something unexpected"}')

    @pytest.mark.asyncio
    async def test_500_error_logs_via_logger_error(self) -> None:
        """500-level errors must be logged with logger.error."""
        exc = CodeGenerationError("generation failed")

        with patch(
            "pulse_board.presentation.api.exception_handlers.logger",
        ) as mock_logger:
            await _domain_error_handler(MOCK_REQUEST, exc)

        mock_logger.error.assert_called_once_with(
            "Domain error: %s",
            "generation failed",
            exc_info=True,
        )

    @pytest.mark.asyncio
    async def test_unmapped_error_logs_via_logger_error(
        self,
    ) -> None:
        """Unmapped errors (defaulting to 500) must also log."""
        exc = _UnmappedDomainError("unknown failure")

        with patch(
            "pulse_board.presentation.api.exception_handlers.logger",
        ) as mock_logger:
            await _domain_error_handler(MOCK_REQUEST, exc)

        mock_logger.error.assert_called_once_with(
            "Domain error: %s",
            "unknown failure",
            exc_info=True,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "exception_class",
        [
            ValidationError,
            EntityNotFoundError,
            EventNotFoundError,
            EventNotActiveError,
            DuplicateVoteError,
        ],
        ids=[
            "validation_error",
            "entity_not_found",
            "event_not_found",
            "event_not_active",
            "duplicate_vote",
        ],
    )
    async def test_non_500_errors_do_not_log(
        self,
        exception_class: type[DomainError],
    ) -> None:
        """Non-500 errors must not trigger logger.error."""
        exc = exception_class("client error")

        with patch(
            "pulse_board.presentation.api.exception_handlers.logger",
        ) as mock_logger:
            await _domain_error_handler(MOCK_REQUEST, exc)

        mock_logger.error.assert_not_called()


class TestRegisterExceptionHandlers:
    """Tests for the register_exception_handlers function."""

    def test_registers_all_handlers(self) -> None:
        """Should register one handler per mapped exception
        plus one for the base DomainError."""
        app = MagicMock()

        register_exception_handlers(app)

        mapped_count = len(DOMAIN_EXCEPTION_STATUS_MAP)
        expected_total = mapped_count + 1  # +1 for DomainError
        assert app.add_exception_handler.call_count == (expected_total)

    def test_registers_each_mapped_exception_type(self) -> None:
        """Every exception in the map should be registered."""
        app = MagicMock()

        register_exception_handlers(app)

        registered_types = [
            call.args[0] for call in app.add_exception_handler.call_args_list
        ]
        for exc_type in DOMAIN_EXCEPTION_STATUS_MAP:
            assert exc_type in registered_types

    def test_registers_base_domain_error(self) -> None:
        """The base DomainError must also be registered."""
        app = MagicMock()

        register_exception_handlers(app)

        registered_types = [
            call.args[0] for call in app.add_exception_handler.call_args_list
        ]
        assert DomainError in registered_types

    def test_all_handlers_point_to_domain_error_handler(
        self,
    ) -> None:
        """Every registered handler should be
        _domain_error_handler."""
        app = MagicMock()

        register_exception_handlers(app)

        for call in app.add_exception_handler.call_args_list:
            handler = call.args[1]
            assert handler is _domain_error_handler
