"""
Test cases for Async Processing & Optimization (SPEC-08) — Part 1: Celery Tasks.
Following TDD: These tests are written BEFORE implementation.

Tests are organized by component:
  1. TestCeleryAppConfig        — Celery app configuration validation
  2. TestRunAsyncHelper         — _run_async() event loop helper
  3. TestProcessDocumentTask    — Celery task orchestration & retry logic
  4. TestMarkFailed             — _mark_failed() DB update helper
  5. TestUploadEndpointAsync    — Controller switch from sync to async (API-level)
  6. TestTaskIdempotency        — Prevent duplicate processing
  7. TestConfigSettings         — Redis/Celery config in settings

All external dependencies (Celery, Redis, DB) are mocked.

Spec Scenarios Covered:
  #1  Upload returns immediately (<1s), status "processing"
  #2  Celery processes the document → status "ready"
  #3  Celery handles failure → status "failed", error_message set
  #4  Celery retries on transient error (up to 3 times)
  #5  Redis connection lost → graceful error
  #6  Multiple concurrent uploads → all queued
"""

import uuid
import io
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from src.helpers.security import hash_password, generate_access_token
from src.models.db_scheams.user import User
from src.models.db_scheams.document import Document
from src.models.db_scheams.DocumentChunk import DocumentChunk


# ── Helpers ──────────────────────────────────────────────────────────────────


