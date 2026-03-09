"""
Service Protocols — Abstract contracts for SOLID dependency inversion.

These Protocol classes define the interfaces that services must satisfy.
They allow the ingestion pipeline (and tests) to depend on abstractions
rather than concrete implementations, enabling:
  - Swapping implementations (e.g., different PDF parsers or embedders)
  - Easier unit testing with mock implementations
  - Clearer architectural boundaries

Usage:
    class MyCustomEmbedder:
        def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
            ...  # Custom implementation

    pipeline = IngestionPipeline(
        document_id="...",
        db=session,
        embedder=MyCustomEmbedder(),
    )
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class PDFParserProtocol(Protocol):
    """Contract for PDF text and metadata extraction."""

    def extract_text(self, file_path: str) -> list[dict]:
        """Extract text page-by-page from a PDF.

        Returns:
            [{"page": 1, "text": "..."}, ...]
        """
        ...

    def extract_metadata(self, file_path: str) -> dict:
        """Extract metadata from a PDF.

        Returns:
            {"title": str|None, "author": str|None, "year": str|None, "total_pages": int}
        """
        ...


@runtime_checkable
class TextChunkerProtocol(Protocol):
    """Contract for splitting document pages into chunks."""

    def chunk(self, pages: list[dict]) -> list[dict]:
        """Split pages into overlapping chunks.

        Args:
            pages: [{"page": 1, "text": "..."}, ...]

        Returns:
            [{"content": "...", "page_number": 1, "chunk_index": 0}, ...]
        """
        ...


@runtime_checkable
class EmbedderProtocol(Protocol):
    """Contract for generating vector embeddings."""

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        ...

    def generate_single_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        ...


# ── Chat System Protocols (SPEC-05) ─────────────────────────────────────────


@runtime_checkable
class LLMProtocol(Protocol):
    """Contract for LLM answer generation."""

    async def generate_answer(self, messages: list[dict]) -> str:
        """Generate a complete answer from the LLM."""
        ...

    async def generate_title(self, question: str) -> str:
        """Generate a short chat title from a question."""
        ...


@runtime_checkable
class ContextBuilderProtocol(Protocol):
    """Contract for assembling LLM prompts from retrieved chunks."""

    def build_prompt(
        self,
        question: str,
        retrieved_chunks: list[dict],
        conversation_history: list[dict] | None = None,
    ) -> list[dict]:
        """Build an OpenAI-compatible message list."""
        ...

    def get_source_summary(self, chunks: list[dict]) -> list[dict]:
        """Create a concise summary of sources used."""
        ...


@runtime_checkable
class RetrievalProtocol(Protocol):
    """Contract for semantic search over document chunks."""

    async def search(
        self,
        query: str,
        user_id: str,
        db: object,
        top_k: int = 5,
        document_ids: list[str] | None = None,
    ) -> list[dict]:
        """Find the most relevant document chunks for a query."""
        ...
