"""Tests for the JoinCodeGenerator domain service."""

import pytest

from pulse_board.domain.exceptions import CodeGenerationError
from pulse_board.domain.services.join_code_generator import (
    CODE_RANGE_MAX,
    CODE_RANGE_MIN,
    MAX_RETRIES,
    JoinCodeGenerator,
)


class TestJoinCodeGeneratorGenerate:
    """Tests for JoinCodeGenerator.generate."""

    def test_generates_six_digit_string(self) -> None:
        """Should return a 6-digit numeric string."""
        generator = JoinCodeGenerator()

        code = generator.generate(is_code_unique=lambda _: True)

        assert len(code) == 6
        assert code.isdigit()

    def test_generated_code_within_range(self) -> None:
        """Code numeric value should be between CODE_RANGE_MIN and CODE_RANGE_MAX."""
        generator = JoinCodeGenerator()

        code = generator.generate(is_code_unique=lambda _: True)

        assert CODE_RANGE_MIN <= int(code) <= CODE_RANGE_MAX

    def test_returns_first_unique_code(self) -> None:
        """Should return the code when is_code_unique returns True."""
        generator = JoinCodeGenerator()
        codes_checked: list[str] = []

        def track_uniqueness(code: str) -> bool:
            codes_checked.append(code)
            return True

        code = generator.generate(is_code_unique=track_uniqueness)

        assert len(codes_checked) == 1
        assert code == codes_checked[0]

    def test_retries_on_collision(self) -> None:
        """Should retry when is_code_unique returns False."""
        generator = JoinCodeGenerator()
        call_count = 0

        def unique_on_third(_code: str) -> bool:
            nonlocal call_count
            call_count += 1
            return call_count >= 3

        code = generator.generate(is_code_unique=unique_on_third)

        assert call_count == 3
        assert len(code) == 6

    def test_raises_after_max_retries_exhausted(self) -> None:
        """Should raise CodeGenerationError after MAX_RETRIES failed attempts."""
        generator = JoinCodeGenerator()

        with pytest.raises(CodeGenerationError, match=str(MAX_RETRIES)):
            generator.generate(is_code_unique=lambda _: False)

    def test_exactly_max_retries_attempts_before_failure(self) -> None:
        """Should attempt exactly MAX_RETRIES times before raising."""
        generator = JoinCodeGenerator()
        attempts = 0

        def always_collide(_code: str) -> bool:
            nonlocal attempts
            attempts += 1
            return False

        with pytest.raises(CodeGenerationError):
            generator.generate(is_code_unique=always_collide)

        assert attempts == MAX_RETRIES

    def test_succeeds_on_last_retry(self) -> None:
        """Should succeed if the last attempt (retry MAX_RETRIES) is unique."""
        generator = JoinCodeGenerator()
        call_count = 0

        def unique_on_last(_code: str) -> bool:
            nonlocal call_count
            call_count += 1
            return call_count == MAX_RETRIES

        code = generator.generate(is_code_unique=unique_on_last)

        assert call_count == MAX_RETRIES
        assert len(code) == 6

    def test_generates_different_codes_across_calls(self) -> None:
        """Multiple generate calls should very likely produce different codes."""
        generator = JoinCodeGenerator()
        codes = {generator.generate(is_code_unique=lambda _: True) for _ in range(50)}

        # With 900,000 possible codes, 50 calls should produce multiple unique values
        assert len(codes) > 1
