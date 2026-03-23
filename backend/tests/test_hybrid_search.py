"""
Test cases for Hybrid Search (SPEC-08 — Part 3).
Following TDD: These tests are written BEFORE implementation.

Tests are organized by functionality:
  1. TestHybridSearchBasic        — Core hybrid search behavior
  2. TestHybridSearchWeights      — Weight parameter tuning
  3. TestHybridSearchFilters      — Document filtering & user isolation
  4. TestHybridSearchEdgeCases    — Edge cases & error handling
  5. TestHybridSearchResultFormat — Output structure validation

All external dependencies (OpenAI embedding API) are mocked.
Database tests use the test database with real pgvector queries.

Spec Scenarios Covered:
  #7  Hybrid search finds keyword matches
  #8  Hybrid search with rare term → better results than vector-only
"""

import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.helpers.security import hash_password
from src.models.db_scheams.user import User
from src.models.db_scheams.document import Document
from src.models.db_scheams.DocumentChunk import DocumentChunk


# ── Helpers ──────────────────────────────────────────────────────────────────


async def create_verified_user(
    db_session: AsyncSession, email: str = "hybrid@example.com"
) -> User:
    """Create a verified user in the DB and return the User object."""
    user = User(
        email=email,
        name="Hybrid Test User",
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
    chunk_contents: list[str] | None = None,
    embedding: list[float] | None = None,
) -> tuple[Document, list[DocumentChunk]]:
    """Create a document with chunks in the DB for test setup.

    If chunk_contents is provided, it overrides num_chunks with specific content.
    """
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

    contents = chunk_contents or [
        f"Content of chunk {i} from {file_name}. " * 20
        for i in range(num_chunks)
    ]

    chunks = []
    for i, content in enumerate(contents):
        chunk = DocumentChunk(
            id=uuid.uuid4(),
            user_id=user.id,
            document_id=doc.id,
            content=content,
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


# ═════════════════════════════════════════════════════════════════════════════
# 1. HYBRID SEARCH BASIC TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestHybridSearchBasic:
    """Tests for retrieval_service.hybrid_search() — core behavior."""

    # ── hybrid_search function exists ────────────────────────────────────

    def test_hybrid_search_function_exists(self):
        """The retrieval_service module should export a hybrid_search function."""
        from src.services.retrieval_service import hybrid_search

        assert callable(hybrid_search)

    # ── Returns results for a matching query ─────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_returns_results(self, db_session: AsyncSession):
        """Hybrid search with a matching query should return results."""
        user = await create_verified_user(db_session)
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="test query about the paper",
                user_id=str(user.id),
                db=db_session,
                top_k=5,
            )

        assert len(results) > 0

    # ── Results are sorted by combined score (descending) ────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_results_sorted_by_combined_score(
        self, db_session: AsyncSession
    ):
        """Results should be ordered by combined_score descending."""
        user = await create_verified_user(db_session, "sorted@example.com")
        doc, _ = await create_document_with_chunks(
            db_session, user, num_chunks=5
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                top_k=10,
            )

        if len(results) > 1:
            # Combined scores should be in descending order
            scores = [r["similarity"] for r in results]
            assert scores == sorted(scores, reverse=True), (
                f"Results not sorted by combined score: {scores}"
            )

    # ── Scenario #7: Finds keyword matches ───────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_finds_keyword_matches(
        self, db_session: AsyncSession
    ):
        """
        Scenario #7: Hybrid search should find chunks that match keywords
        even if vector similarity alone might not rank them highly.
        """
        user = await create_verified_user(db_session, "keyword@example.com")

        # Create chunks with specific keyword-rich content
        chunk_contents = [
            "Machine learning algorithms for natural language processing and transformers are revolutionary.",
            "The CRISPR-Cas9 gene editing technique has transformed molecular biology research forever.",
            "Quantum computing uses qubits to perform parallel computations on quantum states.",
        ]

        doc, _ = await create_document_with_chunks(
            db_session, user,
            chunk_contents=chunk_contents,
            # All embeddings are similar (so vector search doesn't differentiate)
            embedding=[0.1] * 1536,
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="CRISPR gene editing",
                user_id=str(user.id),
                db=db_session,
                top_k=3,
            )

        # With keyword matching, the CRISPR chunk should appear in results
        assert len(results) > 0
        contents = [r["content"] for r in results]
        has_crispr = any("CRISPR" in c for c in contents)
        assert has_crispr, "Hybrid search should find the keyword-matching chunk"

    # ── Uses both vector AND keyword scoring ─────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_combines_vector_and_keyword(
        self, db_session: AsyncSession
    ):
        """Each result should have a combined score from both vector and keyword signals."""
        user = await create_verified_user(db_session, "combined@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="test paper content",
                user_id=str(user.id),
                db=db_session,
                top_k=5,
            )

        # Results should have a similarity score (combined)
        for result in results:
            assert "similarity" in result
            assert isinstance(result["similarity"], float)


