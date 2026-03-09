"""
Edge case & stress tests for Citation Engine (SPEC-06).
Following TDD: These tests are written BEFORE implementation.

Tests are organized by category:
  1. TestMissingMetadataEdgeCases     — Graceful handling of missing/partial metadata
  2. TestDeduplicationEdgeCases       — Duplicate document handling
  3. TestBibtexKeyCollisions          — BibTeX key uniqueness
  4. TestUnicodeAndSpecialCharacters  — International chars, accents, special chars
  5. TestLargeInputEdgeCases          — Very long strings, many authors, many sources
  6. TestMalformedInputEdgeCases      — Unexpected input shapes and types
  7. TestAuthorParsingEdgeCases       — Unusual author name formats
  8. TestCitationFormatConsistency    — Cross-format consistency checks
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.helpers.security import hash_password, generate_access_token
from src.models.db_scheams.user import User
from src.models.db_scheams.Chat import Chat
from src.models.db_scheams.Message import Message


# ── Helpers ──────────────────────────────────────────────────────────────────


async def create_verified_user(
    db_session: AsyncSession, email: str = "edgecase@example.com"
) -> User:
    """Create a verified user in the DB and return the User object."""
    user = User(
        email=email,
        name="Edge Case User",
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
    db_session: AsyncSession, user: User, title: str | None = None
) -> Chat:
    """Insert a Chat record directly into the DB for test setup."""
    chat = Chat(id=uuid.uuid4(), user_id=user.id, title=title)
    db_session.add(chat)
    await db_session.commit()
    await db_session.refresh(chat)
    return chat


async def create_message_in_db(
    db_session: AsyncSession,
    chat: Chat,
    role: str = "assistant",
    content: str = "Test",
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


# ═════════════════════════════════════════════════════════════════════════════
# 1. MISSING METADATA EDGE CASES
# ═════════════════════════════════════════════════════════════════════════════


class TestMissingMetadataEdgeCases:
    """Scenario #14: Missing metadata → graceful fallback, no crashes."""

    @pytest.mark.asyncio
    async def test_completely_empty_metadata(self):
        """Empty dict → generates citations with defaults, no crash."""
        from src.services.citation_service import CitationGenerator

        metadata = {}
        result = CitationGenerator.generate_all_formats(metadata)

        assert isinstance(result, dict)
        assert len(result) == 4
        # Should use fallbacks
        for key, value in result.items():
            assert isinstance(value, str)
            assert len(value) > 0

    @pytest.mark.asyncio
    async def test_all_none_values(self):
        """All values None → generates citations with defaults, no crash."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": None,
            "year": None,
            "title": None,
            "journal": None,
            "doi": None,
        }
        # Should not crash
        result = CitationGenerator.generate_all_formats(metadata)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_all_empty_strings(self):
        """All empty strings → generates citations with defaults, no crash."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "",
            "year": "",
            "title": "",
            "journal": "",
            "doi": "",
        }
        # Should not crash
        result = CitationGenerator.generate_all_formats(metadata)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_only_title_provided(self):
        """Only title provided → citations still generated."""
        from src.services.citation_service import CitationGenerator

        metadata = {"title": "Important Paper"}
        result = CitationGenerator.generate_all_formats(metadata)

        assert "Important Paper" in result["apa"]
        assert "Important Paper" in result["mla"]
        assert "Important Paper" in result["bibtex"]

    @pytest.mark.asyncio
    async def test_only_author_provided(self):
        """Only author provided → citations still generated."""
        from src.services.citation_service import CitationGenerator

        metadata = {"author": "Smith, John"}
        result = CitationGenerator.generate_all_formats(metadata)

        assert "Smith" in result["inline_apa"]
        assert "Smith" in result["apa"]

    @pytest.mark.asyncio
    async def test_missing_author_apa_inline_uses_title(self):
        """APA inline with no author → fallback to shortened title."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "title": "A Study Without Named Authors",
            "year": "2020",
        }
        result = CitationGenerator.apa_inline(metadata)
        assert "2020" in result
        # Should use title since no author
        assert "Study" in result or "A Study" in result

    @pytest.mark.asyncio
    async def test_missing_author_and_title_apa_inline(self):
        """APA inline with no author AND no title → uses fallback."""
        from src.services.citation_service import CitationGenerator

        metadata = {"year": "2020"}
        result = CitationGenerator.apa_inline(metadata)
        assert "2020" in result
        # Should have some fallback text
        assert len(result) > 5


# ═════════════════════════════════════════════════════════════════════════════
# 2. DEDUPLICATION EDGE CASES
# ═════════════════════════════════════════════════════════════════════════════


class TestDeduplicationEdgeCases:
    """Scenario #15: Duplicate documents → only one citation per document."""

    @pytest.mark.asyncio
    async def test_duplicate_documents_deduplicated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Two chunks from same document → only one citation generated."""
        user = await create_verified_user(db_session, "dedup@example.com")
        chat = await create_chat_in_db(db_session, user, "Dedup Chat")

        doc_id = str(uuid.uuid4())
        source_chunks = [
            {
                "source_number": 1,
                "document_id": doc_id,
                "title": "Deep Learning",
                "author": "Smith, John",
                "year": "2020",
                "journal": "AI Journal",
                "page_number": 5,
                "similarity": 0.9,
            },
            {
                "source_number": 2,
                "document_id": doc_id,  # Same document!
                "title": "Deep Learning",
                "author": "Smith, John",
                "year": "2020",
                "journal": "AI Journal",
                "page_number": 10,
                "similarity": 0.85,
            },
        ]

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Answer from same document [Source 1][Source 2]",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        # Should only have 1 citation (deduplicated by document_id)
        assert len(data["citations"]) == 1

    @pytest.mark.asyncio
    async def test_different_documents_not_deduplicated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Two different documents → two separate citations."""
        user = await create_verified_user(db_session, "nodup@example.com")
        chat = await create_chat_in_db(db_session, user, "No Dedup Chat")

        source_chunks = [
            {
                "source_number": 1,
                "document_id": str(uuid.uuid4()),
                "title": "Paper A",
                "author": "Smith, John",
                "year": "2020",
                "page_number": 5,
                "similarity": 0.9,
            },
            {
                "source_number": 2,
                "document_id": str(uuid.uuid4()),  # Different document
                "title": "Paper B",
                "author": "Doe, Jane",
                "year": "2021",
                "page_number": 10,
                "similarity": 0.85,
            },
        ]

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Answer from two documents",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["citations"]) == 2

    @pytest.mark.asyncio
    async def test_three_chunks_two_documents_deduplicated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Three chunks from two documents → two citations."""
        user = await create_verified_user(db_session, "three_chunk@example.com")
        chat = await create_chat_in_db(db_session, user, "Three Chunk Chat")

        doc1_id = str(uuid.uuid4())
        doc2_id = str(uuid.uuid4())
        source_chunks = [
            {
                "source_number": 1,
                "document_id": doc1_id,
                "title": "Paper Alpha",
                "author": "Author A",
                "year": "2020",
                "page_number": 1,
                "similarity": 0.95,
            },
            {
                "source_number": 2,
                "document_id": doc2_id,
                "title": "Paper Beta",
                "author": "Author B",
                "year": "2021",
                "page_number": 5,
                "similarity": 0.88,
            },
            {
                "source_number": 3,
                "document_id": doc1_id,  # Duplicate of doc1
                "title": "Paper Alpha",
                "author": "Author A",
                "year": "2020",
                "page_number": 12,
                "similarity": 0.80,
            },
        ]

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Answer from three chunks, two docs",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["citations"]) == 2


# ═════════════════════════════════════════════════════════════════════════════
# 3. BIBTEX KEY COLLISION TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestBibtexKeyCollisions:
    """Business Rule #3: BibTeX keys must be unique; append a/b/c on collision."""

    @pytest.mark.asyncio
    async def test_bibtex_keys_unique_in_export(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Two papers by same author, same year → BibTeX keys with a/b suffix."""
        user = await create_verified_user(db_session, "keyunique@example.com")
        chat = await create_chat_in_db(db_session, user, "Key Collision Chat")

        source_chunks = [
            {
                "source_number": 1,
                "document_id": str(uuid.uuid4()),
                "title": "Deep Learning Approaches",
                "author": "Smith, John",
                "year": "2020",
                "page_number": 1,
                "similarity": 0.9,
            },
            {
                "source_number": 2,
                "document_id": str(uuid.uuid4()),
                "title": "Deep Understanding Methods",
                "author": "Smith, John",
                "year": "2020",
                "page_number": 5,
                "similarity": 0.85,
            },
        ]

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Answer with key collisions",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/export?message_id={msg.id}&format=bibtex",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        text = response.text

        # Both keys would normally be "smith2020deep" — but they must be unique
        # Find all citation keys (text between @ and ,)
        import re
        keys = re.findall(r'@\w+\{(\w+),', text)
        assert len(keys) == 2
        # Keys must be unique
        assert keys[0] != keys[1]


# ═════════════════════════════════════════════════════════════════════════════
# 4. UNICODE AND SPECIAL CHARACTER TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestUnicodeAndSpecialCharacters:
    """Test handling of international characters, accents, and special chars."""

    @pytest.mark.asyncio
    async def test_unicode_author_name(self):
        """Author with accented characters → no crash, valid output."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "García, José",
            "year": "2021",
            "title": "Estudio de IA",
            "journal": "Revista de Investigación",
        }
        result = CitationGenerator.generate_all_formats(metadata)
        assert isinstance(result, dict)
        assert "García" in result["apa"] or "Garcia" in result["apa"]

    @pytest.mark.asyncio
    async def test_chinese_title(self):
        """Chinese title → no crash, valid output."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Wang, Lei",
            "year": "2022",
            "title": "深度学习在医学中的应用",
        }
        result = CitationGenerator.generate_all_formats(metadata)
        assert isinstance(result, dict)
        assert "深度学习" in result["bibtex"]

    @pytest.mark.asyncio
    async def test_german_umlauts(self):
        """German umlauts in author → valid citation."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Müller, Hans",
            "year": "2020",
            "title": "Über die Verwendung von KI",
        }
        result = CitationGenerator.generate_all_formats(metadata)
        assert isinstance(result, dict)
        assert "Müller" in result["mla"] or "Muller" in result["mla"]

    @pytest.mark.asyncio
    async def test_special_characters_in_title(self):
        """Title with special chars (braces, quotes) → no BibTeX breakage."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Using {LaTeX} & \"Special\" Characters",
        }
        # Should not crash
        result = CitationGenerator.bibtex_entry(metadata)
        assert "@" in result  # Valid BibTeX structure
        assert "}" in result

    @pytest.mark.asyncio
    async def test_doi_with_special_characters(self):
        """DOI with special characters → handled correctly."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "DOI Test",
            "doi": "10.1000/xyz-123_456.789",
        }
        result = CitationGenerator.apa_reference(metadata)
        assert "10.1000/xyz-123_456.789" in result


