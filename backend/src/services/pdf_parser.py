"""
PDF Parser — Extract text and metadata from PDF files using PyMuPDF.
"""

import re
import fitz  # PyMuPDF


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text page-by-page from a PDF.

    Returns:
        [{"page": 1, "text": "..."}, {"page": 2, "text": "..."}, ...]

    Raises:
        ValueError: If the file cannot be opened or has no extractable text.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Cannot open PDF: {str(e)}")

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

    doc.close()

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
    """
    doc = fitz.open(file_path)
    meta = doc.metadata or {}
    total_pages = doc.page_count
    doc.close()

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