# ═════════════════════════════════════════════════════════════════════════════
# 2. HYBRID SEARCH WEIGHT TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestHybridSearchWeights:
    """Tests for hybrid search weight parameters."""

    # ── Default weights are 0.7 vector, 0.3 keyword ──────────────────────

    @pytest.mark.asyncio
    async def test_default_weights(self, db_session: AsyncSession):
        """Default vector_weight=0.7, keyword_weight=0.3 per spec."""
        user = await create_verified_user(db_session, "defaults@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            # Should work without providing weight args
            results = await hybrid_search(
                query="test query",
                user_id=str(user.id),
                db=db_session,
            )

        # Should not raise, should return results
        assert isinstance(results, list)

    # ── Custom weights are respected ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_custom_weights_accepted(self, db_session: AsyncSession):
        """Custom vector_weight and keyword_weight should be accepted."""
        user = await create_verified_user(db_session, "custom_w@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            # Keyword-heavy search
            results_keyword = await hybrid_search(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                vector_weight=0.2,
                keyword_weight=0.8,
            )

            # Vector-heavy search
            results_vector = await hybrid_search(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                vector_weight=0.9,
                keyword_weight=0.1,
            )

        # Both should return results without error
        assert isinstance(results_keyword, list)
        assert isinstance(results_vector, list)

    # ── 100% vector weight == pure vector search ─────────────────────────

    @pytest.mark.asyncio
    async def test_full_vector_weight(self, db_session: AsyncSession):
        """With keyword_weight=0, results should be purely vector-based."""
        user = await create_verified_user(db_session, "vector_only@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                vector_weight=1.0,
                keyword_weight=0.0,
            )

        assert isinstance(results, list)

    # ── 100% keyword weight == pure keyword search ───────────────────────

    @pytest.mark.asyncio
    async def test_full_keyword_weight(self, db_session: AsyncSession):
        """With vector_weight=0, results should be purely keyword-based."""
        user = await create_verified_user(db_session, "keyword_only@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="Content chunk",
                user_id=str(user.id),
                db=db_session,
                vector_weight=0.0,
                keyword_weight=1.0,
            )

        assert isinstance(results, list)


# ═════════════════════════════════════════════════════════════════════════════
# 3. HYBRID SEARCH FILTER TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestHybridSearchFilters:
    """Tests for hybrid search filtering — documents, users, status."""

    # ── Filter by document_ids ───────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_with_document_ids_filter(
        self, db_session: AsyncSession
    ):
        """Passing document_ids should restrict results to those documents."""
        user = await create_verified_user(db_session, "filter@example.com")

        doc1, _ = await create_document_with_chunks(
            db_session, user, file_name="doc_a.pdf", title="Doc A"
        )
        doc2, _ = await create_document_with_chunks(
            db_session, user, file_name="doc_b.pdf", title="Doc B"
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                top_k=10,
                document_ids=[str(doc1.id)],
            )

        # All results should be from doc1 only
        for result in results:
            assert result["document_id"] == str(doc1.id)

    # ── User isolation enforced ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_user_isolation(self, db_session: AsyncSession):
        """User A cannot see User B's documents in hybrid search."""
        user_a = await create_verified_user(db_session, "h_user_a@example.com")
        user_b = await create_verified_user(db_session, "h_user_b@example.com")

        doc_a, _ = await create_document_with_chunks(
            db_session, user_a, file_name="a_paper.pdf"
        )
        doc_b, _ = await create_document_with_chunks(
            db_session, user_b, file_name="b_paper.pdf"
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results_a = await hybrid_search(
                query="test query",
                user_id=str(user_a.id),
                db=db_session,
                top_k=20,
            )

        for result in results_a:
            assert result["document_id"] == str(doc_a.id)
            assert result["document_id"] != str(doc_b.id)

    # ── Only "ready" documents are searched ──────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_excludes_non_ready_documents(
        self, db_session: AsyncSession
    ):
        """Documents with status != 'ready' should not appear in results."""
        user = await create_verified_user(db_session, "h_status@example.com")

        ready_doc, _ = await create_document_with_chunks(
            db_session, user, file_name="ready.pdf", status="ready"
        )
        processing_doc, _ = await create_document_with_chunks(
            db_session, user, file_name="processing.pdf", status="processing"
        )
        failed_doc, _ = await create_document_with_chunks(
            db_session, user, file_name="failed.pdf", status="failed"
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                top_k=20,
            )

        result_doc_ids = {r["document_id"] for r in results}
        assert str(ready_doc.id) in result_doc_ids or len(results) == 0
        assert str(processing_doc.id) not in result_doc_ids
        assert str(failed_doc.id) not in result_doc_ids

    # ── top_k limits results ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_respects_top_k(self, db_session: AsyncSession):
        """top_k should limit the number of results returned."""
        user = await create_verified_user(db_session, "h_topk@example.com")
        doc, _ = await create_document_with_chunks(
            db_session, user, num_chunks=10
        )

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                top_k=3,
            )

        assert len(results) <= 3


