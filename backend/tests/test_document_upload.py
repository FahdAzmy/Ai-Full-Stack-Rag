"""
Test cases for Document Upload & Management endpoints (SPEC-02).
Following TDD: These tests are written BEFORE implementation.

All tests mock Supabase Storage to avoid hitting real services.
"""

import io
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.helpers.security import hash_password, generate_access_token
from src.models.db_scheams.user import User
from src.models.db_scheams.document import Document


# ── Helpers ──────────────────────────────────────────────────────────────────


async def create_verified_user(db_session: AsyncSession, email: str = "docuser@example.com") -> User:
    """Create a verified user in the DB and return the User object."""
    user = User(
        email=email,
        name="Doc Test User",
        hashed_password=hash_password("SecurePass123"),
        is_verified=True,
        verification_token="123456",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def auth_header(user: User) -> dict:
    """Generate Authorization header with a valid access token for the given user."""
    token = generate_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


def make_pdf_bytes(size_bytes: int = 1024) -> bytes:
    """Create fake PDF content of the given size.

    Starts with the PDF magic bytes so MIME-type validation
    can identify it as a PDF.
    """
    header = b"%PDF-1.4 fake content "
    if size_bytes <= len(header):
        return header[:size_bytes]
    return header + b"\x00" * (size_bytes - len(header))


def make_upload_file(filename: str = "paper.pdf", content: bytes | None = None):
    """Return a tuple suitable for httpx multipart file upload."""
    if content is None:
        content = make_pdf_bytes(5 * 1024)  # 5 KB default
    return {"file": (filename, io.BytesIO(content), "application/pdf")}


def make_docx_upload():
    """Return a .docx file upload (invalid type)."""
    content = b"PK\x03\x04 fake docx"
    return {"file": ("report.docx", io.BytesIO(content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}


async def create_document_in_db(
    db_session: AsyncSession,
    user: User,
    file_name: str = "existing.pdf",
    status: str = "ready",
) -> Document:
    """Insert a Document record directly into the DB for test setup."""
    doc = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        file_name=file_name,
        file_path=f"{user.id}/{uuid.uuid4()}.pdf",
        status=status,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


# ── Fixtures ─────────────────────────────────────────────────────────────────


STORAGE_MOCK_PATH = "src.controllers.document_controller.storage"


@pytest.fixture
def mock_storage():
    """Mock the Supabase Storage helper used by the document controller.

    The controller is expected to import a `storage` helper from
    `src.helpers.storage`.  We patch it at the controller level so
    that no real Supabase calls are made during tests.
    """
    with patch(STORAGE_MOCK_PATH) as mock:
        # upload returns the storage path
        mock.upload = MagicMock(return_value="user_id/doc_id.pdf")
        # download returns bytes
        mock.download = MagicMock(return_value=make_pdf_bytes())
        # delete returns None (success)
        mock.delete = MagicMock(return_value=None)
        # create_signed_url returns a fake URL
        mock.create_signed_url = MagicMock(return_value="https://storage.supabase.co/signed/documents/fake")
        yield mock


@pytest.fixture
def mock_storage_upload_failure():
    """Mock storage where upload always fails."""
    with patch(STORAGE_MOCK_PATH) as mock:
        mock.upload = MagicMock(side_effect=Exception("Storage upload failed"))
        yield mock


@pytest.fixture(autouse=True)
def mock_ingestion_pipeline():
    """Mock process_document to prevent full extraction during upload tests.
    
    This simulates an asynchronous pipeline kicking off by just setting
    the status to "processing" (which the tests expect), avoiding 
    the real Supabase download calls and heavy PyMuPDF parsing.
    """
    async def mock_process(doc_id: str, db: AsyncSession):
        from sqlalchemy import select
        result = await db.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = "processing"
            await db.commit()
            
    with patch("src.controllers.document_controller.process_document", side_effect=mock_process) as mock:
        yield mock


# ═════════════════════════════════════════════════════════════════════════════
# TEST CLASSES
# ═════════════════════════════════════════════════════════════════════════════


class TestDocumentUpload:
    """Test cases for POST /documents/upload — Spec scenarios #1-#5."""

    # ── Scenario #1: Upload valid PDF ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_upload_valid_pdf(
        self, client: AsyncClient, db_session: AsyncSession, mock_storage
    ):
        """Scenario #1: Upload valid 5MB PDF → 201, file saved, DB record created."""
        user = await create_verified_user(db_session)
        pdf_content = make_pdf_bytes(5 * 1024 * 1024)  # 5 MB
        files = make_upload_file("deep_learning.pdf", pdf_content)

        response = await client.post(
            "/documents/upload",
            files=files,
            headers=auth_header(user),
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["file_name"] == "deep_learning.pdf"
        assert data["file_size"] == 5 * 1024 * 1024
        assert data["status"] == "processing"
        assert "message" in data

        # Verify DB record was created
        result = await db_session.execute(
            select(Document).where(Document.id == data["id"])
        )
        doc = result.scalar_one_or_none()
        assert doc is not None
        assert doc.user_id == user.id
        assert doc.status == "processing"

        # Verify storage.upload was called
        mock_storage.upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_small_pdf(
        self, client: AsyncClient, db_session: AsyncSession, mock_storage
    ):
        """Upload a small valid PDF → 201."""
        user = await create_verified_user(db_session)
        files = make_upload_file("small.pdf", make_pdf_bytes(1024))

        response = await client.post(
            "/documents/upload",
            files=files,
            headers=auth_header(user),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["file_name"] == "small.pdf"
        assert data["file_size"] == 1024

    # ── Scenario #2: Upload .docx file ───────────────────────────────────

    @pytest.mark.asyncio
    async def test_upload_non_pdf_rejected(
        self, client: AsyncClient, db_session: AsyncSession, mock_storage
    ):
        """Scenario #2: Upload .docx file → 400, 'Only PDF files are accepted'."""
        user = await create_verified_user(db_session)
        files = make_docx_upload()

        response = await client.post(
            "/documents/upload",
            files=files,
            headers=auth_header(user),
        )

        assert response.status_code == 400
        data = response.json()
        assert "only pdf" in data["detail"].lower() or "pdf" in data["detail"].lower()
        assert ".docx" in data["detail"]

        # Verify storage was NOT called
        mock_storage.upload.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_txt_file_rejected(
        self, client: AsyncClient, db_session: AsyncSession, mock_storage
    ):
        """Upload a .txt file → 400."""
        user = await create_verified_user(db_session)
        files = {"file": ("notes.txt", io.BytesIO(b"plain text"), "text/plain")}

        response = await client.post(
            "/documents/upload",
            files=files,
            headers=auth_header(user),
        )

        assert response.status_code == 400
        assert "pdf" in response.json()["detail"].lower()

    # ── Scenario #3: Upload too-large PDF ────────────────────────────────

    @pytest.mark.asyncio
    async def test_upload_oversized_pdf_rejected(
        self, client: AsyncClient, db_session: AsyncSession, mock_storage
    ):
        """Scenario #3: Upload 60MB PDF → 400, 'File too large'."""
        user = await create_verified_user(db_session)
        # We don't actually create 60MB in memory — we set the content-length
        # or use a smaller payload and rely on the controller reading file.size.
        # For a realistic test, we create a small buffer but mock size checking.
        large_content = make_pdf_bytes(60 * 1024 * 1024)  # 60MB
        files = make_upload_file("huge_paper.pdf", large_content)

        response = await client.post(
            "/documents/upload",
            files=files,
            headers=auth_header(user),
        )

        assert response.status_code == 400
        data = response.json()
        assert "too large" in data["detail"].lower() or "maximum" in data["detail"].lower()

        # Verify storage was NOT called
        mock_storage.upload.assert_not_called()

    # ── Scenario #4: Upload empty file ───────────────────────────────────

    @pytest.mark.asyncio
    async def test_upload_empty_file_rejected(
        self, client: AsyncClient, db_session: AsyncSession, mock_storage
    ):
        """Scenario #4: Upload empty file → 400, 'Uploaded file is empty'."""
        user = await create_verified_user(db_session)
        files = make_upload_file("empty.pdf", b"")

        response = await client.post(
            "/documents/upload",
            files=files,
            headers=auth_header(user),
        )

        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()

        # Verify storage was NOT called
        mock_storage.upload.assert_not_called()

    # ── Scenario #5: Upload without auth ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_upload_without_auth_token(
        self, client: AsyncClient, mock_storage
    ):
        """Scenario #5: Upload without auth token → 401/403."""
        files = make_upload_file("paper.pdf")

        response = await client.post(
            "/documents/upload",
            files=files,
            # No auth header
        )

        assert response.status_code in (401, 403)

    # ── Additional: Storage upload failure ───────────────────────────────

    @pytest.mark.asyncio
    async def test_upload_storage_failure_rolls_back(
        self, client: AsyncClient, db_session: AsyncSession, mock_storage_upload_failure
    ):
        """If Supabase Storage upload fails, DB record should be rolled back."""
        user = await create_verified_user(db_session)
        files = make_upload_file("paper.pdf")

        response = await client.post(
            "/documents/upload",
            files=files,
            headers=auth_header(user),
        )

        assert response.status_code == 500
        data = response.json()
        assert "storage" in data["detail"].lower() or "upload" in data["detail"].lower()

        # Verify no document was left in DB
        result = await db_session.execute(
            select(Document).where(Document.user_id == user.id)
        )
        docs = result.scalars().all()
        assert len(docs) == 0


class TestListDocuments:
    """Test cases for GET /documents/ — Spec scenarios #6-#7."""

    # ── Scenario #6: List documents (has 3) ──────────────────────────────

    @pytest.mark.asyncio
    async def test_list_documents_with_results(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Scenario #6: List documents (has 3) → 200, returns array of 3 items."""
        user = await create_verified_user(db_session)

        # Create 3 documents
        for i in range(3):
            await create_document_in_db(db_session, user, f"paper_{i}.pdf")

        response = await client.get(
            "/documents/",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) == 3
        assert data["total"] == 3

        # Check document structure
        doc = data["documents"][0]
        assert "id" in doc
        assert "file_name" in doc
        assert "status" in doc
        assert "created_at" in doc

    # ── Scenario #7: List documents (has 0) ──────────────────────────────

    @pytest.mark.asyncio
    async def test_list_documents_empty(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Scenario #7: List documents (has 0) → 200, returns empty array."""
        user = await create_verified_user(db_session)

        response = await client.get(
            "/documents/",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) == 0
        assert data["total"] == 0

    # ── Additional: Filter by status ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_documents_filter_by_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """List documents filtered by status → only matching documents returned."""
        user = await create_verified_user(db_session)

        await create_document_in_db(db_session, user, "ready_1.pdf", status="ready")
        await create_document_in_db(db_session, user, "ready_2.pdf", status="ready")
        await create_document_in_db(db_session, user, "processing.pdf", status="processing")

        response = await client.get(
            "/documents/?status=ready",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 2
        for doc in data["documents"]:
            assert doc["status"] == "ready"

    # ── Additional: List without auth ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_documents_without_auth(self, client: AsyncClient):
        """List documents without auth → 401/403."""
        response = await client.get("/documents/")
        assert response.status_code in (401, 403)

    # ── Additional: User isolation ───────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_documents_user_isolation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Each user should only see their own documents."""
        user_a = await create_verified_user(db_session, "user_a@example.com")
        user_b = await create_verified_user(db_session, "user_b@example.com")

        await create_document_in_db(db_session, user_a, "a_paper.pdf")
        await create_document_in_db(db_session, user_a, "a_paper_2.pdf")
        await create_document_in_db(db_session, user_b, "b_paper.pdf")

        # User A should see 2 documents
        response_a = await client.get(
            "/documents/",
            headers=auth_header(user_a),
        )
        assert response_a.status_code == 200
        assert response_a.json()["total"] == 2

        # User B should see 1 document
        response_b = await client.get(
            "/documents/",
            headers=auth_header(user_b),
        )
        assert response_b.status_code == 200
        assert response_b.json()["total"] == 1


class TestGetDocument:
    """Test cases for GET /documents/{document_id} — Spec scenarios #8-#10."""

    # ── Scenario #8: Get document by ID ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_document_by_id(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Scenario #8: Get document by ID → 200, returns full detail."""
        user = await create_verified_user(db_session)
        doc = await create_document_in_db(db_session, user, "detailed.pdf")

        response = await client.get(
            f"/documents/{doc.id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(doc.id)
        assert data["file_name"] == "detailed.pdf"
        assert data["status"] == "ready"
        assert "created_at" in data
        assert "updated_at" in data

    # ── Scenario #9: Get another user's document ─────────────────────────

    @pytest.mark.asyncio
    async def test_get_other_users_document(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Scenario #9: Get another user's document → 403, 'Access denied'."""
        owner = await create_verified_user(db_session, "owner@example.com")
        intruder = await create_verified_user(db_session, "intruder@example.com")
        doc = await create_document_in_db(db_session, owner, "private.pdf")

        response = await client.get(
            f"/documents/{doc.id}",
            headers=auth_header(intruder),
        )

        assert response.status_code == 403
        data = response.json()
        assert "access denied" in data["detail"].lower() or "denied" in data["detail"].lower()

    # ── Scenario #10: Get non-existent document ──────────────────────────

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Scenario #10: Get non-existent document → 404, 'Document not found'."""
        user = await create_verified_user(db_session)
        fake_id = uuid.uuid4()

        response = await client.get(
            f"/documents/{fake_id}",
            headers=auth_header(user),
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    # ── Additional: Get document without auth ────────────────────────────

    @pytest.mark.asyncio
    async def test_get_document_without_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Get document without auth → 401/403."""
        user = await create_verified_user(db_session)
        doc = await create_document_in_db(db_session, user)

        response = await client.get(f"/documents/{doc.id}")
        assert response.status_code in (401, 403)


class TestUpdateDocument:
    """Test cases for PATCH /documents/{document_id} — Spec scenario #11."""

    # ── Scenario #11: Update document metadata ───────────────────────────

    @pytest.mark.asyncio
    async def test_update_document_metadata(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Scenario #11: Update document metadata → 200, metadata updated in DB."""
        user = await create_verified_user(db_session)
        doc = await create_document_in_db(db_session, user)

        update_data = {
            "title": "Deep Learning in Medical Imaging: A Survey",
            "author": "Smith, John A. and Doe, Jane B.",
            "year": "2020",
            "journal": "Journal of AI Research",
            "doi": "10.1234/jair.2020.001",
        }

        response = await client.patch(
            f"/documents/{doc.id}",
            json=update_data,
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["id"] == str(doc.id)

        # Verify metadata was persisted in DB
        await db_session.refresh(doc)
        assert doc.title == "Deep Learning in Medical Imaging: A Survey"
        assert doc.author == "Smith, John A. and Doe, Jane B."
        assert doc.year == "2020"
        assert doc.journal == "Journal of AI Research"
        assert doc.doi == "10.1234/jair.2020.001"

    @pytest.mark.asyncio
    async def test_update_partial_metadata(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Partial update — only provided fields are updated."""
        user = await create_verified_user(db_session)
        doc = await create_document_in_db(db_session, user)

        response = await client.patch(
            f"/documents/{doc.id}",
            json={"title": "Only Title Updated"},
            headers=auth_header(user),
        )

        assert response.status_code == 200

        await db_session.refresh(doc)
        assert doc.title == "Only Title Updated"
        # Other fields should remain None
        assert doc.author is None

    @pytest.mark.asyncio
    async def test_update_other_users_document(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Update another user's document → 403."""
        owner = await create_verified_user(db_session, "owner2@example.com")
        intruder = await create_verified_user(db_session, "intruder2@example.com")
        doc = await create_document_in_db(db_session, owner)

        response = await client.patch(
            f"/documents/{doc.id}",
            json={"title": "Hacked Title"},
            headers=auth_header(intruder),
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_nonexistent_document(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Update non-existent document → 404."""
        user = await create_verified_user(db_session)
        fake_id = uuid.uuid4()

        response = await client.patch(
            f"/documents/{fake_id}",
            json={"title": "Doesn't Exist"},
            headers=auth_header(user),
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_document_without_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Update document without auth → 401/403."""
        user = await create_verified_user(db_session)
        doc = await create_document_in_db(db_session, user)

        response = await client.patch(
            f"/documents/{doc.id}",
            json={"title": "No Auth"},
        )

        assert response.status_code in (401, 403)


class TestDeleteDocument:
    """Test cases for DELETE /documents/{document_id} — Spec scenarios #12-#13."""

    # ── Scenario #12: Delete document ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_delete_document(
        self, client: AsyncClient, db_session: AsyncSession, mock_storage
    ):
        """Scenario #12: Delete document → 200, file deleted, DB record deleted."""
        user = await create_verified_user(db_session)
        doc = await create_document_in_db(db_session, user, "to_delete.pdf")
        doc_id = doc.id

        response = await client.delete(
            f"/documents/{doc_id}",
            headers=auth_header(user),
        )

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()

        # Verify DB record was deleted
        result = await db_session.execute(
            select(Document).where(Document.id == doc_id)
        )
        assert result.scalar_one_or_none() is None

        # Verify storage.delete was called
        mock_storage.delete.assert_called_once()

    # ── Scenario #13: Delete non-existent document ───────────────────────

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(
        self, client: AsyncClient, db_session: AsyncSession, mock_storage
    ):
        """Scenario #13: Delete non-existent document → 404, 'Document not found'."""
        user = await create_verified_user(db_session)
        fake_id = uuid.uuid4()

        response = await client.delete(
            f"/documents/{fake_id}",
            headers=auth_header(user),
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_other_users_document(
        self, client: AsyncClient, db_session: AsyncSession, mock_storage
    ):
        """Delete another user's document → 403."""
        owner = await create_verified_user(db_session, "del_owner@example.com")
        intruder = await create_verified_user(db_session, "del_intruder@example.com")
        doc = await create_document_in_db(db_session, owner, "private.pdf")

        response = await client.delete(
            f"/documents/{doc.id}",
            headers=auth_header(intruder),
        )

        assert response.status_code == 403

        # Verify document was NOT deleted from DB
        result = await db_session.execute(
            select(Document).where(Document.id == doc.id)
        )
        assert result.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_delete_document_without_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Delete document without auth → 401/403."""
        user = await create_verified_user(db_session)
        doc = await create_document_in_db(db_session, user)

        response = await client.delete(f"/documents/{doc.id}")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_delete_continues_even_if_storage_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """If storage delete fails, DB records should still be deleted (per spec)."""
        user = await create_verified_user(db_session)
        doc = await create_document_in_db(db_session, user, "orphan.pdf")
        doc_id = doc.id

        with patch(STORAGE_MOCK_PATH) as mock_st:
            mock_st.delete = MagicMock(side_effect=Exception("Storage unavailable"))

            response = await client.delete(
                f"/documents/{doc_id}",
                headers=auth_header(user),
            )

        # Should still succeed (200) even though storage failed
        assert response.status_code == 200

        # DB record should be gone
        result = await db_session.execute(
            select(Document).where(Document.id == doc_id)
        )
        assert result.scalar_one_or_none() is None
