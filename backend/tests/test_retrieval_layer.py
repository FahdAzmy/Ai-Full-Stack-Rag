"""
Test cases for Retrieval Layer (SPEC-04).
Following TDD: These tests are written BEFORE implementation.

Tests are organized by service:
  1. TestSearchSimilarChunks         — Semantic search via pgvector
  2. TestContextBuilder              — LLM prompt assembly
  3. TestBuildContextString          — Context formatting helper
  4. TestGetSourceSummary            — Source metadata summary

All external dependencies (OpenAI embedding API, database) are mocked.

Spec Scenarios Covered:
  #1  Search with relevant query → returns chunks sorted by relevance
  #2  Search with irrelevant query → returns empty or fewer results
  #3  Search with document_ids filter → only returns matching documents
  #4  Search when user has no documents → returns empty results
  #5  Search only returns "ready" documents → processing/failed excluded
  #6  User A cannot see User B's chunks → user_id filter enforced
  #7  Context builder with 5 chunks → well-formatted prompt
  #8  Context builder with 0 chunks → "(No relevant context found)"
  #9  Context builder with history → history messages in correct order
  #10 Context builder history limit → only last 10 messages
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.helpers.security import hash_password
from src.models.db_scheams.user import User
from src.models.db_scheams.document import Document
from src.models.db_scheams.DocumentChunk import DocumentChunk


# ── Helpers ──────────────────────────────────────────────────────────────────


async def create_verified_user(
    db_session: AsyncSession, email: str = "retrieval@example.com"
) -> User:
    """Create a verified user in the DB and return the User object."""
    user = User(
        email=email,
        name="Retrieval Test User",
        hashed_password=hash_password("SecurePass123"),
        is_verified=True,
        verification_token="123456",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def create_document_with_chunks(
    db_session: AsyncSession,
    user: User,
    file_name: str = "test_paper.pdf",
    status: str = "ready",
    title: str = "Test Paper",
    author: str = "Test Author",
    year: str = "2023",
    journal: str = "Test Journal",
    doi: str = "10.1234/test",
    num_chunks: int = 3,
    embedding: list[float] | None = None,
) -> tuple[Document, list[DocumentChunk]]:
    """Create a document with chunks in the DB for test setup."""
    doc = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        file_name=file_name,
        file_path=f"/tmp/{file_name}",
        status=status,
        title=title,
        author=author,
        year=year,
        journal=journal,
        doi=doi,
        total_pages=num_chunks,
    )
    db_session.add(doc)
    await db_session.flush()

    chunks = []
    for i in range(num_chunks):
        chunk = DocumentChunk(
            id=uuid.uuid4(),
            user_id=user.id,
            document_id=doc.id,
            content=f"Content of chunk {i} from {file_name}. " * 20,
            page_number=i + 1,
            chunk_index=i,
            embedding=embedding or [0.1 * (i + 1)] * 1536,
        )
        db_session.add(chunk)
        chunks.append(chunk)

    await db_session.commit()
    for chunk in chunks:
        await db_session.refresh(chunk)
    await db_session.refresh(doc)
    return doc, chunks


def make_mock_row(
    chunk_id: str | None = None,
    content: str = "Mock chunk content",
    page_number: int | None = 1,
    chunk_index: int = 0,
    document_id: str | None = None,
    file_name: str | None = "paper.pdf",
    title: str | None = "Mock Paper",
    author: str | None = "Mock Author",
    year: str | None = "2023",
    journal: str | None = "Mock Journal",
    doi: str | None = "10.1234/mock",
    similarity: float = 0.85,
) -> dict:
    """Create a mock row dict as returned by search_similar_chunks."""
    return {
        "chunk_id": chunk_id or str(uuid.uuid4()),
        "content": content,
        "page_number": page_number,
        "chunk_index": chunk_index,
        "document_id": document_id or str(uuid.uuid4()),
        "file_name": file_name,
        "title": title,
        "author": author,
        "year": year,
        "journal": journal,
        "doi": doi,
        "similarity": similarity,
    }


# ═════════════════════════════════════════════════════════════════════════════
# 1. RETRIEVAL SERVICE TESTS — search_similar_chunks()
# ═════════════════════════════════════════════════════════════════════════════


class TestSearchSimilarChunks:
    """Tests for retrieval_service.search_similar_chunks()."""

    # ── Scenario #1: Search with relevant query → returns chunks sorted ──

    @pytest.mark.asyncio
    async def test_search_returns_chunks_sorted_by_relevance(
        self, db_session: AsyncSession
    ):
        """
        Scenario #1: A relevant query should return chunks with
        similarity > 0.3, sorted descending by relevance.
        """
        user = await create_verified_user(db_session)
        doc, chunks = await create_document_with_chunks(db_session, user)

        # The mock embedding will be compared via pgvector cosine distance
        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="test query about the paper",
                user_id=str(user.id),
                db=db_session,
                top_k=5,
                similarity_threshold=0.0,  # Low threshold to get results
            )

        # Should return results
        assert len(results) > 0

        # Each result should have all required fields
        for result in results:
            assert "chunk_id" in result
            assert "content" in result
            assert "page_number" in result
            assert "chunk_index" in result
            assert "document_id" in result
            assert "file_name" in result
            assert "title" in result
            assert "author" in result
            assert "year" in result
            assert "journal" in result
            assert "doi" in result
            assert "similarity" in result
            assert isinstance(result["similarity"], float)

        # Results should be sorted by similarity descending (cosine distance ASC)
        similarities = [r["similarity"] for r in results]
        assert similarities == sorted(similarities, reverse=True)

    # ── Scenario #2: Irrelevant query → empty or fewer results ───────────

    @pytest.mark.asyncio
    async def test_search_irrelevant_query_returns_empty(
        self, db_session: AsyncSession
    ):
        """
        Scenario #2: A query with a very high threshold should return
        empty or fewer results when similarity is below threshold.
        """
        user = await create_verified_user(db_session, "irrelevant@example.com")
        doc, chunks = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.9] * 1536  # Very different from stored embeddings

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="completely unrelated topic xyz",
                user_id=str(user.id),
                db=db_session,
                top_k=5,
                similarity_threshold=0.99,  # Very high threshold
            )

        # Should return no results or fewer results
        assert len(results) == 0 or all(
            r["similarity"] >= 0.99 for r in results
        )

    # ── Scenario #3: Filter by document_ids ──────────────────────────────

    @pytest.mark.asyncio
    async def test_search_with_document_ids_filter(
        self, db_session: AsyncSession
    ):
        """
        Scenario #3: Passing document_ids should only return chunks
        from those specific documents.
        """
        user = await create_verified_user(db_session, "filter@example.com")

        # Create two documents
        doc1, _ = await create_document_with_chunks(
            db_session, user, file_name="paper_a.pdf", title="Paper A"
        )
        doc2, _ = await create_document_with_chunks(
            db_session, user, file_name="paper_b.pdf", title="Paper B"
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            # Search only in doc1
            results = await search_similar_chunks(
                query="search within paper A",
                user_id=str(user.id),
                db=db_session,
                top_k=10,
                similarity_threshold=0.0,
                document_ids=[str(doc1.id)],
            )

        # All results should be from doc1
        for result in results:
            assert result["document_id"] == str(doc1.id)

    # ── Scenario #4: User has no documents → empty results ───────────────

    @pytest.mark.asyncio
    async def test_search_no_documents_returns_empty(
        self, db_session: AsyncSession
    ):
        """
        Scenario #4: When a user has no documents, search should
        return an empty list gracefully.
        """
        user = await create_verified_user(db_session, "nodocs@example.com")

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="any question at all",
                user_id=str(user.id),
                db=db_session,
            )

        assert results == []

    # ── Scenario #5: Only "ready" documents are searched ─────────────────

    @pytest.mark.asyncio
    async def test_search_excludes_non_ready_documents(
        self, db_session: AsyncSession
    ):
        """
        Scenario #5: Documents with status 'processing' or 'failed'
        should never appear in search results.
        """
        user = await create_verified_user(db_session, "status@example.com")

        # Create documents with different statuses
        ready_doc, _ = await create_document_with_chunks(
            db_session, user,
            file_name="ready.pdf", status="ready", title="Ready Paper"
        )
        processing_doc, _ = await create_document_with_chunks(
            db_session, user,
            file_name="processing.pdf", status="processing", title="Processing Paper"
        )
        failed_doc, _ = await create_document_with_chunks(
            db_session, user,
            file_name="failed.pdf", status="failed", title="Failed Paper"
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="search all documents",
                user_id=str(user.id),
                db=db_session,
                top_k=20,
                similarity_threshold=0.0,
            )

        # Only the "ready" document's chunks should appear
        result_doc_ids = {r["document_id"] for r in results}
        assert len(results) > 0, "Ready document should return results"
        assert str(ready_doc.id) in result_doc_ids
        assert str(processing_doc.id) not in result_doc_ids
        assert str(failed_doc.id) not in result_doc_ids

    # ── Scenario #6: User A cannot see User B's chunks ───────────────────

    @pytest.mark.asyncio
    async def test_user_isolation_enforced(self, db_session: AsyncSession):
        """
        Scenario #6: User A's search must NEVER return chunks
        belonging to User B. Data isolation is non-negotiable.
        """
        user_a = await create_verified_user(db_session, "user_a@example.com")
        user_b = await create_verified_user(db_session, "user_b@example.com")

        # Create documents for both users
        doc_a, _ = await create_document_with_chunks(
            db_session, user_a,
            file_name="user_a_paper.pdf", title="User A Paper"
        )
        doc_b, _ = await create_document_with_chunks(
            db_session, user_b,
            file_name="user_b_paper.pdf", title="User B Paper"
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            # Search as User A
            results_a = await search_similar_chunks(
                query="search as user A",
                user_id=str(user_a.id),
                db=db_session,
                top_k=20,
                similarity_threshold=0.0,
            )

        # User A should only see their own documents
        for result in results_a:
            assert result["document_id"] == str(doc_a.id)
            assert result["document_id"] != str(doc_b.id)

    @pytest.mark.asyncio
    async def test_user_b_cannot_see_user_a_chunks(
        self, db_session: AsyncSession
    ):
        """
        Reverse of Scenario #6: User B also must not see User A's data.
        """
        user_a = await create_verified_user(db_session, "a_reverse@example.com")
        user_b = await create_verified_user(db_session, "b_reverse@example.com")

        doc_a, _ = await create_document_with_chunks(
            db_session, user_a, file_name="a_paper.pdf", title="A's Paper"
        )
        doc_b, _ = await create_document_with_chunks(
            db_session, user_b, file_name="b_paper.pdf", title="B's Paper"
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            # Search as User B
            results_b = await search_similar_chunks(
                query="search as user B",
                user_id=str(user_b.id),
                db=db_session,
                top_k=20,
                similarity_threshold=0.0,
            )

        # User B should only see their own documents
        for result in results_b:
            assert result["document_id"] == str(doc_b.id)
            assert result["document_id"] != str(doc_a.id)

    # ── Edge Case: top_k limits results ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_top_k_limits_results(self, db_session: AsyncSession):
        """
        top_k=2 should return at most 2 results even if more match.
        """
        user = await create_verified_user(db_session, "topk@example.com")
        doc, _ = await create_document_with_chunks(
            db_session, user, num_chunks=10
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                top_k=2,
                similarity_threshold=0.0,
            )

        assert len(results) <= 2

    # ── Edge Case: Default top_k is 5 ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_default_top_k_is_5(self, db_session: AsyncSession):
        """
        Without explicit top_k, default should be 5.
        """
        user = await create_verified_user(db_session, "default_topk@example.com")
        doc, _ = await create_document_with_chunks(
            db_session, user, num_chunks=10
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                similarity_threshold=0.0,
            )

        assert len(results) <= 5

    # ── Edge Case: Default similarity threshold is 0.3 ───────────────────

    @pytest.mark.asyncio
    async def test_default_similarity_threshold_is_0_3(
        self, db_session: AsyncSession
    ):
        """
        The default similarity_threshold should be 0.3.
        Chunks with similarity < 0.3 should be excluded.
        """
        user = await create_verified_user(db_session, "threshold@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                # Not passing similarity_threshold → should default to 0.3
            )

        # All returned results should have similarity >= 0.3
        for result in results:
            assert result["similarity"] >= 0.3

    # ── Edge Case: Similarity score is a rounded float ───────────────────

    @pytest.mark.asyncio
    async def test_similarity_is_rounded_float(self, db_session: AsyncSession):
        """
        Each result's similarity should be a float rounded to 4 decimal places.
        """
        user = await create_verified_user(db_session, "round@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                similarity_threshold=0.0,
            )

        for result in results:
            sim = result["similarity"]
            assert isinstance(sim, float)
            # Check rounded to 4 decimal places
            assert sim == round(sim, 4)

    # ── Edge Case: All result fields are strings where expected ──────────

    @pytest.mark.asyncio
    async def test_result_field_types(self, db_session: AsyncSession):
        """
        chunk_id and document_id should be string UUIDs.
        """
        user = await create_verified_user(db_session, "types@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="type check query",
                user_id=str(user.id),
                db=db_session,
                similarity_threshold=0.0,
            )

        for result in results:
            assert isinstance(result["chunk_id"], str)
            assert isinstance(result["document_id"], str)
            assert isinstance(result["content"], str)
            # Verify UUIDs are valid
            uuid.UUID(result["chunk_id"])
            uuid.UUID(result["document_id"])

    # ── Edge Case: Embedding generation failure propagates ────────────────

    @pytest.mark.asyncio
    async def test_embedding_failure_propagates(self, db_session: AsyncSession):
        """
        If embedding generation fails, the exception should propagate.
        """
        user = await create_verified_user(db_session, "embfail@example.com")

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            side_effect=Exception("Embedding API error"),
        ):
            from src.services.retrieval_service import search_similar_chunks

            with pytest.raises(Exception, match="Embedding API error"):
                await search_similar_chunks(
                    query="this will fail",
                    user_id=str(user.id),
                    db=db_session,
                )

    # ── Edge Case: Empty query string ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_empty_query_still_works(self, db_session: AsyncSession):
        """
        An empty query should not crash; it should still attempt
        embedding and return results (or empty) without errors.
        """
        user = await create_verified_user(db_session, "empty_q@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            # Should not raise
            results = await search_similar_chunks(
                query="",
                user_id=str(user.id),
                db=db_session,
                similarity_threshold=0.0,
            )

        assert isinstance(results, list)

    # ── Edge Case: document_ids with empty list ──────────────────────────

    @pytest.mark.asyncio
    async def test_empty_document_ids_list(self, db_session: AsyncSession):
        """
        Passing an empty list for document_ids should behave the same
        as not filtering (None) — i.e., search all documents.
        """
        user = await create_verified_user(db_session, "emptyids@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            # Empty list should not filter
            results_empty = await search_similar_chunks(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                similarity_threshold=0.0,
                document_ids=[],
            )

            results_none = await search_similar_chunks(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                similarity_threshold=0.0,
                document_ids=None,
            )

        # Both should return the same results
        assert len(results_empty) == len(results_none)

    # ── Edge Case: Non-existent user_id → empty results ──────────────────

    @pytest.mark.asyncio
    async def test_nonexistent_user_id_returns_empty(
        self, db_session: AsyncSession
    ):
        """
        A user_id that doesn't exist should return empty results,
        not raise an error.
        """
        fake_user_id = str(uuid.uuid4())
        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="test query",
                user_id=fake_user_id,
                db=db_session,
            )

        assert results == []

    # ── Edge Case: Multiple document_ids filter ──────────────────────────

    @pytest.mark.asyncio
    async def test_multiple_document_ids_filter(self, db_session: AsyncSession):
        """
        Passing multiple document_ids should return chunks
        from all specified documents.
        """
        user = await create_verified_user(db_session, "multi_filter@example.com")

        doc1, _ = await create_document_with_chunks(
            db_session, user, file_name="first.pdf", title="First"
        )
        doc2, _ = await create_document_with_chunks(
            db_session, user, file_name="second.pdf", title="Second"
        )
        doc3, _ = await create_document_with_chunks(
            db_session, user, file_name="third.pdf", title="Third"
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                top_k=20,
                similarity_threshold=0.0,
                document_ids=[str(doc1.id), str(doc2.id)],
            )

        # Results should only be from doc1 and doc2
        result_doc_ids = {r["document_id"] for r in results}
        for doc_id in result_doc_ids:
            assert doc_id in {str(doc1.id), str(doc2.id)}
        assert str(doc3.id) not in result_doc_ids

    # ── Edge Case: Non-existent document_id returns no results ───────────

    @pytest.mark.asyncio
    async def test_nonexistent_document_id_filter(
        self, db_session: AsyncSession
    ):
        """
        Filtering by a non-existent document_id should return empty.
        """
        user = await create_verified_user(db_session, "no_doc@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                similarity_threshold=0.0,
                document_ids=[str(uuid.uuid4())],  # Non-existent
            )

        assert results == []

    # ── Edge Case: Metadata fields can be None ───────────────────────────

    @pytest.mark.asyncio
    async def test_results_include_null_metadata(self, db_session: AsyncSession):
        """
        Documents with null metadata fields should still return
        results with None values for those fields.
        """
        user = await create_verified_user(db_session, "nullmeta@example.com")
        doc, _ = await create_document_with_chunks(
            db_session, user,
            file_name="no_meta.pdf",
            title=None,
            author=None,
            year=None,
            journal=None,
            doi=None,
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                similarity_threshold=0.0,
            )

        # Should still return results; metadata fields will be None
        if len(results) > 0:
            result = results[0]
            assert result["title"] is None
            assert result["author"] is None
            assert result["year"] is None
            assert result["journal"] is None
            assert result["doi"] is None

    # ── Edge Case: "uploading" status documents excluded ─────────────────

    @pytest.mark.asyncio
    async def test_uploading_status_excluded(self, db_session: AsyncSession):
        """
        Documents with status "uploading" should be excluded from search.
        """
        user = await create_verified_user(db_session, "uploading@example.com")
        doc, _ = await create_document_with_chunks(
            db_session, user,
            file_name="uploading.pdf",
            status="uploading",
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                similarity_threshold=0.0,
            )

        assert results == []

    # ── Acceptance Criteria: Logging captures query details & count ────────

    @pytest.mark.asyncio
    async def test_search_logs_query_and_result_count(
        self, db_session: AsyncSession
    ):
        """
        Acceptance Criteria: Logging should capture query details
        and the number of retrieved results.
        """
        user = await create_verified_user(db_session, "logging@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)
        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ), patch(
            "src.services.retrieval_service.logger"
        ) as mock_logger:
            from src.services.retrieval_service import search_similar_chunks

            results = await search_similar_chunks(
                query="test query about logging",
                user_id=str(user.id),
                db=db_session,
                similarity_threshold=0.0,
            )

        # Should log at least twice: once for the query, once for results
        assert mock_logger.info.call_count >= 2

        # First log: query text appears in format string or args
        first_call = mock_logger.info.call_args_list[0][0]
        first_log_msg = first_call[0] % first_call[1:] if len(first_call) > 1 else first_call[0]
        assert "test query about logging" in first_log_msg

        # Second log: should mention retrieved count
        second_call = mock_logger.info.call_args_list[1][0]
        second_log_msg = second_call[0] % second_call[1:] if len(second_call) > 1 else second_call[0]
        assert "Retrieved" in second_log_msg

    # ── Edge Case: Database query failure propagates ──────────────────────

    @pytest.mark.asyncio
    async def test_database_error_propagates(self, db_session: AsyncSession):
        """
        If the DB query itself fails, the exception should propagate.
        (Complements test_embedding_failure_propagates.)
        """
        user = await create_verified_user(db_session, "dberror@example.com")
        mock_embedding = [0.1] * 1536

        # Create a mock session whose execute() raises
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(
            side_effect=Exception("Database connection lost")
        )

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import search_similar_chunks

            with pytest.raises(Exception, match="Database connection lost"):
                await search_similar_chunks(
                    query="this will fail at DB level",
                    user_id=str(user.id),
                    db=mock_db,
                )

    # ── Validation: Invalid query type raises ValueError ─────────────────

    @pytest.mark.asyncio
    async def test_invalid_query_type_raises_value_error(
        self, db_session: AsyncSession
    ):
        """
        Passing a non-string query (e.g. None, int) should raise ValueError
        before any embedding or DB call is made.
        """
        user = await create_verified_user(db_session, "bad_query@example.com")

        from src.services.retrieval_service import search_similar_chunks

        with pytest.raises(ValueError, match="Query must be a string"):
            await search_similar_chunks(
                query=None,  # type: ignore
                user_id=str(user.id),
                db=db_session,
            )

    # ── Validation: Invalid user_id UUID raises ValueError ───────────────

    @pytest.mark.asyncio
    async def test_invalid_user_id_raises_value_error(
        self, db_session: AsyncSession
    ):
        """
        Passing a malformed user_id (not a valid UUID) should raise ValueError.
        """
        from src.services.retrieval_service import search_similar_chunks

        with pytest.raises(ValueError, match="Invalid user_id format"):
            await search_similar_chunks(
                query="test query",
                user_id="not-a-uuid",
                db=db_session,
            )


# ═════════════════════════════════════════════════════════════════════════════
# 2. CONTEXT BUILDER TESTS — build_prompt()
# ═════════════════════════════════════════════════════════════════════════════


class TestContextBuilderBuildPrompt:
    """Tests for context_builder.build_prompt()."""

    # ── Scenario #7: Build prompt with 5 chunks ─────────────────────────

    def test_build_prompt_with_chunks(self):
        """
        Scenario #7: 5 chunks should produce a well-formatted prompt
        with numbered sources and system instructions.
        """
        chunks = [make_mock_row(similarity=0.9 - i * 0.1) for i in range(5)]

        from src.services.context_builder import build_prompt

        messages = build_prompt(
            question="What is deep learning?",
            retrieved_chunks=chunks,
        )

        # Should return a list of dicts
        assert isinstance(messages, list)
        assert len(messages) >= 2  # system + user

        # First message should be the system prompt
        assert messages[0]["role"] == "system"
        assert "ScholarGPT" in messages[0]["content"]

        # Last message should be the user's question
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "What is deep learning?"

        # System prompt should contain source labels
        system_content = messages[0]["content"]
        assert "[Source 1]" in system_content
        assert "[Source 5]" in system_content

    # ── Scenario #8: Build prompt with 0 chunks ─────────────────────────

    def test_build_prompt_with_no_chunks(self):
        """
        Scenario #8: When no chunks are retrieved, the system prompt
        should include "(No relevant context found in uploaded papers.)".
        """
        from src.services.context_builder import build_prompt

        messages = build_prompt(
            question="What is quantum computing?",
            retrieved_chunks=[],
        )

        system_content = messages[0]["content"]
        assert "(No relevant context found in uploaded papers.)" in system_content

        # Should still have system + user messages
        assert len(messages) == 2
        assert messages[-1]["content"] == "What is quantum computing?"

    # ── Scenario #9: Build prompt with conversation history ──────────────

    def test_build_prompt_with_history(self):
        """
        Scenario #9: Conversation history should be included between
        system prompt and current question, in correct order.
        """
        chunks = [make_mock_row()]
        history = [
            {"role": "user", "content": "What is AI?"},
            {"role": "assistant", "content": "AI is artificial intelligence."},
            {"role": "user", "content": "Tell me more."},
            {"role": "assistant", "content": "AI has many applications..."},
        ]

        from src.services.context_builder import build_prompt

        messages = build_prompt(
            question="How does it relate to medicine?",
            retrieved_chunks=chunks,
            conversation_history=history,
        )

        # Structure: system + 4 history + current user question = 6 messages
        assert len(messages) == 6

        # First: system
        assert messages[0]["role"] == "system"

        # Middle: history in order
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "What is AI?"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "AI is artificial intelligence."
        assert messages[3]["role"] == "user"
        assert messages[3]["content"] == "Tell me more."
        assert messages[4]["role"] == "assistant"
        assert messages[4]["content"] == "AI has many applications..."

        # Last: current question
        assert messages[5]["role"] == "user"
        assert messages[5]["content"] == "How does it relate to medicine?"

    # ── Scenario #10: History limit (max 10 messages) ────────────────────

    def test_build_prompt_history_limit(self):
        """
        Scenario #10: Only the last 10 history messages should be included.
        """
        chunks = [make_mock_row()]
        # Create 20 history messages
        history = []
        for i in range(20):
            role = "user" if i % 2 == 0 else "assistant"
            history.append({"role": role, "content": f"Message {i}"})

        from src.services.context_builder import build_prompt

        messages = build_prompt(
            question="Current question",
            retrieved_chunks=chunks,
            conversation_history=history,
        )

        # Should have: system + 10 history + current = 12
        assert len(messages) == 12

        # The included history should be the LAST 10 messages (10-19)
        included_history = messages[1:-1]  # Exclude system and current
        assert len(included_history) == 10
        assert included_history[0]["content"] == "Message 10"
        assert included_history[-1]["content"] == "Message 19"

    # ── Edge Case: Custom max_history_messages ───────────────────────────

    def test_build_prompt_custom_history_limit(self):
        """
        Custom max_history_messages should override the default 10.
        """
        chunks = [make_mock_row()]
        history = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(20)
        ]

        from src.services.context_builder import build_prompt

        messages = build_prompt(
            question="Current question",
            retrieved_chunks=chunks,
            conversation_history=history,
            max_history_messages=3,
        )

        # system + 3 history + current = 5
        assert len(messages) == 5

        # Should include last 3 messages
        included_history = messages[1:-1]
        assert len(included_history) == 3
        assert included_history[0]["content"] == "Message 17"

    # ── Edge Case: None conversation history ─────────────────────────────

    def test_build_prompt_none_history(self):
        """
        Passing None for conversation_history should produce only
        system + user messages.
        """
        chunks = [make_mock_row()]

        from src.services.context_builder import build_prompt

        messages = build_prompt(
            question="A question",
            retrieved_chunks=chunks,
            conversation_history=None,
        )

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    # ── Edge Case: Empty conversation history ────────────────────────────

    def test_build_prompt_empty_history(self):
        """
        Passing an empty list for conversation_history should produce
        only system + user messages.
        """
        chunks = [make_mock_row()]

        from src.services.context_builder import build_prompt

        messages = build_prompt(
            question="A question",
            retrieved_chunks=chunks,
            conversation_history=[],
        )

        assert len(messages) == 2

    # ── Edge Case: Messages have correct role/content structure ──────────

    def test_messages_have_role_and_content(self):
        """
        Every message in the output must have 'role' and 'content' keys.
        This ensures OpenAI API compatibility.
        """
        chunks = [make_mock_row()]
        history = [{"role": "user", "content": "Previous question"}]

        from src.services.context_builder import build_prompt

        messages = build_prompt(
            question="Current question",
            retrieved_chunks=chunks,
            conversation_history=history,
        )

        for msg in messages:
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ("system", "user", "assistant")
            assert isinstance(msg["content"], str)

    # ── Edge Case: System prompt includes ScholarGPT instructions ────────

    def test_system_prompt_contains_key_instructions(self):
        """
        System prompt should contain ScholarGPT identity, citation rules,
        and context limitations.
        """
        chunks = [make_mock_row()]

        from src.services.context_builder import build_prompt

        messages = build_prompt(
            question="test question",
            retrieved_chunks=chunks,
        )

        system_content = messages[0]["content"]

        # Identity
        assert "ScholarGPT" in system_content

        # Citation instruction
        assert "[Source" in system_content

        # Context-only rule
        assert "ONLY" in system_content or "only" in system_content

        # Anti-hallucination rule
        assert "Do NOT make up" in system_content or "do NOT" in system_content

    def test_system_prompt_contains_references_and_context_headers(self):
        """
        System prompt should include the 'References Used' instruction
        and the 'RESEARCH CONTEXT' header from the spec template.
        """
        chunks = [make_mock_row()]

        from src.services.context_builder import build_prompt

        messages = build_prompt(question="test", retrieved_chunks=chunks)
        system_content = messages[0]["content"]

        assert "References Used" in system_content
        assert "RESEARCH CONTEXT" in system_content

    # ── Edge Case: Very long question preserved exactly ──────────────────

    def test_long_question_preserved(self):
        """
        A very long question should be preserved exactly as provided.
        """
        long_question = "How does " + "deep learning " * 500 + "work?"

        from src.services.context_builder import build_prompt

        messages = build_prompt(
            question=long_question,
            retrieved_chunks=[make_mock_row()],
        )

        assert messages[-1]["content"] == long_question


# ═════════════════════════════════════════════════════════════════════════════
# 3. CONTEXT BUILDER TESTS — _build_context_string()
# ═════════════════════════════════════════════════════════════════════════════


class TestBuildContextString:
    """Tests for context_builder._build_context_string()."""

    def test_empty_chunks_produces_fallback(self):
        """Empty chunks → fallback message."""
        from src.services.context_builder import _build_context_string

        result = _build_context_string([])
        assert "(No relevant context found in uploaded papers.)" in result

    def test_single_chunk_formatting(self):
        """A single chunk should produce a numbered [Source 1] label."""
        chunk = make_mock_row(
            title="Deep Learning in Medicine",
            author="Smith, John",
            year="2020",
            page_number=15,
            similarity=0.87,
            content="Neural networks have shown remarkable performance.",
        )

        from src.services.context_builder import _build_context_string

        result = _build_context_string([chunk])

        assert "[Source 1]" in result
        assert '"Deep Learning in Medicine"' in result
        assert "Smith, John" in result
        assert "2020" in result
        assert "Page 15" in result
        # Relevance scores are no longer in context (saves tokens for LLM)
        assert "Neural networks" in result
        assert "Content:" in result

    def test_multiple_chunks_numbered_sequentially(self):
        """Multiple chunks should be numbered [Source 1], [Source 2], etc."""
        chunks = [make_mock_row(content=f"Content {i}") for i in range(5)]

        from src.services.context_builder import _build_context_string

        result = _build_context_string(chunks)

        for i in range(1, 6):
            assert f"[Source {i}]" in result

    def test_missing_title_uses_filename(self):
        """
        When title is None, the file_name should be used as fallback.
        """
        chunk = make_mock_row(title=None, file_name="fallback_paper.pdf")

        from src.services.context_builder import _build_context_string

        result = _build_context_string([chunk])
        assert "fallback_paper.pdf" in result

    def test_missing_author_uses_unknown(self):
        """When author is None, 'Unknown author' should be used."""
        chunk = make_mock_row(author=None)

        from src.services.context_builder import _build_context_string

        result = _build_context_string([chunk])
        assert "Unknown author" in result

    def test_missing_year_uses_nd(self):
        """When year is None, 'n.d.' should be used."""
        chunk = make_mock_row(year=None)

        from src.services.context_builder import _build_context_string

        result = _build_context_string([chunk])
        assert "n.d." in result

    def test_context_ends_with_separator(self):
        """Context string should end with '---' separator."""
        chunks = [make_mock_row()]

        from src.services.context_builder import _build_context_string

        result = _build_context_string(chunks)
        assert result.strip().endswith("---")

    def test_context_includes_content(self):
        """Each chunk's content should appear in the context string."""
        chunks = [
            make_mock_row(content="First chunk content about ML"),
            make_mock_row(content="Second chunk content about NLP"),
        ]

        from src.services.context_builder import _build_context_string

        result = _build_context_string(chunks)
        assert "First chunk content about ML" in result
        assert "Second chunk content about NLP" in result

    def test_relevance_score_not_in_context(self):
        """Relevance scores should NOT appear in context (saves tokens for LLM)."""
        chunk = make_mock_row(similarity=0.92)

        from src.services.context_builder import _build_context_string

        result = _build_context_string([chunk])
        assert "92%" not in result
        assert "relevance" not in result.lower()

    def test_page_number_question_mark_default(self):
        """When page_number is missing, '?' should be used."""
        chunk = make_mock_row()
        # Remove page_number from dict
        del chunk["page_number"]

        from src.services.context_builder import _build_context_string

        result = _build_context_string([chunk])
        assert "Page ?" in result

    def test_similarity_zero_formatted_correctly(self):
        """Chunk with similarity=0.0 should still be formatted (not skipped)."""
        chunk = make_mock_row(similarity=0.0)

        from src.services.context_builder import _build_context_string

        result = _build_context_string([chunk])
        assert "[Source 1]" in result
        # Relevance scores no longer in context, but chunk is still included
        assert "Content:" in result

    def test_context_string_caps_at_max_chunks(self):
        """Only MAX_CONTEXT_CHUNKS chunks should be included in context."""
        from src.services.context_builder import _build_context_string, MAX_CONTEXT_CHUNKS

        chunks = [make_mock_row(content=f"Chunk {i}") for i in range(15)]
        result = _build_context_string(chunks)

        assert f"[Source {MAX_CONTEXT_CHUNKS}]" in result
        assert f"[Source {MAX_CONTEXT_CHUNKS + 1}]" not in result

    def test_context_string_truncates_long_chunks(self):
        """Chunks longer than MAX_CHUNK_CHARS should be truncated."""
        from src.services.context_builder import _build_context_string, MAX_CHUNK_CHARS

        long_content = "A" * 3000
        chunks = [make_mock_row(content=long_content)]
        result = _build_context_string(chunks)

        # Should not contain full 3000 chars
        assert "A" * (MAX_CHUNK_CHARS + 1) not in result
        # Should contain truncated content
        assert "A" * MAX_CHUNK_CHARS in result