# ═════════════════════════════════════════════════════════════════════════════
# 4. HYBRID SEARCH EDGE CASES
# ═════════════════════════════════════════════════════════════════════════════


class TestHybridSearchEdgeCases:
    """Edge cases and error handling for hybrid search."""

    # ── No documents → returns empty list ────────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_no_documents_returns_empty(
        self, db_session: AsyncSession
    ):
        """A user with no documents should get an empty results list."""
        user = await create_verified_user(db_session, "h_empty@example.com")

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="any question",
                user_id=str(user.id),
                db=db_session,
            )

        assert results == []

    # ── Non-existent user_id → returns empty ─────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_nonexistent_user_returns_empty(
        self, db_session: AsyncSession
    ):
        """A fake user_id should return empty results, not crash."""
        fake_user_id = str(uuid.uuid4())
        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="test query",
                user_id=fake_user_id,
                db=db_session,
            )

        assert results == []

    # ── Empty query string ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_empty_query(self, db_session: AsyncSession):
        """An empty query should not crash."""
        user = await create_verified_user(db_session, "h_empty_q@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="",
                user_id=str(user.id),
                db=db_session,
            )

        assert isinstance(results, list)

    # ── Embedding service failure propagates ──────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_embedding_failure_propagates(
        self, db_session: AsyncSession
    ):
        """If embedding generation fails, the error should propagate."""
        user = await create_verified_user(db_session, "h_emb_fail@example.com")

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            side_effect=Exception("Embedding API error"),
        ):
            from src.services.retrieval_service import hybrid_search

            with pytest.raises(Exception, match="Embedding API error"):
                await hybrid_search(
                    query="fail query",
                    user_id=str(user.id),
                    db=db_session,
                )

    # ── Non-string query raises ValueError ───────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_non_string_query_raises(
        self, db_session: AsyncSession
    ):
        """Passing non-string query should raise ValueError."""
        user = await create_verified_user(db_session, "h_invalid@example.com")

        from src.services.retrieval_service import hybrid_search

        with pytest.raises(ValueError, match="Query must be a string"):
            await hybrid_search(
                query=12345,  # Not a string
                user_id=str(user.id),
                db=db_session,
            )

    # ── Invalid user_id format raises ValueError ─────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_invalid_user_id_raises(
        self, db_session: AsyncSession
    ):
        """Passing invalid user_id should raise ValueError."""
        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            with pytest.raises(ValueError, match="Invalid user_id"):
                await hybrid_search(
                    query="test",
                    user_id="not-a-valid-uuid",
                    db=db_session,
                )

    # ── DI embedder parameter is supported ───────────────────────────────

    @pytest.mark.asyncio
    async def test_hybrid_search_supports_embedder_injection(
        self, db_session: AsyncSession
    ):
        """hybrid_search should accept an optional embedder parameter for DI."""
        user = await create_verified_user(db_session, "h_di@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        custom_embedder = MagicMock(return_value=[0.1] * 1536)

        from src.services.retrieval_service import hybrid_search

        results = await hybrid_search(
            query="test query",
            user_id=str(user.id),
            db=db_session,
            embedder=custom_embedder,
        )

        custom_embedder.assert_called_once_with("test query")
        assert isinstance(results, list)


# ═════════════════════════════════════════════════════════════════════════════
# 5. HYBRID SEARCH RESULT FORMAT TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestHybridSearchResultFormat:
    """Tests for the structure and field types of hybrid search results."""

    # ── All required fields present ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_result_has_all_required_fields(self, db_session: AsyncSession):
        """Each result dict should have all the expected fields."""
        user = await create_verified_user(db_session, "h_fields@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                top_k=5,
            )

        assert len(results) > 0

        required_fields = [
            "chunk_id", "content", "page_number", "chunk_index",
            "document_id", "file_name", "title", "author",
            "year", "journal", "doi", "similarity",
        ]

        for result in results:
            for field in required_fields:
                assert field in result, f"Missing field: {field}"

    # ── Field types are correct ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_result_field_types(self, db_session: AsyncSession):
        """chunk_id and document_id should be string UUIDs, similarity should be float."""
        user = await create_verified_user(db_session, "h_types@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="type check",
                user_id=str(user.id),
                db=db_session,
                top_k=5,
            )

        for result in results:
            assert isinstance(result["chunk_id"], str)
            assert isinstance(result["document_id"], str)
            assert isinstance(result["content"], str)
            assert isinstance(result["similarity"], float)

            # Verify UUIDs are valid
            uuid.UUID(result["chunk_id"])
            uuid.UUID(result["document_id"])

    # ── Similarity score is a valid float ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_similarity_is_rounded_float(self, db_session: AsyncSession):
        """Similarity score should be rounded to 4 decimal places."""
        user = await create_verified_user(db_session, "h_round@example.com")
        doc, _ = await create_document_with_chunks(db_session, user)

        mock_embedding = [0.1] * 1536

        with patch(
            "src.services.retrieval_service.generate_single_embedding",
            return_value=mock_embedding,
        ):
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="test query",
                user_id=str(user.id),
                db=db_session,
            )

        for result in results:
            sim = result["similarity"]
            assert sim == round(sim, 4)

    # ── Results with null metadata fields handle gracefully ───────────────

    @pytest.mark.asyncio
    async def test_results_with_null_metadata(self, db_session: AsyncSession):
        """Documents with null metadata should still return valid results."""
        user = await create_verified_user(db_session, "h_null@example.com")
        doc, _ = await create_document_with_chunks(
            db_session, user,
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
            from src.services.retrieval_service import hybrid_search

            results = await hybrid_search(
                query="test query",
                user_id=str(user.id),
                db=db_session,
                top_k=5,
            )

        assert len(results) > 0
        for result in results:
            # Null metadata fields should be None, not crash
            assert result["title"] is None
            assert result["author"] is None
