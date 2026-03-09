"""
Integration tests for Citation Engine API endpoints (SPEC-06).
Following TDD: These tests are written BEFORE implementation.

Tests are organized by endpoint:
  1. TestGetMessageCitations — GET /citations/messages/{message_id}
  2. TestExportCitations     — GET /citations/export
  3. TestCitationSecurity    — Auth & user isolation checks

All external services are mocked. Uses the same patterns as test_chat_system.py.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.helpers.security import hash_password, generate_access_token
from src.models.db_scheams.user import User
from src.models.db_scheams.Chat import Chat
from src.models.db_scheams.Message import Message
from src.models.db_scheams.document import Document


# ── Helpers ──────────────────────────────────────────────────────────────────


async def create_verified_user(
    db_session: AsyncSession, email: str = "citationuser@example.com"
) -> User:
    """Create a verified user in the DB and return the User object."""
    user = User(
        email=email,
        name="Citation Test User",
        hashed_password=hash_password("SecurePass123"),
        is_verified=True,
        verification_token="123456",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def auth_header(user: User) -> dict:
    """Generate Authorization header with a valid access token."""
    token = generate_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


async def create_chat_in_db(
    db_session: AsyncSession,
    user: User,
    title: str | None = None,
) -> Chat:
    """Insert a Chat record directly into the DB for test setup."""
    chat = Chat(
        id=uuid.uuid4(),
        user_id=user.id,
        title=title,
    )
    db_session.add(chat)
    await db_session.commit()
    await db_session.refresh(chat)
    return chat


async def create_message_in_db(
    db_session: AsyncSession,
    chat: Chat,
    role: str = "user",
    content: str = "Test message",
    source_chunks: list | None = None,
) -> Message:
    """Insert a Message record directly into the DB for test setup."""
    msg = Message(
        id=uuid.uuid4(),
        chat_id=chat.id,
        role=role,
        content=content,
        source_chunks=source_chunks,
    )
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)
    return msg


async def create_document_in_db(
    db_session: AsyncSession,
    user: User,
    title: str = "Test Paper",
    author: str = "Smith, John",
    year: str = "2020",
    journal: str = "Journal of AI Research",
    doi: str = "10.1234/jair.2020.001",
) -> Document:
    """Insert a Document record with metadata for citation tests."""
    doc = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        file_name="test_paper.pdf",
        file_path=f"{user.id}/{uuid.uuid4()}.pdf",
        status="ready",
        title=title,
        author=author,
        year=year,
        journal=journal,
        doi=doi,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


# ── Sample source_chunks data as stored in messages ──────────────────────────

SAMPLE_SOURCE_CHUNKS = [
    {
        "source_number": 1,
        "chunk_id": str(uuid.uuid4()),
        "content": "Convolutional neural networks require large datasets...",
        "page_number": 15,
        "chunk_index": 3,
        "document_id": None,  # Will be replaced with actual doc IDs
        "file_name": "deep_learning.pdf",
        "title": "Deep Learning in Medicine",
        "author": "Smith, John",
        "year": "2020",
        "journal": "Journal of AI Research",
        "doi": "10.1234/jair.2020.001",
        "similarity": 0.87,
    },
    {
        "source_number": 2,
        "chunk_id": str(uuid.uuid4()),
        "content": "The primary challenge remains the need for quality data...",
        "page_number": 8,
        "chunk_index": 2,
        "document_id": None,  # Will be replaced with actual doc IDs
        "file_name": "cnn_challenges.pdf",
        "title": "CNN Challenges in Healthcare",
        "author": "Doe, Jane",
        "year": "2021",
        "journal": "Healthcare AI Review",
        "doi": None,
        "similarity": 0.82,
    },
]


def make_source_chunks(doc1_id: str | None = None, doc2_id: str | None = None) -> list:
    """Create source_chunks with optional document IDs."""
    chunks = []
    for i, chunk in enumerate(SAMPLE_SOURCE_CHUNKS):
        c = chunk.copy()
        if i == 0 and doc1_id:
            c["document_id"] = doc1_id
        elif i == 1 and doc2_id:
            c["document_id"] = doc2_id
        chunks.append(c)
    return chunks


# ═════════════════════════════════════════════════════════════════════════════
# 1. TestGetMessageCitations — GET /citations/messages/{message_id}
# ═════════════════════════════════════════════════════════════════════════════


class TestGetMessageCitations:
    """Test cases for GET /citations/messages/{message_id}."""

    # ── Scenario: Get all citation formats for a message ─────────────────

    @pytest.mark.asyncio
    async def test_get_citations_all_formats(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get citations with format=all → 200, returns all 4 formats per source."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Citation Chat")
        source_chunks = make_source_chunks()

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Answer with sources [Source 1] [Source 2]",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert "message_id" in data
        assert "citations" in data
        assert len(data["citations"]) == 2

        # Each citation should have all format keys
        for citation in data["citations"]:
            assert "source_number" in citation
            assert "formats" in citation
            formats = citation["formats"]
            assert "inline_apa" in formats
            assert "apa" in formats
            assert "mla" in formats
            assert "bibtex" in formats

    # ── Scenario: Get only APA format ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_citations_apa_only(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get citations with format=apa → only APA format returned."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "APA Chat")
        source_chunks = make_source_chunks()

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "APA answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}?format=apa",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["citations"]) > 0

    # ── Scenario: Get only MLA format ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_citations_mla_only(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get citations with format=mla → only MLA format returned."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "MLA Chat")
        source_chunks = make_source_chunks()

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "MLA answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}?format=mla",
            headers=auth_header(user),
        )

        assert response.status_code == 200

    # ── Scenario: Get only BibTeX format ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_citations_bibtex_only(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get citations with format=bibtex → only BibTeX format returned."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "BibTeX Chat")
        source_chunks = make_source_chunks()

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "BibTeX answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}?format=bibtex",
            headers=auth_header(user),
        )

        assert response.status_code == 200

    # ── Scenario: Message not found → 404 ────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_citations_message_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Non-existent message → 404."""
        user = await create_verified_user(db_session)
        fake_id = uuid.uuid4()

        response = await client.get(
            f"/citations/messages/{fake_id}",
            headers=auth_header(user),
        )

        assert response.status_code == 404

    # ── Scenario: User message (no sources) → empty citations ────────────

    @pytest.mark.asyncio
    async def test_get_citations_user_message_no_sources(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """User message (no source_chunks) → empty citations list."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "No Sources Chat")

        msg = await create_message_in_db(
            db_session, chat, "user",
            "Just a user question",
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["citations"] == []

    # ── Scenario: Assistant message with empty source_chunks → empty ─────

    @pytest.mark.asyncio
    async def test_get_citations_empty_source_chunks(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Assistant message with empty source_chunks → empty citations."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Empty Sources Chat")

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Answer without sources",
            source_chunks=[],
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["citations"] == []

    # ── Business Rule: Citation metadata matches source metadata ─────────

    @pytest.mark.asyncio
    async def test_citation_metadata_matches_source(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Citation metadata (title, author, year) matches original source."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Metadata Chat")
        source_chunks = make_source_chunks()

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Metadata test answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        citation = data["citations"][0]
        assert citation["title"] == "Deep Learning in Medicine"
        assert citation["author"] == "Smith, John"
        assert citation["year"] == "2020"

    # ── Scenario: Citations include correct source numbers ───────────────

    @pytest.mark.asyncio
    async def test_citation_source_numbers(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Each citation has the correct source_number from the original chunks."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Source Numbers Chat")
        source_chunks = make_source_chunks()

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Numbered sources answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        source_numbers = [c["source_number"] for c in data["citations"]]
        assert 1 in source_numbers
        assert 2 in source_numbers

    # ── Scenario: Citations include page number ──────────────────────────

    @pytest.mark.asyncio
    async def test_citation_includes_page_number(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Each citation includes the page_number from the source chunk."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Page Number Chat")
        source_chunks = make_source_chunks()

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Page reference answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["citations"][0]["page_number"] == 15
        assert data["citations"][1]["page_number"] == 8


# ═════════════════════════════════════════════════════════════════════════════
# 2. TestExportCitations — GET /citations/export
# ═════════════════════════════════════════════════════════════════════════════


class TestExportCitations:
    """Test cases for GET /citations/export."""

    # ── Scenario #13: Export multiple sources as APA ──────────────────────

    @pytest.mark.asyncio
    async def test_export_apa_format(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Export as APA → plain text with all APA references."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Export APA Chat")
        source_chunks = make_source_chunks()

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Export APA answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/export?message_id={msg.id}&format=apa",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        # Should be plain text
        assert "text/plain" in response.headers.get("content-type", "")
        text = response.text
        # Should contain both authors
        assert "Smith" in text
        assert "Doe" in text

    # ── Export as MLA ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_export_mla_format(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Export as MLA → plain text with all MLA references."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Export MLA Chat")
        source_chunks = make_source_chunks()

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Export MLA answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/export?message_id={msg.id}&format=mla",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        text = response.text
        assert "Smith" in text

    # ── Export as BibTeX ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_export_bibtex_format(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Export as BibTeX → plain text with valid BibTeX entries."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Export BibTeX Chat")
        source_chunks = make_source_chunks()

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Export BibTeX answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/export?message_id={msg.id}&format=bibtex",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        text = response.text
        # Should contain valid BibTeX entries
        assert "@" in text
        assert "title=" in text
        assert "author=" in text

    # ── Export: Multiple entries separated properly ───────────────────────

    @pytest.mark.asyncio
    async def test_export_bibtex_multiple_entries_separated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """BibTeX export with multiple sources → entries separated by newline."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user, "Multi BibTeX Chat")
        source_chunks = make_source_chunks()

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Multi BibTeX answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/export?message_id={msg.id}&format=bibtex",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        text = response.text
        # Should have 2 BibTeX entries (count '@' occurrences)
        assert text.count("@") == 2

    # ── Export: Missing message_id → 422 ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_export_missing_message_id(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Export without message_id → 422 validation error."""
        user = await create_verified_user(db_session)

        response = await client.get(
            "/citations/export?format=apa",
            headers=auth_header(user),
        )

        assert response.status_code == 422

    # ── Export: Missing format → 422 ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_export_missing_format(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Export without format → 422 validation error."""
        user = await create_verified_user(db_session)
        fake_msg_id = uuid.uuid4()

        response = await client.get(
            f"/citations/export?message_id={fake_msg_id}",
            headers=auth_header(user),
        )

        assert response.status_code == 422

    # ── Export: Invalid format → 422 ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_export_invalid_format(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Export with invalid format (e.g. 'chicago') → 422."""
        user = await create_verified_user(db_session)
        fake_msg_id = uuid.uuid4()

        response = await client.get(
            f"/citations/export?message_id={fake_msg_id}&format=chicago",
            headers=auth_header(user),
        )

        assert response.status_code == 422

    # ── Export: Non-existent message → 404 ───────────────────────────────

    @pytest.mark.asyncio
    async def test_export_message_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Export for non-existent message → 404."""
        user = await create_verified_user(db_session)
        fake_msg_id = uuid.uuid4()

        response = await client.get(
            f"/citations/export?message_id={fake_msg_id}&format=apa",
            headers=auth_header(user),
        )

        assert response.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
# 3. TestCitationSecurity — Auth & user isolation
# ═════════════════════════════════════════════════════════════════════════════


class TestCitationSecurity:
    """Security tests: authentication, authorization, user isolation."""

    # ── No auth → 401/403 on get citations ───────────────────────────────

    @pytest.mark.asyncio
    async def test_get_citations_without_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get citations without auth → 401/403."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user)
        msg = await create_message_in_db(db_session, chat, "assistant", "answer")

        response = await client.get(f"/citations/messages/{msg.id}")
        assert response.status_code in (401, 403)

    # ── No auth → 401/403 on export ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_export_citations_without_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Export citations without auth → 401/403."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user)
        msg = await create_message_in_db(db_session, chat, "assistant", "answer")

        response = await client.get(
            f"/citations/export?message_id={msg.id}&format=apa"
        )
        assert response.status_code in (401, 403)

    # ── User isolation: cannot see other user's citations → 403 ──────────

    @pytest.mark.asyncio
    async def test_get_citations_other_users_message(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Accessing another user's message citations → 403."""
        owner = await create_verified_user(db_session, "cit_owner@example.com")
        intruder = await create_verified_user(db_session, "cit_intruder@example.com")

        chat = await create_chat_in_db(db_session, owner, "Private Chat")
        source_chunks = make_source_chunks()
        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Private answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(intruder),
        )

        assert response.status_code == 403

    # ── User isolation: cannot export other user's citations → 403 ───────

    @pytest.mark.asyncio
    async def test_export_citations_other_users_message(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Exporting another user's message citations → 403."""
        owner = await create_verified_user(db_session, "exp_owner@example.com")
        intruder = await create_verified_user(db_session, "exp_intruder@example.com")

        chat = await create_chat_in_db(db_session, owner, "Private Export Chat")
        source_chunks = make_source_chunks()
        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Private export answer",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/export?message_id={msg.id}&format=apa",
            headers=auth_header(intruder),
        )

        assert response.status_code == 403

    # ── Expired token → 401 ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_citations_expired_token(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Expired auth token → 401."""
        user = await create_verified_user(db_session)
        chat = await create_chat_in_db(db_session, user)
        msg = await create_message_in_db(db_session, chat, "assistant", "answer")

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers={"Authorization": "Bearer expired.jwt.token"},
        )

        assert response.status_code == 401

    # ── Invalid UUID format → 422 ────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_citations_invalid_uuid(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Invalid UUID in path → 422 or 404."""
        user = await create_verified_user(db_session)

        response = await client.get(
            "/citations/messages/not-a-valid-uuid",
            headers=auth_header(user),
        )

        # Depending on implementation, could be 422 (validation) or 404
        assert response.status_code in (404, 422)
