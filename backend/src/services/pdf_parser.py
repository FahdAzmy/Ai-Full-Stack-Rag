"""
PDF Parser — Extract text and metadata from PDF files using PyMuPDF.
"""

import os
import re
import fitz  # PyMuPDF

from src.helpers.config import settings


def _validate_file_size(file_path: str) -> None:
    """Raise ValueError if the file exceeds the maximum allowed size."""
    try:
        size_bytes = os.path.getsize(file_path)
    except OSError as e:
        raise ValueError(f"Cannot access PDF file: {str(e)}")

    size_mb = size_bytes / (1024 * 1024)
    if size_mb > settings.MAX_PDF_SIZE_MB:
        raise ValueError(
            f"PDF too large. Maximum allowed size is {settings.MAX_PDF_SIZE_MB} MB."
        )


def _open_pdf(file_path: str) -> fitz.Document:
    """Open a PDF file with size and page-count validation.

    Returns an opened fitz.Document (caller must use as context manager or close).

    Raises:
        ValueError: If the file cannot be accessed, opened, or exceeds limits.
    """
    _validate_file_size(file_path)

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Cannot open PDF: {str(e)}")

    if doc.page_count > settings.MAX_PDF_PAGES:
        doc.close()
        raise ValueError(
            f"PDF too large. Maximum allowed pages is {settings.MAX_PDF_PAGES}."
        )

    return doc


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text page-by-page from a PDF.

    Returns:
        [{"page": 1, "text": "..."}, {"page": 2, "text": "..."}, ...]

    Raises:
        ValueError: If the file cannot be opened, exceeds limits,
                    or has no extractable text.
    """
    with _open_pdf(file_path) as doc:
        pages = []
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text("text")
            cleaned = _clean_text(text)
            if cleaned:
                pages.append(
                    {
                        "page": page_num + 1,
                        "text": cleaned,
                    }
                )

    if not pages:
        raise ValueError(
            "PDF contains no extractable text. It may be a scanned document."
        )

    return pages


def extract_metadata(file_path: str) -> dict:
    """
    Extract metadata from PDF file properties.

    Returns:
        {
            "title": str | None,
            "author": str | None,
            "year": str | None,
            "total_pages": int,
        }

    Raises:
        ValueError: If the file cannot be opened or exceeds limits.
    """
    with _open_pdf(file_path) as doc:
        meta = doc.metadata or {}
        total_pages = doc.page_count

    return {
        "title": meta.get("title", "").strip() or None,
        "author": meta.get("author", "").strip() or None,
        "year": _extract_year(meta.get("creationDate", "")),
        "total_pages": total_pages,
    }


def _clean_text(text: str) -> str:
    """Clean extracted text: normalize whitespace, remove control chars."""
    if not text:
        return ""
    # Replace multiple newlines with double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Replace multiple spaces with single space
    text = re.sub(r" {2,}", " ", text)
    # Remove control characters except newline and tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text.strip()


def _extract_year(date_str: str) -> str | None:
    """Extract 4-digit year from PDF date string like 'D:20200315120000'."""
    if not date_str:
        return None
    match = re.search(r"(\d{4})", date_str)
    return match.group(1) if match else None
