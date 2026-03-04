"""
Text Chunker — Split document text into overlapping chunks for RAG retrieval.

Strategy:
  - Chunk size: 800 characters (configurable via settings)
  - Overlap: 120 characters (configurable via settings)
  - Splits on: paragraphs → sentences → clauses → words (semantic priority)
  - Each chunk retains its source page number and global chunk_index
  - Chunks are prefixed with [Page N] for LLM context awareness
  - Tiny fragments (< 50 chars) are discarded
"""

import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.helpers.config import settings

# ── Constants ────────────────────────────────────────────────────────────────
MIN_CHUNK_LENGTH = 50

SEPARATORS = [
    "\n\n",
    "\n",
    ". ",
    "? ",
    "! ",
    "; ",
    ": ",
    " ",
    "",
]


def _normalize_text(text: str) -> str:
    """Light normalization: collapse whitespace, normalize line breaks."""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_document(pages: list[dict]) -> list[dict]:
    """
    Split document pages into overlapping chunks.

    Args:
        pages: [{"page": 1, "text": "..."}, ...]

    Returns:
        [
            {"content": "[Page 1] ...", "page_number": 1, "chunk_index": 0},
            {"content": "[Page 1] ...", "page_number": 1, "chunk_index": 1},
            {"content": "[Page 2] ...", "page_number": 2, "chunk_index": 2},
            ...
        ]
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )

    chunks: list[dict] = []
    chunk_index = 0

    for page_data in pages:
        page_text = page_data.get("text")
        page_num = page_data.get("page")

        # Skip invalid or empty pages
        if not page_text or not page_num:
            continue
        if not page_text.strip():
            continue

        normalized = _normalize_text(page_text)
        page_chunks = splitter.split_text(normalized)

        # Clean and filter in one pass
        clean_chunks = list(map(str.strip, page_chunks))

        for chunk_text in clean_chunks:
            if chunk_text and len(chunk_text) >= MIN_CHUNK_LENGTH:
                chunks.append(
                    {
                        "content": f"[Page {page_num}] {chunk_text}",
                        "page_number": page_num,
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1

    return chunks
