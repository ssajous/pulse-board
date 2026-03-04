"""Word cloud normalization — domain service for text normalization."""

import re

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_word_cloud_text(raw: str) -> str:
    """Normalize a raw word cloud submission to a canonical form.

    Pipeline: strip leading/trailing whitespace → lowercase →
    collapse any internal whitespace run to a single space.

    Args:
        raw: The raw input string submitted by the participant.

    Returns:
        The normalized string ready for validation and storage.
    """
    stripped = raw.strip()
    lowered = stripped.lower()
    return _WHITESPACE_RE.sub(" ", lowered)
