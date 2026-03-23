"""
Background task: Process a document through the ingestion pipeline (SPEC-08).

This wraps the async ingestion_service in a Celery task so it runs
in a background worker process instead of blocking the API.

Key design decisions:
  - _run_async() creates a NEW event loop each call (Celery workers are sync)
  - _make_session() creates a FRESH engine each call (asyncpg pools can't
    cross event loops — the global engine from db.py is bound to import-time loop)
  - Lazy import of process_document to avoid circular imports
  - _mark_failed uses raw SQL update (not ORM pipeline) for reliability
  - Task retries up to 3 times with 30-second delays
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.tasks import celery_app
from src.helpers.config import settings
from src.helpers.logging_config import get_logger

# ── EAGER ORM IMPORTS FOR CELERY WORKER ──────────────────────────────────────
# Fixes "One or more mappers failed to initialize... expression 'User' failed"
# Because Celery runs independently of FastAPI, we must ensure all models are
# loaded into the SQLAlchemy registry before doing DB operations.
import src.models.db_scheams.user  # noqa
import src.models.db_scheams.document  # noqa
import src.models.db_scheams.DocumentChunk  # noqa

logger = get_logger("celery.ingestion")


def _make_session() -> async_sessionmaker[AsyncSession]:
    """Create a fresh engine + session factory for this event loop.

    We can NOT reuse the global engine from db.py because asyncpg's
    connection pool is bound to the event loop that created it. Since
    _run_async() creates a new loop for each task, we need a new engine too.
    """
    engine = create_async_engine(settings.get_database_url(), echo=False)
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def _run_async(coro):
    """Run async code inside a sync Celery task.

    Creates a new event loop each time because Celery workers
    are synchronous — there's no existing loop to reuse.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="tasks.process_document",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_document_task(self, document_id: str):
    """Celery task to process a document through the ingestion pipeline.

    Args:
        document_id: UUID string of the document to process.

    Retries:
        Up to 3 times with 30-second delays on failure.
        On each failure, the document is marked as "failed" in the DB
        before the retry is scheduled.
    """
    logger.info(f"[Task {self.request.id}] Starting document processing: {document_id}")

    try:
        _run_async(_process(document_id))
        logger.info(f"[Task {self.request.id}] Document {document_id} processed successfully")

    except Exception as exc:
        logger.error(f"[Task {self.request.id}] Failed: {str(exc)}")
        # Mark as failed in DB before retrying
        _run_async(_mark_failed(document_id, str(exc)))
        raise self.retry(exc=exc)


async def _process(document_id: str):
    """Run the ingestion pipeline with a fresh DB session.

    Uses a lazy import of process_document to avoid circular imports
    when the Celery app initializes.
    """
    from src.services.ingestion_service import process_document

    SessionLocal = _make_session()
    async with SessionLocal() as db:
        await process_document(document_id, db)


async def _mark_failed(document_id: str, error: str):
    """Mark a document as failed in the database.

    Uses a raw SQL update (not the ORM pipeline) so this works
    even if the ORM session that was processing the document
    is in a broken state.
    """
    from sqlalchemy import update
    from src.models.db_scheams.document import Document

    SessionLocal = _make_session()
    async with SessionLocal() as db:
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(status="failed", error_message=error)
        )
        await db.commit()