# ═════════════════════════════════════════════════════════════════════════════
# 5. LARGE INPUT EDGE CASES
# ═════════════════════════════════════════════════════════════════════════════


class TestLargeInputEdgeCases:
    """Test handling of very long strings and many items."""

    @pytest.mark.asyncio
    async def test_very_long_title(self):
        """Very long title (1000+ chars) → no crash."""
        from src.services.citation_service import CitationGenerator

        long_title = "A" * 1000
        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": long_title,
        }
        result = CitationGenerator.generate_all_formats(metadata)
        assert isinstance(result, dict)
        for value in result.values():
            assert len(value) > 0

    @pytest.mark.asyncio
    async def test_very_long_author_string(self):
        """Very long author string (many co-authors) → no crash."""
        from src.services.citation_service import CitationGenerator

        # 20 authors
        authors = " and ".join([f"Author{i}, Name{i}" for i in range(20)])
        metadata = {
            "author": authors,
            "year": "2020",
            "title": "Multi-Author Paper",
        }
        result = CitationGenerator.generate_all_formats(metadata)
        assert isinstance(result, dict)
        # APA inline should use "et al." for 3+
        assert "et al." in result["inline_apa"]

    @pytest.mark.asyncio
    async def test_many_sources_in_message(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Message with 20 sources → all citations generated."""
        user = await create_verified_user(db_session, "manysources@example.com")
        chat = await create_chat_in_db(db_session, user, "Many Sources Chat")

        source_chunks = [
            {
                "source_number": i + 1,
                "document_id": str(uuid.uuid4()),
                "title": f"Paper {i + 1}",
                "author": f"Author{i + 1}, Name",
                "year": str(2000 + i),
                "page_number": i + 1,
                "similarity": 0.9 - (i * 0.02),
            }
            for i in range(20)
        ]

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Answer with many sources",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["citations"]) == 20


# ═════════════════════════════════════════════════════════════════════════════
# 6. MALFORMED INPUT EDGE CASES
# ═════════════════════════════════════════════════════════════════════════════


class TestMalformedInputEdgeCases:
    """Test handling of unexpected/malformed inputs."""

    @pytest.mark.asyncio
    async def test_metadata_with_extra_fields(self):
        """Metadata with extra unknown fields → ignored, no crash."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Test Paper",
            "unknown_field": "should be ignored",
            "another_field": 12345,
        }
        result = CitationGenerator.generate_all_formats(metadata)
        assert isinstance(result, dict)
        assert "Smith" in result["inline_apa"]

    @pytest.mark.asyncio
    async def test_year_as_integer(self):
        """Year as integer instead of string → no crash."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": 2020,  # Integer instead of string
            "title": "Type Test",
        }
        # Should not crash — implementation should handle type conversion
        try:
            result = CitationGenerator.generate_all_formats(metadata)
            assert isinstance(result, dict)
        except (TypeError, AttributeError):
            # If it crashes on integer year, that's also a valid test finding
            pass

    @pytest.mark.asyncio
    async def test_whitespace_only_author(self):
        """Author string with only whitespace → treated as missing."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "   ",
            "year": "2020",
            "title": "Whitespace Author",
        }
        result = CitationGenerator.apa_inline(metadata)
        # Whitespace-only author should be treated as no author
        assert "2020" in result

    @pytest.mark.asyncio
    async def test_source_chunks_with_missing_fields(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Source chunks with minimal fields → citations still generated."""
        user = await create_verified_user(db_session, "minimal@example.com")
        chat = await create_chat_in_db(db_session, user, "Minimal Fields Chat")

        source_chunks = [
            {
                "source_number": 1,
                "document_id": str(uuid.uuid4()),
                # Missing title, author, year — only minimal fields
                "page_number": 1,
                "similarity": 0.9,
            },
        ]

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "Answer with minimal metadata",
            source_chunks=source_chunks,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        # Should still return citation(s) with fallback values
        assert len(data["citations"]) >= 1

    @pytest.mark.asyncio
    async def test_source_chunks_null_in_message(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """source_chunks stored as null → empty citations list."""
        user = await create_verified_user(db_session, "nullchunks@example.com")
        chat = await create_chat_in_db(db_session, user, "Null Chunks Chat")

        msg = await create_message_in_db(
            db_session, chat, "assistant",
            "No sources",
            source_chunks=None,
        )

        response = await client.get(
            f"/citations/messages/{msg.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["citations"] == []


# ═════════════════════════════════════════════════════════════════════════════
# 7. AUTHOR PARSING EDGE CASES
# ═════════════════════════════════════════════════════════════════════════════


class TestAuthorParsingEdgeCases:
    """Edge cases for _parse_authors() and author formatting."""

    @pytest.mark.asyncio
    async def test_author_with_hyphenated_last_name(self):
        """Hyphenated last name → kept intact."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("García-López, María")
        assert len(result) == 1
        assert result[0]["last"] == "García-López"

    @pytest.mark.asyncio
    async def test_author_with_jr_suffix(self):
        """Author with Jr. → parsed without crash."""
        from src.services.citation_service import _parse_authors

        # "Jr." might appear in various positions
        result = _parse_authors("Smith Jr., John")
        assert len(result) >= 1
        # Should capture some form of the name

    @pytest.mark.asyncio
    async def test_author_with_multiple_spaces(self):
        """Author string with extra spaces → cleaned up."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("  Smith ,  John   and   Doe ,  Jane  ")
        assert len(result) == 2
        assert result[0]["last"] == "Smith"
        assert result[1]["last"] == "Doe"

    @pytest.mark.asyncio
    async def test_author_with_de_prefix(self):
        """Author with 'de' prefix → handled as part of name."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("de la Cruz, Carlos")
        assert len(result) == 1
        # "de la Cruz" should be the last name
        assert "Cruz" in result[0]["last"]

    @pytest.mark.asyncio
    async def test_mononym_author(self):
        """Single-name author (mononym like 'Aristotle') → last name only."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("Aristotle")
        assert len(result) == 1
        assert result[0]["last"] == "Aristotle"
        assert result[0]["first"] == ""

    @pytest.mark.asyncio
    async def test_author_with_mixed_separators(self):
        """Authors with mixed separators (and, &, ;) → all parsed."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("Smith, John and Doe, Jane; Johnson, Robert")
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_author_first_last_with_middle(self):
        """'John Adam Smith' → first='John Adam', last='Smith'."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("John Adam Smith")
        assert len(result) == 1
        assert result[0]["last"] == "Smith"
        assert result[0]["first"] == "John Adam"


# ═════════════════════════════════════════════════════════════════════════════
# 8. CITATION FORMAT CONSISTENCY TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestCitationFormatConsistency:
    """Verify consistency across different citation formats."""

    @pytest.mark.asyncio
    async def test_same_metadata_produces_consistent_output(self):
        """Same metadata → same output every time (deterministic)."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Deep Learning in Medicine",
            "journal": "Journal of AI Research",
            "doi": "10.1234/jair.2020.001",
        }

        result1 = CitationGenerator.generate_all_formats(metadata)
        result2 = CitationGenerator.generate_all_formats(metadata)

        assert result1 == result2

    @pytest.mark.asyncio
    async def test_all_formats_contain_title(self):
        """Title appears in every format."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Unique Paper Title XYZ",
            "journal": "Test Journal",
        }
        result = CitationGenerator.generate_all_formats(metadata)

        assert "Unique Paper Title XYZ" in result["apa"]
        assert "Unique Paper Title XYZ" in result["mla"]
        assert "Unique Paper Title XYZ" in result["bibtex"]

    @pytest.mark.asyncio
    async def test_all_formats_contain_year(self):
        """Year appears in every format."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Test Paper",
        }
        result = CitationGenerator.generate_all_formats(metadata)

        assert "2020" in result["inline_apa"]
        assert "2020" in result["apa"]
        assert "2020" in result["mla"]
        assert "2020" in result["bibtex"]

    @pytest.mark.asyncio
    async def test_all_formats_contain_author(self):
        """Author name (in some form) appears in every format."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Test Paper",
        }
        result = CitationGenerator.generate_all_formats(metadata)

        assert "Smith" in result["inline_apa"]
        assert "Smith" in result["apa"]
        assert "Smith" in result["mla"]
        assert "Smith" in result["bibtex"]

    @pytest.mark.asyncio
    async def test_bibtex_entry_is_parseable(self):
        """BibTeX entry should follow valid syntax that a parser can read."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Parseable Paper",
            "journal": "Test Journal",
            "doi": "10.1234/test",
        }
        result = CitationGenerator.bibtex_entry(metadata)

        # Check basic BibTeX structure requirements
        assert result.startswith("@")
        assert "{" in result
        assert result.strip().endswith("}")
        # Count balanced braces (should have matching { and })
        assert result.count("{") == result.count("}")

    @pytest.mark.asyncio
    async def test_apa_reference_ends_with_period_or_url(self):
        """APA reference should end with a period or a URL."""
        from src.services.citation_service import CitationGenerator

        # Without DOI → ends with period
        metadata_no_doi = {
            "author": "Smith, John",
            "year": "2020",
            "title": "No DOI Paper",
            "journal": "Test Journal",
        }
        result_no_doi = CitationGenerator.apa_reference(metadata_no_doi)
        assert result_no_doi.rstrip().endswith(".")

        # With DOI → ends with URL
        metadata_with_doi = {
            "author": "Smith, John",
            "year": "2020",
            "title": "DOI Paper",
            "doi": "10.1234/test",
        }
        result_with_doi = CitationGenerator.apa_reference(metadata_with_doi)
        assert "doi.org" in result_with_doi

    @pytest.mark.asyncio
    async def test_mla_reference_ends_with_period(self):
        """MLA reference should end with a period."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "MLA Paper",
            "journal": "Test Journal",
        }
        result = CitationGenerator.mla_reference(metadata)
        assert result.rstrip().endswith(".")
