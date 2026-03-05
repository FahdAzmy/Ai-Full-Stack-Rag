"""
Text Utilities — Shared text processing functions.

Extracted from embedding_service.py to follow SRP.
These utilities are reusable across any service that needs
text normalization, truncation, or sanitization.
"""

import re


def normalize_for_embedding(text: str) -> str:
    """Normalize text for embedding: collapse all whitespace to single spaces.

    This is aggressive normalization — removes newlines entirely.
    For chunk-level normalization that preserves paragraph breaks,
    see chunker._normalize_text().
    """
    text = text.replace("\n", " ")
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def truncate_text(text: str, max_length: int = 8000) -> str:
    """Truncate text to max_length characters to prevent token limit errors."""
    if len(text) > max_length:
        return text[:max_length]
    return text


def sanitize_texts(texts: list[str], max_length: int = 8000) -> list[str]:
    """Validate, normalize, and truncate a list of texts.

    Removes None values, empty strings, and whitespace-only strings.
    Applies embedding normalization and truncation to each text.

    Args:
        texts: Raw input texts (may contain None or empty strings).
        max_length: Maximum character length per text.

    Returns:
        Cleaned list of non-empty, normalized, truncated texts.
    """
    cleaned: list[str] = []
    for t in texts:
        if t is None:
            continue
        stripped = t.strip()
        if not stripped:
            continue
        normalized = normalize_for_embedding(stripped)
        truncated = truncate_text(normalized, max_length)
        cleaned.append(truncated)
    return cleaned
