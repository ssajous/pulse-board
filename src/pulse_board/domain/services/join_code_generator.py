"""Join code generator — domain service for creating unique codes."""

import secrets
from collections.abc import Callable

from pulse_board.domain.exceptions import CodeGenerationError

MAX_RETRIES = 10
CODE_RANGE_MIN = 100000
CODE_RANGE_MAX = 999999


class JoinCodeGenerator:
    """Generates unique 6-digit numeric join codes for events.

    The generator relies on a caller-provided uniqueness check
    (typically backed by the repository) to ensure no collisions.
    """

    def generate(
        self,
        is_code_unique: Callable[[str], bool],
    ) -> str:
        """Generate a unique 6-digit join code.

        Uses cryptographically secure random numbers to
        produce codes in the range 100000-999999. Retries
        up to 10 times if collisions are detected.

        Args:
            is_code_unique: A callable that returns True if
                the given code string is not already in use.

        Returns:
            A unique 6-digit numeric string.

        Raises:
            CodeGenerationError: If a unique code cannot be
                generated within the retry limit.
        """
        for _ in range(MAX_RETRIES):
            code = str(
                secrets.randbelow(CODE_RANGE_MAX - CODE_RANGE_MIN + 1) + CODE_RANGE_MIN
            )
            if is_code_unique(code):
                return code

        raise CodeGenerationError(
            f"Failed to generate a unique join code after {MAX_RETRIES} attempts"
        )
