"""
Citation Controller — Business logic for the Citation Engine (SPEC-06).

Handles:
  - Getting citations for a specific message
  - Exporting citations in various formats (APA, MLA, BibTeX)
  - User isolation (users can only access their own messages)
"""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_scheams.Message import Message
from src.models.db_scheams.Chat import Chat
from src.models.db_scheams.user import User
from src.services.citation_service import CitationGenerator
from src.helpers.logging_config import get_logger

logger = get_logger("citation.controller")


async def _get_message_with_auth(
    message_id: str,
    current_user: User,
    db: AsyncSession,
) -> Message:
    """
    Fetch a message and verify the current user owns the chat it belongs to.

    Raises:
        HTTPException 404: Message not found
        HTTPException 403: User doesn't own the chat
    """
    # Validate UUID format
    try:
        msg_uuid = uuid.UUID(str(message_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid message ID format.",
        )

    # Fetch the message
    result = await db.execute(select(Message).where(Message.id == msg_uuid))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found.",
        )

    # Fetch the chat to check ownership
    chat_result = await db.execute(select(Chat).where(Chat.id == message.chat_id))
    chat = chat_result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found.",
        )

    if str(chat.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You do not own this chat.",
        )

    return message


def _deduplicate_by_document(source_chunks: list) -> list:
    """
    Deduplicate source chunks by document_id.
    Keeps the first chunk from each document (highest relevance).
    If a chunk has no document_id, it is kept as-is (treated as unique).
    """
    seen_doc_ids: set = set()
    unique_chunks: list = []

    for chunk in source_chunks:
        doc_id = chunk.get("document_id")
        if doc_id and doc_id in seen_doc_ids:
            continue  # Skip duplicate document
        if doc_id:
            seen_doc_ids.add(doc_id)
        unique_chunks.append(chunk)

    return unique_chunks


def _build_citations(source_chunks: list) -> list:
    """
    Build citation list from source_chunks stored in a message.
    Deduplicates by document_id — multiple chunks from the same document
    produce only one citation.
    """
    unique_chunks = _deduplicate_by_document(source_chunks)

    citations = []
    for chunk in unique_chunks:
        metadata = {
            "author": chunk.get("author", ""),
            "year": chunk.get("year", ""),
            "title": chunk.get("title", ""),
            "journal": chunk.get("journal", ""),
            "doi": chunk.get("doi", ""),
        }

        formats = CitationGenerator.generate_all_formats(metadata)

        citations.append({
            "source_number": chunk.get("source_number"),
            "title": chunk.get("title", ""),
            "author": chunk.get("author", ""),
            "year": chunk.get("year", ""),
            "page_number": chunk.get("page_number"),
            "formats": formats,
        })

    return citations


async def get_message_citations(
    message_id: str,
    current_user: User,
    db: AsyncSession,
    citation_format: Optional[str] = None,
) -> dict:
    """
    Get citations for all sources used in a specific message.

    Args:
        message_id: UUID of the message
        current_user: Authenticated user
        db: Database session
        citation_format: Optional specific format (apa, mla, bibtex)

    Returns:
        Dict with message_id and list of citations with format data
    """
    message = await _get_message_with_auth(message_id, current_user, db)

    source_chunks = message.source_chunks or []
    if not source_chunks:
        return {
            "message_id": str(message.id),
            "citations": [],
        }

    citations = _build_citations(source_chunks)

    return {
        "message_id": str(message.id),
        "citations": citations,
    }


def _ensure_unique_bibtex_keys(entries: list[str]) -> list[str]:
    """
    Ensure all BibTeX entries have unique keys.
    If collisions are detected, append a/b/c/... suffixes.
    """
    import re

    # Extract keys from entries
    key_pattern = re.compile(r'@\w+\{(\w+),')
    keys = []
    for entry in entries:
        match = key_pattern.search(entry)
        keys.append(match.group(1) if match else "")

    # Find colliding keys
    key_counts: dict[str, int] = {}
    for key in keys:
        key_counts[key] = key_counts.get(key, 0) + 1

    # For colliding keys, assign suffixes a, b, c, ...
    key_suffix_tracker: dict[str, int] = {}
    result_entries = []
    for i, entry in enumerate(entries):
        original_key = keys[i]
        if key_counts.get(original_key, 0) > 1:
            # This key has collisions — assign suffix
            suffix_idx = key_suffix_tracker.get(original_key, 0)
            suffix = chr(ord('a') + suffix_idx)
            new_key = f"{original_key}{suffix}"
            key_suffix_tracker[original_key] = suffix_idx + 1
            # Replace the key in the entry
            entry = entry.replace(f"{original_key},", f"{new_key},", 1)
        result_entries.append(entry)

    return result_entries


async def export_citations(
    message_id: str,
    citation_format: str,
    current_user: User,
    db: AsyncSession,
) -> str:
    """
    Export citations for a message in a specific format as plain text.

    Args:
        message_id: UUID of the message
        citation_format: Format to export (apa, mla, bibtex)
        current_user: Authenticated user
        db: Database session

    Returns:
        Plain text string of formatted citations
    """
    message = await _get_message_with_auth(message_id, current_user, db)

    source_chunks = message.source_chunks or []
    if not source_chunks:
        return ""

    # Deduplicate by document_id
    unique_chunks = _deduplicate_by_document(source_chunks)

    lines = []
    for chunk in unique_chunks:
        metadata = {
            "author": chunk.get("author", ""),
            "year": chunk.get("year", ""),
            "title": chunk.get("title", ""),
            "journal": chunk.get("journal", ""),
            "doi": chunk.get("doi", ""),
        }

        if citation_format == "apa":
            lines.append(CitationGenerator.apa_reference(metadata))
        elif citation_format == "mla":
            lines.append(CitationGenerator.mla_reference(metadata))
        elif citation_format == "bibtex":
            lines.append(CitationGenerator.bibtex_entry(metadata))

    # Ensure unique BibTeX keys
    if citation_format == "bibtex":
        lines = _ensure_unique_bibtex_keys(lines)

    separator = "\n\n" if citation_format == "bibtex" else "\n"
    return separator.join(lines)
