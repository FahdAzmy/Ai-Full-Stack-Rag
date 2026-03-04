"""
Embedding Service — Generate vector embeddings via OpenRouter.

OpenRouter provides an OpenAI-compatible API, so we use the openai SDK
with a custom base_url pointing to OpenRouter.

Model: openai/text-embedding-3-small
Dimensions: 1536
Max batch size: 100 texts per API call
Retry: 3 attempts with exponential backoff (1s → 2s → 4s)
"""

import re
import time
import logging
from openai import OpenAI
from src.helpers.config import settings

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
    timeout=30.0,
)

# ── Constants ────────────────────────────────────────────────────────────────
BATCH_SIZE = 100
MAX_RETRIES = 3
MAX_TEXT_LENGTH = 8000


def _normalize_text(text: str) -> str:
    """Normalize text for embedding: collapse whitespace, strip."""
    text = text.replace("\n", " ")
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _truncate_text(text: str) -> str:
    """Truncate text to MAX_TEXT_LENGTH characters."""
    if len(text) > MAX_TEXT_LENGTH:
        return text[:MAX_TEXT_LENGTH]
    return text


def _sanitize_texts(texts: list[str]) -> list[str]:
    """Validate, normalize, and truncate input texts."""
    cleaned: list[str] = []
    for t in texts:
        if t is None:
            continue
        stripped = t.strip()
        if not stripped:
            continue
        normalized = _normalize_text(stripped)
        truncated = _truncate_text(normalized)
        cleaned.append(truncated)
    return cleaned


def _call_with_retry(batch: list[str]) -> list[list[float]]:
    """Call the embedding API with exponential backoff retry."""
    last_exception: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=batch,
                dimensions=settings.EMBEDDING_DIMENSIONS,
            )

            if not response.data:
                raise ValueError("API returned empty embeddings response.")

            # Sort by index to maintain input order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]

        except Exception as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                delay = 2**attempt  # 1s, 2s, 4s
                logger.warning(
                    "Embedding API call failed (attempt %d/%d): %s. "
                    "Retrying in %ds...",
                    attempt + 1,
                    MAX_RETRIES,
                    str(e),
                    delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "Embedding API call failed after %d attempts: %s",
                    MAX_RETRIES,
                    str(e),
                )

    raise last_exception  # type: ignore[misc]


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each is a list of floats).

    Raises:
        Exception: If the OpenRouter API call fails after retries.
        ValueError: If the API returns an empty response.
    """
    if not texts:
        return []

    clean_texts = _sanitize_texts(texts)
    if not clean_texts:
        return []

    all_embeddings: list[list[float]] = []

    for i in range(0, len(clean_texts), BATCH_SIZE):
        batch = clean_texts[i : i + BATCH_SIZE]
        logger.info("Processing embedding batch: %d texts", len(batch))

        batch_embeddings = _call_with_retry(batch)
        all_embeddings.extend(batch_embeddings)

        logger.info("Generated %d embeddings", len(batch_embeddings))

    return all_embeddings


def generate_single_embedding(text: str) -> list[float]:
    """
    Generate embedding for a single text.
    Convenience wrapper for queries.

    Raises:
        ValueError: If no embedding is returned.
    """
    result = generate_embeddings([text])
    if not result:
        raise ValueError("Failed to generate embedding for the provided text.")
    return result[0]