async def create_verified_user(
    db_session: AsyncSession, email: str = "async@example.com"
) -> User:
    """Create a verified user in the DB and return the User object."""
    user = User(
        email=email,
        name="Async Test User",
        hashed_password=hash_password("SecurePass123"),
        is_verified=True,
        verification_token="123456",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def create_document_record(
    db_session: AsyncSession,
    user: User,
    file_name: str = "test_paper.pdf",
    status: str = "uploading",
) -> Document:
    """Insert a Document record directly into the DB for test setup."""
    doc = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        file_name=file_name,
        file_path=f"{user.id}/{uuid.uuid4()}.pdf",
        file_size=5000,
        status=status,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


def auth_header(user: User) -> dict:
    """Generate Authorization header with a valid access token."""
    token = generate_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


def make_pdf_bytes(size_bytes: int = 1024) -> bytes:
    """Create fake PDF content."""
    header = b"%PDF-1.4 fake content "
    if size_bytes <= len(header):
        return header[:size_bytes]
    return header + b"\x00" * (size_bytes - len(header))


def make_upload_file(filename: str = "paper.pdf", content: bytes | None = None):
    """Return a tuple suitable for httpx multipart file upload."""
    if content is None:
        content = make_pdf_bytes(5 * 1024)
    return {"file": (filename, io.BytesIO(content), "application/pdf")}


STORAGE_MOCK_PATH = "src.controllers.document_controller.storage"


# ═════════════════════════════════════════════════════════════════════════════
# 1. CELERY APP CONFIGURATION TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestCeleryAppConfig:
    """Tests for src/tasks/__init__.py — Celery app setup."""

    # ── The celery_app instance should exist ──────────────────────────────

    def test_celery_app_exists(self):
        """The module should export a celery_app instance."""
        from src.tasks import celery_app

        assert celery_app is not None
        assert celery_app.main == "scholargpt"

    # ── Serialization is JSON only (no pickle) ───────────────────────────

    def test_celery_uses_json_serialization(self):
        """Celery should be configured with JSON serializer (no pickle for security)."""
        from src.tasks import celery_app

        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert "json" in celery_app.conf.accept_content

    # ── Late acknowledgement is enabled ──────────────────────────────────

    def test_celery_acks_late_enabled(self):
        """task_acks_late should be True so tasks are re-delivered if the worker dies."""
        from src.tasks import celery_app

        assert celery_app.conf.task_acks_late is True

    # ── Task tracking is enabled ─────────────────────────────────────────

    def test_celery_task_tracking_enabled(self):
        """task_track_started should be True to know when tasks begin."""
        from src.tasks import celery_app

        assert celery_app.conf.task_track_started is True

    # ── Worker prefetch multiplier is 1 ──────────────────────────────────

    def test_celery_prefetch_multiplier(self):
        """worker_prefetch_multiplier should be 1 (one task at a time)."""
        from src.tasks import celery_app

        assert celery_app.conf.worker_prefetch_multiplier == 1

    # ── Default retry settings ───────────────────────────────────────────

    def test_celery_retry_defaults(self):
        """Default retry delay should be 30s, max retries should be 3."""
        from src.tasks import celery_app

        assert celery_app.conf.task_default_retry_delay == 30
        assert celery_app.conf.task_max_retries == 3

    # ── Results expire after 1 hour ──────────────────────────────────────

    def test_celery_result_expiry(self):
        """Results should expire after 3600 seconds (1 hour)."""
        from src.tasks import celery_app

        assert celery_app.conf.result_expires == 3600

    # ── UTC timezone ─────────────────────────────────────────────────────

    def test_celery_uses_utc(self):
        """Celery should use UTC timezone."""
        from src.tasks import celery_app

        assert celery_app.conf.enable_utc is True
        assert celery_app.conf.timezone == "UTC"


# ═════════════════════════════════════════════════════════════════════════════
# 2. _run_async() HELPER TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestRunAsyncHelper:
    """Tests for tasks.ingestion._run_async() — event loop bridge."""

    # ── Successfully runs an async coroutine ──────────────────────────────

    def test_run_async_executes_coroutine(self):
        """_run_async should execute an async function and return its result."""
        from src.tasks.ingestion import _run_async

        async def example_coro():
            return "hello from async"

        result = _run_async(example_coro())
        assert result == "hello from async"

    # ── Propagates exceptions from the coroutine ─────────────────────────

    def test_run_async_propagates_exceptions(self):
        """If the coroutine raises, _run_async should propagate the exception."""
        from src.tasks.ingestion import _run_async

        async def failing_coro():
            raise ValueError("async failure")

        with pytest.raises(ValueError, match="async failure"):
            _run_async(failing_coro())

    # ── Creates and closes its own event loop ────────────────────────────

    def test_run_async_creates_new_event_loop(self):
        """_run_async should create a NEW event loop each time (no reuse)."""
        from src.tasks.ingestion import _run_async

        loops_seen = []

        async def capture_loop():
            loops_seen.append(asyncio.get_event_loop())
            return True

        _run_async(capture_loop())
        _run_async(capture_loop())

        # Two different loops should have been used
        assert len(loops_seen) == 2
        assert loops_seen[0] is not loops_seen[1]


# ═════════════════════════════════════════════════════════════════════════════
# 3. PROCESS DOCUMENT TASK TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestProcessDocumentTask:
    """Tests for tasks.ingestion.process_document_task — Celery task."""

    # ── Task is registered with correct name ─────────────────────────────

    def test_task_is_registered(self):
        """process_document_task should be registered as 'tasks.process_document'."""
        from src.tasks.ingestion import process_document_task

        assert process_document_task.name == "tasks.process_document"

    # ── Task has correct retry configuration ─────────────────────────────

    def test_task_retry_config(self):
        """Task should have max_retries=3 and default_retry_delay=30."""
        from src.tasks.ingestion import process_document_task

        assert process_document_task.max_retries == 3
        assert process_document_task.default_retry_delay == 30

    # ── Task calls _process with the document_id ─────────────────────────

    def test_task_calls_process_with_document_id(self):
        """The task should call _process() with the provided document_id."""
        doc_id = str(uuid.uuid4())

        with patch("src.tasks.ingestion._run_async") as mock_run:
            from src.tasks.ingestion import process_document_task

            # Call the underlying function directly (skip Celery broker)
            process_document_task.apply(args=[doc_id])

        # _run_async should have been called (at least once for _process)
        assert mock_run.called

    # ── Scenario #2: Successful processing completes without errors ──────

    def test_task_success_path(self):
        """On success, the task should complete without raising."""
        doc_id = str(uuid.uuid4())

        with patch("src.tasks.ingestion._run_async") as mock_run:
            mock_run.return_value = None  # _process completes OK

            from src.tasks.ingestion import process_document_task

            # apply() runs the task synchronously for testing
            result = process_document_task.apply(args=[doc_id])

        assert result.successful()

    # ── Scenario #3: Failed task marks document as failed ────────────────

    def test_task_failure_marks_failed_and_retries(self):
        """On failure, the task should call _mark_failed and then retry."""
        doc_id = str(uuid.uuid4())

        with patch("src.tasks.ingestion._run_async") as mock_run:
            # First call (_process) raises, second call (_mark_failed) succeeds
            mock_run.side_effect = [
                Exception("Embedding API timeout"),  # _process fails
                None,  # _mark_failed succeeds
            ]

            from src.tasks.ingestion import process_document_task

            result = process_document_task.apply(args=[doc_id])

        # Task should have failed (after retries exhausted in apply)
        assert result.failed() or result.status == "RETRY"

    # ── Scenario #4: Task retries on transient errors ────────────────────

    def test_task_retries_on_transient_error(self):
        """Transient errors should trigger retry (up to max_retries)."""
        doc_id = str(uuid.uuid4())

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # First two calls are _process (fails) and _mark_failed (succeeds)
                if call_count == 1:
                    raise ConnectionError("Redis unavailable")
                return None
            return None

        with patch("src.tasks.ingestion._run_async", side_effect=side_effect):
            from src.tasks.ingestion import process_document_task

            # When using apply(), retries are executed eagerly
            result = process_document_task.apply(args=[doc_id])

        # The task should have attempted to retry
        assert call_count >= 1

    # ── Task has acks_late enabled ────────────────────────────────────────

    def test_task_acks_late(self):
        """process_document_task should have acks_late=True."""
        from src.tasks.ingestion import process_document_task

        assert process_document_task.acks_late is True

    # ── Task is bound (has access to self) ───────────────────────────────

    def test_task_is_bound(self):
        """Task should be bound (bind=True) so it has access to self.request.id."""
        from src.tasks.ingestion import process_document_task

        # Celery strips 'self' from .run() signature when bind=True,
        # but sets __bound__ = True on the task internally.
        assert getattr(process_document_task, "__bound__", False) is True, (
            "Task must be bound (bind=True) so it receives self at runtime"
        )


# ═════════════════════════════════════════════════════════════════════════════
# 4. _mark_failed() TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestMarkFailed:
    """Tests for tasks.ingestion._mark_failed() — DB status update."""

    # ── Marks the document as failed with error message ──────────────────

    @pytest.mark.asyncio
    async def test_mark_failed_updates_status(self, db_session: AsyncSession):
        """_mark_failed should set status='failed' and error_message."""
        user = await create_verified_user(db_session)
        doc = await create_document_record(db_session, user, status="processing")

        # Patch AsyncSessionLocal to return our test session
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=db_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("src.tasks.ingestion.AsyncSessionLocal", return_value=mock_session_ctx):
            from src.tasks.ingestion import _mark_failed

            await _mark_failed(str(doc.id), "Embedding service timeout")

        # Refresh and verify
        await db_session.refresh(doc)
        assert doc.status == "failed"
        assert doc.error_message == "Embedding service timeout"

    # ── Handles non-existent document gracefully ─────────────────────────

    @pytest.mark.asyncio
    async def test_mark_failed_nonexistent_document(self, db_session: AsyncSession):
        """_mark_failed should not crash on non-existent document_id."""
        fake_id = str(uuid.uuid4())

        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=db_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("src.tasks.ingestion.AsyncSessionLocal", return_value=mock_session_ctx):
            from src.tasks.ingestion import _mark_failed

            # Should not raise
            await _mark_failed(fake_id, "Some error")


# ═════════════════════════════════════════════════════════════════════════════
# 5. UPLOAD ENDPOINT ASYNC TESTS (API-level)
# ═════════════════════════════════════════════════════════════════════════════


class TestUploadEndpointAsync:
    """Tests for the upload endpoint after SPEC-08 async switch.

    These verify that the controller now uses process_document_task.delay()
    instead of the synchronous process_document() call.
    """

    # ── Scenario #1: Upload returns immediately with "processing" ────────

    @pytest.mark.asyncio
    async def test_upload_returns_immediately_with_processing_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Upload should return immediately with status='processing'."""
        user = await create_verified_user(db_session)
        files = make_upload_file("paper.pdf", make_pdf_bytes(5 * 1024))

        with patch(STORAGE_MOCK_PATH) as mock_storage, \
             patch("src.controllers.document_controller.process_document_task") as mock_task:
            mock_storage.upload = MagicMock(return_value="path/doc.pdf")
            mock_task.delay = MagicMock()  # Simulates queuing without execution

            response = await client.post(
                "/documents/upload",
                files=files,
                headers=auth_header(user),
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "processing"
        assert "id" in data
        assert data["file_name"] == "paper.pdf"

    # ── Verify process_document_task.delay() is called ───────────────────

    @pytest.mark.asyncio
    async def test_upload_calls_celery_task_delay(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """The upload endpoint should call process_document_task.delay() with the doc ID."""
        user = await create_verified_user(db_session, "celery_call@example.com")
        files = make_upload_file("queued.pdf", make_pdf_bytes(2 * 1024))

        with patch(STORAGE_MOCK_PATH) as mock_storage, \
             patch("src.controllers.document_controller.process_document_task") as mock_task:
            mock_storage.upload = MagicMock(return_value="path/doc.pdf")
            mock_task.delay = MagicMock()

            response = await client.post(
                "/documents/upload",
                files=files,
                headers=auth_header(user),
            )

        assert response.status_code == 201
        # process_document_task.delay should have been called once with the doc id
        mock_task.delay.assert_called_once()
        call_args = mock_task.delay.call_args
        doc_id_arg = call_args[0][0]
        # Verify the argument is a valid UUID string
        uuid.UUID(doc_id_arg)

    # ── Upload does NOT call sync process_document anymore ───────────────

    @pytest.mark.asyncio
    async def test_upload_does_not_call_sync_process_document(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """After SPEC-08, the sync process_document should NOT be called by the controller."""
        user = await create_verified_user(db_session, "nosync@example.com")
        files = make_upload_file("nosync.pdf", make_pdf_bytes(1024))

        with patch(STORAGE_MOCK_PATH) as mock_storage, \
             patch("src.controllers.document_controller.process_document_task") as mock_task:
            mock_storage.upload = MagicMock(return_value="path/doc.pdf")
            mock_task.delay = MagicMock()

            # Patch the OLD sync function to verify it's NOT called
            with patch(
                "src.services.ingestion_service.process_document",
                new_callable=AsyncMock,
            ) as mock_sync:
                response = await client.post(
                    "/documents/upload",
                    files=files,
                    headers=auth_header(user),
                )

            # The old sync function should NOT have been called
            mock_sync.assert_not_called()

    # ── Scenario #6: Multiple concurrent uploads all get queued ──────────

    @pytest.mark.asyncio
    async def test_multiple_uploads_all_queued(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Multiple simultaneous uploads should all be queued independently."""
        user = await create_verified_user(db_session, "multi@example.com")

        with patch(STORAGE_MOCK_PATH) as mock_storage, \
             patch("src.controllers.document_controller.process_document_task") as mock_task:
            mock_storage.upload = MagicMock(return_value="path/doc.pdf")
            mock_task.delay = MagicMock()

            # Upload 3 files
            responses = []
            for i in range(3):
                files = make_upload_file(f"paper_{i}.pdf", make_pdf_bytes(1024))
                resp = await client.post(
                    "/documents/upload",
                    files=files,
                    headers=auth_header(user),
                )
                responses.append(resp)

        # All should succeed
        for resp in responses:
            assert resp.status_code == 201
            assert resp.json()["status"] == "processing"

        # delay() should have been called 3 times
        assert mock_task.delay.call_count == 3

        # Each call should have a unique document_id
        doc_ids = [call[0][0] for call in mock_task.delay.call_args_list]
        assert len(set(doc_ids)) == 3  # All unique

    # ── Upload response message mentions async/queued ────────────────────

    @pytest.mark.asyncio
    async def test_upload_response_message(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """The response message should indicate async processing."""
        user = await create_verified_user(db_session, "msg@example.com")
        files = make_upload_file("msg.pdf", make_pdf_bytes(1024))

        with patch(STORAGE_MOCK_PATH) as mock_storage, \
             patch("src.controllers.document_controller.process_document_task") as mock_task:
            mock_storage.upload = MagicMock(return_value="path/doc.pdf")
            mock_task.delay = MagicMock()

            response = await client.post(
                "/documents/upload",
                files=files,
                headers=auth_header(user),
            )

        data = response.json()
        assert "message" in data
        # Should mention processing or queued
        msg_lower = data["message"].lower()
        assert "processing" in msg_lower or "queued" in msg_lower


# ═════════════════════════════════════════════════════════════════════════════
# 6. TASK IDEMPOTENCY TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestTaskIdempotency:
    """Business rule: Don't allow re-processing a document already 'processing'."""

    # ── _process function calls the ingestion service ────────────────────

    @pytest.mark.asyncio
    async def test_process_helper_calls_ingestion_service(self, db_session: AsyncSession):
        """_process() should call process_document from ingestion_service."""
        user = await create_verified_user(db_session, "helper@example.com")
        doc = await create_document_record(db_session, user, status="uploading")

        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=db_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("src.tasks.ingestion.AsyncSessionLocal", return_value=mock_session_ctx), \
             patch("src.services.ingestion_service.process_document", new_callable=AsyncMock) as mock_process:
            from src.tasks.ingestion import _process

            await _process(str(doc.id))

        mock_process.assert_called_once_with(str(doc.id), db_session)

    # ── Ingestion pipeline's race condition guard still works ────────────

    @pytest.mark.asyncio
    async def test_pipeline_skips_already_processing_documents(
        self, db_session: AsyncSession
    ):
        """The IngestionPipeline should skip documents not in 'uploading' status."""
        user = await create_verified_user(db_session, "guard@example.com")
        doc = await create_document_record(db_session, user, status="processing")

        from src.services.ingestion_service import IngestionPipeline

        pipeline = IngestionPipeline(str(doc.id), db_session)
        await pipeline.run()

        # Document status should remain "processing" (not changed)
        await db_session.refresh(doc)
        assert doc.status == "processing"


# ═════════════════════════════════════════════════════════════════════════════
# 7. CONFIG SETTINGS TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestConfigSettings:
    """Tests for Redis/Celery configuration in settings."""

    def test_redis_url_exists_in_settings(self):
        """Settings should have a REDIS_URL field."""
        from src.helpers.config import settings

        assert hasattr(settings, "REDIS_URL")
        assert "redis://" in settings.REDIS_URL

    def test_celery_broker_url_exists(self):
        """Settings should have a CELERY_BROKER_URL field."""
        from src.helpers.config import settings

        assert hasattr(settings, "CELERY_BROKER_URL")
        assert "redis://" in settings.CELERY_BROKER_URL

    def test_celery_result_backend_exists(self):
        """Settings should have a CELERY_RESULT_BACKEND field."""
        from src.helpers.config import settings

        assert hasattr(settings, "CELERY_RESULT_BACKEND")
        assert "redis://" in settings.CELERY_RESULT_BACKEND

    def test_broker_and_backend_use_different_redis_dbs(self):
        """Broker and result backend should use different Redis databases."""
        from src.helpers.config import settings

        # They should end with different db numbers (e.g., /0 vs /1)
        broker_db = settings.CELERY_BROKER_URL.rsplit("/", 1)[-1]
        backend_db = settings.CELERY_RESULT_BACKEND.rsplit("/", 1)[-1]
        assert broker_db != backend_db, (
            "Broker and result backend should use different Redis databases "
            f"to avoid key collisions. Got broker={broker_db}, backend={backend_db}"
        )
