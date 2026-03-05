"""
Embedding Service — Generate vector embeddings via OpenRouter.

Architecture:
  - EmbeddingService class: injectable, testable, SOLID-compliant
  - Module-level facade functions: backward-compatible entry points

The class accepts an OpenAI client via constructor injection (DIP),
making it easy to swap providers or mock in tests.

The module-level functions (generate_embeddings, generate_single_embedding)
delegate to a service instance constructed from module-level config,
preserving backward compatibility with existing code and tests.
"""

import time
import logging
from openai import OpenAI
from src.helpers.config import settings
from src.helpers.text_utils import sanitize_texts

logger = logging.getLogger(__name__)

# ── Module-level client (backward-compatible, mockable by tests) ─────────────
client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
    timeout=30.0,
)


class EmbeddingService:
    """
    Injectable embedding service with retry logic and batching.

    Args:
        client: OpenAI-compatible API client.
        model: Embedding model name (e.g., "openai/text-embedding-3-small").
        dimensions: Embedding vector dimensions (e.g., 1536).
        batch_size: Max texts per API call.
        max_retries: Number of retry attempts on failure.
        max_text_length: Max characters per text before truncation.
    """

    def __init__(
        self,
        client: OpenAI,
        model: str,
        dimensions: int,
        batch_size: int = 100,
        max_retries: int = 3,
        max_text_length: int = 8000,
    ):
        self._client = client
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._max_retries = max_retries
        self._max_text_length = max_text_length

    def _call_with_retry(self, batch: list[str]) -> list[list[float]]:
        """Call the embedding API with exponential backoff retry."""
        last_exception: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                response = self._client.embeddings.create(
                    model=self._model,
                    input=batch,
                    dimensions=self._dimensions,
                )

                if not response.data:
                    raise ValueError("API returned empty embeddings response.")

                # Sort by index to maintain input order
                sorted_data = sorted(response.data, key=lambda x: x.index)
                return [item.embedding for item in sorted_data]

            except Exception as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    delay = 2**attempt  # 1s, 2s, 4s
                    logger.warning(
                        "Embedding API call failed (attempt %d/%d): %s. "
                        "Retrying in %ds...",
                        attempt + 1,
                        self._max_retries,
                        str(e),
                        delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "Embedding API call failed after %d attempts: %s",
                        self._max_retries,
                        str(e),
                    )

        raise last_exception  # type: ignore[misc]

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Handles sanitization, batching, and retry internally.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each is a list of floats).

        Raises:
            Exception: If the API call fails after retries.
            ValueError: If the API returns an empty response.
        """
        if not texts:
            return []

        clean_texts = sanitize_texts(texts, self._max_text_length)
        if not clean_texts:
            return []

        all_embeddings: list[list[float]] = []

        for i in range(0, len(clean_texts), self._batch_size):
            batch = clean_texts[i : i + self._batch_size]
            logger.info("Processing embedding batch: %d texts", len(batch))

            batch_embeddings = self._call_with_retry(batch)
            all_embeddings.extend(batch_embeddings)

            logger.info("Generated %d embeddings", len(batch_embeddings))

        return all_embeddings

    def generate_single_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        Convenience wrapper for queries.

        Raises:
            ValueError: If no embedding is returned.
        """
        result = self.generate_embeddings([text])
        if not result:
            raise ValueError("Failed to generate embedding for the provided text.")
        return result[0]


# ═════════════════════════════════════════════════════════════════════════════
# Backward-compatible module-level functions
# ═════════════════════════════════════════════════════════════════════════════
# These facades construct a service instance using module-level variables
# (client, settings), which tests can mock via patch().


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Module-level facade for EmbeddingService.generate_embeddings."""
    service = EmbeddingService(
        client=client,
        model=settings.EMBEDDING_MODEL,
        dimensions=settings.EMBEDDING_DIMENSIONS,
    )
    return service.generate_embeddings(texts)


def generate_single_embedding(text: str) -> list[float]:
    """Module-level facade for EmbeddingService.generate_single_embedding."""
    service = EmbeddingService(
        client=client,
        model=settings.EMBEDDING_MODEL,
        dimensions=settings.EMBEDDING_DIMENSIONS,
    )
    return service.generate_single_embedding(text)