# ═════════════════════════════════════════════════════════════════════════════
# 4. SOURCE SUMMARY TESTS — get_source_summary()
# ═════════════════════════════════════════════════════════════════════════════


class TestGetSourceSummary:
    """Tests for context_builder.get_source_summary()."""

    def test_source_summary_basic(self):
        """Source summary should create numbered entries from chunks."""
        chunks = [
            make_mock_row(
                title="Paper A",
                author="Author A",
                year="2021",
                page_number=5,
                file_name="paper_a.pdf",
                similarity=0.85,
            ),
            make_mock_row(
                title="Paper B",
                author="Author B",
                year="2022",
                page_number=10,
                file_name="paper_b.pdf",
                similarity=0.72,
            ),
        ]

        from src.services.context_builder import get_source_summary

        summaries = get_source_summary(chunks)

        assert len(summaries) == 2

        # First source
        assert summaries[0]["source_number"] == 1
        assert summaries[0]["title"] == "Paper A"
        assert summaries[0]["author"] == "Author A"
        assert summaries[0]["year"] == "2021"
        assert summaries[0]["page_number"] == 5
        assert summaries[0]["file_name"] == "paper_a.pdf"
        assert summaries[0]["similarity"] == 0.85

        # Second source
        assert summaries[1]["source_number"] == 2
        assert summaries[1]["title"] == "Paper B"

    def test_source_summary_empty_chunks(self):
        """Empty chunks → empty summary list."""
        from src.services.context_builder import get_source_summary

        summaries = get_source_summary([])
        assert summaries == []

    def test_source_summary_includes_chunk_and_document_ids(self):
        """Each summary should include chunk_id and document_id."""
        chunk_id = str(uuid.uuid4())
        doc_id = str(uuid.uuid4())
        chunks = [make_mock_row(chunk_id=chunk_id, document_id=doc_id)]

        from src.services.context_builder import get_source_summary

        summaries = get_source_summary(chunks)

        assert summaries[0]["chunk_id"] == chunk_id
        assert summaries[0]["document_id"] == doc_id

    def test_source_summary_excerpt_truncation(self):
        """Content > 200 chars should be truncated with '...' appended."""
        long_content = "A" * 300
        chunks = [make_mock_row(content=long_content)]

        from src.services.context_builder import get_source_summary

        summaries = get_source_summary(chunks)

        excerpt = summaries[0]["excerpt"]
        assert len(excerpt) == 203  # 200 + "..."
        assert excerpt.endswith("...")

    def test_source_summary_short_content_not_truncated(self):
        """Content <= 200 chars should not be truncated."""
        short_content = "Short content"
        chunks = [make_mock_row(content=short_content)]

        from src.services.context_builder import get_source_summary

        summaries = get_source_summary(chunks)

        assert summaries[0]["excerpt"] == "Short content"
        assert not summaries[0]["excerpt"].endswith("...")

    def test_source_summary_exactly_200_chars(self):
        """Content exactly 200 chars should not be truncated."""
        exact_content = "A" * 200
        chunks = [make_mock_row(content=exact_content)]

        from src.services.context_builder import get_source_summary

        summaries = get_source_summary(chunks)

        assert summaries[0]["excerpt"] == exact_content
        assert not summaries[0]["excerpt"].endswith("...")

    def test_source_summary_201_chars_truncated(self):
        """Content of 201 chars should be truncated."""
        content_201 = "A" * 201
        chunks = [make_mock_row(content=content_201)]

        from src.services.context_builder import get_source_summary

        summaries = get_source_summary(chunks)

        assert summaries[0]["excerpt"].endswith("...")
        assert len(summaries[0]["excerpt"]) == 203  # 200 + "..."

    def test_source_summary_null_title_uses_filename(self):
        """
        When title is None, the source summary should use file_name
        as fallback for the title field.
        """
        chunks = [make_mock_row(title=None, file_name="fallback.pdf")]

        from src.services.context_builder import get_source_summary

        summaries = get_source_summary(chunks)

        assert summaries[0]["title"] == "fallback.pdf"

    def test_source_summary_null_fields(self):
        """Null metadata fields should be preserved as None in summary."""
        chunks = [make_mock_row(
            author=None, year=None, page_number=None,
        )]

        from src.services.context_builder import get_source_summary

        summaries = get_source_summary(chunks)

        assert summaries[0]["author"] is None
        assert summaries[0]["year"] is None
        assert summaries[0]["page_number"] is None

    def test_source_summary_numbering_sequential(self):
        """Source numbers should be 1-indexed and sequential."""
        chunks = [make_mock_row() for _ in range(5)]

        from src.services.context_builder import get_source_summary

        summaries = get_source_summary(chunks)

        for i, summary in enumerate(summaries):
            assert summary["source_number"] == i + 1

    def test_source_summary_all_required_fields_present(self):
        """Each source summary must have all required fields."""
        required_fields = {
            "source_number", "title", "author", "year",
            "page_number", "file_name", "document_id",
            "chunk_id", "similarity", "excerpt",
        }
        chunks = [make_mock_row()]

        from src.services.context_builder import get_source_summary

        summaries = get_source_summary(chunks)

        for field in required_fields:
            assert field in summaries[0], f"Missing field: {field}"

    def test_source_summary_both_title_and_filename_none(self):
        """
        When both title and file_name are None, the summary title
        should be None (no fallback available).
        """
        chunks = [make_mock_row(title=None, file_name=None)]

        from src.services.context_builder import get_source_summary

        summaries = get_source_summary(chunks)
        assert summaries[0]["title"] is None
