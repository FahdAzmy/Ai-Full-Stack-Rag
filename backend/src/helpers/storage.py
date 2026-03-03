"""
Supabase Storage helper for document file operations (SPEC-02).

Wraps the Supabase Python client's storage API.
All operations use the Service Role Key — the frontend never accesses storage directly.
"""

import traceback

from supabase import create_client

from src.helpers.config import settings
from src.helpers.logging_config import get_logger

logger = get_logger("helpers.storage")

# Lazy-init the Supabase client (import is at top, but client is created on first use)
_client = None


def _get_client():
    """Get or create the Supabase client (lazy singleton)."""
    global _client
    if _client is None:
        logger.info("Initializing Supabase client for URL=%s", settings.SUPABASE_URL)
        try:
            _client = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(
                "Failed to initialize Supabase client: %s\n%s",
                str(e),
                traceback.format_exc(),
            )
            raise
    return _client


def upload(file_content: bytes, storage_path: str) -> str:
    """Upload a file to Supabase Storage.

    Args:
        file_content: The raw file bytes.
        storage_path: Object path inside the bucket, e.g. '{user_id}/{doc_id}.pdf'

    Returns:
        The storage path on success.

    Raises:
        Exception: If the upload fails.
    """
    client = _get_client()
    bucket = settings.STORAGE_BUCKET

    logger.info(
        "Uploading to bucket=%s path=%s (%d bytes)",
        bucket,
        storage_path,
        len(file_content),
    )

    client.storage.from_(bucket).upload(
        path=storage_path,
        file=file_content,
        file_options={"content-type": "application/pdf"},
    )

    logger.info("Upload successful: %s", storage_path)
    return storage_path


def download(storage_path: str) -> bytes:
    """Download a file from Supabase Storage."""
    client = _get_client()
    bucket = settings.STORAGE_BUCKET

    logger.info("Downloading from bucket=%s path=%s", bucket, storage_path)
    return client.storage.from_(bucket).download(storage_path)


def delete(storage_path: str) -> None:
    """Delete a file from Supabase Storage."""
    client = _get_client()
    bucket = settings.STORAGE_BUCKET

    logger.info("Deleting from bucket=%s path=%s", bucket, storage_path)
    client.storage.from_(bucket).remove([storage_path])
    logger.info("Delete successful: %s", storage_path)


def create_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """Generate a signed URL for temporary access to a file."""
    client = _get_client()
    bucket = settings.STORAGE_BUCKET

    logger.info(
        "Creating signed URL for path=%s expires_in=%ds", storage_path, expires_in
    )
    result = client.storage.from_(bucket).create_signed_url(
        path=storage_path,
        expires_in=expires_in,
    )
    return result["signedURL"]
