# SPEC-06: Citation & Reference Engine

> **Status:** 🔲 Todo  
> **Dependencies:** SPEC-05 (Chat System)  
> **Priority:** P0 — Key Differentiator  
> **Estimated effort:** 3–4 days

---

## Overview

The Citation Engine is **what makes ScholarGPT unique**. After the LLM generates an answer with source references, this module:

1. Extracts source metadata from the `source_chunks` stored per message
2. Generates properly formatted academic citations in APA, MLA, and BibTeX
3. Provides inline citation text (e.g., `(Smith, 2020)`)
4. Exports BibTeX entries ready for LaTeX or Zotero

```
Assistant Message (with source_chunks) 
    │
    ▼
┌─────────────────────────────┐
│    CITATION ENGINE          │
│                             │
│  Input: document metadata   │
│                             │
│  Output:                    │
│  ├── Inline: (Smith, 2020)  │
│  ├── APA full reference     │
│  ├── MLA full reference     │
│  └── BibTeX @article{...}   │
│                             │
└─────────────────────────────┘
```

---

## No Database Changes

This spec does not modify any database tables. It reads from existing data:
- `messages.source_chunks` — JSON with source metadata (from SPEC-05)
- `documents` — metadata (title, author, year, journal, doi)

---

## Citation Service

**New file:** `src/services/citation_service.py`

This is the core module. It generates all citation formats from document metadata.

```python
"""
Citation & Reference Generator.

Generates formatted academic citations from document metadata.
Supports: APA 7th edition, MLA 9th edition, BibTeX.

Usage:
    metadata = {
        "title": "Deep Learning in Medicine",
        "author": "Smith, John and Doe, Jane",
        "year": "2020",
        "journal": "Journal of AI Research",
        "doi": "10.1234/jair.2020.001",
    }

    apa = CitationGenerator.apa_reference(metadata)
    mla = CitationGenerator.mla_reference(metadata)
    bibtex = CitationGenerator.bibtex_entry(metadata)
    inline = CitationGenerator.apa_inline(metadata)
"""
import re
import unicodedata


class CitationGenerator:
    """Generate academic citations in multiple formats."""

    # ── APA 7th Edition ──────────────────────────────────────

    @staticmethod
    def apa_inline(metadata: dict) -> str:
        """
        Generate APA inline citation.

        Examples:
            (Smith, 2020)
            (Smith & Doe, 2020)
            (Smith et al., 2020)
        """
        author = metadata.get("author", "")
        year = metadata.get("year", "n.d.")

        if not author:
            title = metadata.get("title", "Unknown")
            # Use shortened title for inline
            short_title = title[:30] + "..." if len(title) > 30 else title
            return f'("{short_title}", {year})'

        authors = _parse_authors(author)

        if len(authors) == 1:
            return f"({authors[0]['last']}, {year})"
        elif len(authors) == 2:
            return f"({authors[0]['last']} & {authors[1]['last']}, {year})"
        else:
            return f"({authors[0]['last']} et al., {year})"

    @staticmethod
    def apa_reference(metadata: dict) -> str:
        """
        Generate APA 7th edition full reference.

        Format:
            Author, F. M. (Year). Title of article. Journal Name, Volume(Issue), Pages.
            https://doi.org/xxxxx

        Examples:
            Smith, J. (2020). Deep Learning in Medicine. Journal of AI Research.
            Smith, J., & Doe, J. (2020). Title. Journal Name. https://doi.org/10.xxxx
        """
        author = metadata.get("author", "Unknown Author")
        year = metadata.get("year", "n.d.")
        title = metadata.get("title", "Untitled")
        journal = metadata.get("journal", "")
        doi = metadata.get("doi", "")

        # Format authors for APA
        formatted_author = _format_authors_apa(author)

        # Build citation
        parts = [f"{formatted_author} ({year}). {title}."]

        if journal:
            parts.append(f"*{journal}*.")

        if doi:
            clean_doi = doi.strip()
            if not clean_doi.startswith("http"):
                clean_doi = f"https://doi.org/{clean_doi}"
            parts.append(clean_doi)

        return " ".join(parts)

    # ── MLA 9th Edition ──────────────────────────────────────

    @staticmethod
    def mla_reference(metadata: dict) -> str:
        """
        Generate MLA 9th edition full reference.

        Format:
            Author. "Title of Article." Journal Name, vol. X, no. Y, Year, pp. Pages.

        Examples:
            Smith, John. "Deep Learning in Medicine." Journal of AI Research, 2020.
        """
        author = metadata.get("author", "Unknown Author")
        year = metadata.get("year", "n.d.")
        title = metadata.get("title", "Untitled")
        journal = metadata.get("journal", "")

        # Format author for MLA (Last, First)
        formatted_author = _format_author_mla(author)

        parts = [f'{formatted_author}. "{title}."']

        if journal:
            parts.append(f"*{journal}*,")

        parts.append(f"{year}.")

        return " ".join(parts)

    # ── BibTeX ───────────────────────────────────────────────

    @staticmethod
    def bibtex_entry(metadata: dict) -> str:
        """
        Generate BibTeX entry.

        Example:
            @article{smith2020deep,
              title={Deep Learning in Medicine},
              author={Smith, John},
              journal={Journal of AI Research},
              year={2020},
              doi={10.1234/jair.2020.001}
            }
        """
        author = metadata.get("author", "Unknown")
        year = metadata.get("year", "0000")
        title = metadata.get("title", "Untitled")
        journal = metadata.get("journal", "")
        doi = metadata.get("doi", "")

        # Generate citation key
        key = _generate_bibtex_key(author, year, title)

        # Determine entry type
        entry_type = "article" if journal else "misc"

        lines = [f"@{entry_type}{{{key},"]
        lines.append(f"  title={{{title}}},")
        lines.append(f"  author={{{author}}},")
        if journal:
            lines.append(f"  journal={{{journal}}},")
        lines.append(f"  year={{{year}}},")
        if doi:
            lines.append(f"  doi={{{doi}}},")
        lines.append("}")

        return "\n".join(lines)

    # ── Batch Generation ─────────────────────────────────────

    @staticmethod
    def generate_all_formats(metadata: dict) -> dict:
        """
        Generate all citation formats at once.

        Returns:
            {
                "inline_apa": "(Smith, 2020)",
                "apa": "Smith, J. (2020). Title. *Journal*.",
                "mla": 'Smith, John. "Title." *Journal*, 2020.',
                "bibtex": "@article{smith2020..., ...}",
            }
        """
        return {
            "inline_apa": CitationGenerator.apa_inline(metadata),
            "apa": CitationGenerator.apa_reference(metadata),
            "mla": CitationGenerator.mla_reference(metadata),
            "bibtex": CitationGenerator.bibtex_entry(metadata),
        }


# ── Helper Functions ─────────────────────────────────────────

def _parse_authors(author_string: str) -> list[dict]:
    """
    Parse author string into structured list.

    Input: "Smith, John and Doe, Jane B."
    Output: [{"first": "John", "last": "Smith"}, {"first": "Jane B.", "last": "Doe"}]
    """
    if not author_string:
        return [{"first": "", "last": "Unknown"}]

    # Split by "and", "&", ";"
    parts = re.split(r'\s+and\s+|\s*&\s*|\s*;\s*', author_string)
    authors = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if "," in part:
            # "Last, First" format
            segments = part.split(",", 1)
            authors.append({
                "last": segments[0].strip(),
                "first": segments[1].strip() if len(segments) > 1 else "",
            })
        else:
            # "First Last" format
            words = part.split()
            if len(words) >= 2:
                authors.append({
                    "last": words[-1],
                    "first": " ".join(words[:-1]),
                })
            else:
                authors.append({"last": words[0], "first": ""})

    return authors if authors else [{"first": "", "last": "Unknown"}]


def _format_authors_apa(author_string: str) -> str:
    """
    Format author string for APA.
    "Smith, John and Doe, Jane" → "Smith, J., & Doe, J."
    """
    authors = _parse_authors(author_string)

    formatted = []
    for a in authors:
        last = a["last"]
        first = a["first"]

        if first:
            # Abbreviate first name(s): "John Adam" → "J. A."
            initials = ". ".join(n[0] for n in first.split() if n) + "."
            formatted.append(f"{last}, {initials}")
        else:
            formatted.append(last)

    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    else:
        return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"


def _format_author_mla(author_string: str) -> str:
    """
    Format author string for MLA.
    "Smith, John and Doe, Jane" → "Smith, John, and Jane Doe"
    """
    authors = _parse_authors(author_string)

    if len(authors) == 1:
        a = authors[0]
        return f"{a['last']}, {a['first']}" if a['first'] else a['last']
    elif len(authors) == 2:
        a1, a2 = authors
        first_author = f"{a1['last']}, {a1['first']}" if a1['first'] else a1['last']
        second_author = f"{a2['first']} {a2['last']}" if a2['first'] else a2['last']
        return f"{first_author}, and {second_author}"
    else:
        a1 = authors[0]
        first_author = f"{a1['last']}, {a1['first']}" if a1['first'] else a1['last']
        return f"{first_author}, et al."


def _generate_bibtex_key(author: str, year: str, title: str) -> str:
    """
    Generate BibTeX citation key.
    "Smith, John", "2020", "Deep Learning in Medicine" → "smith2020deep"
    """
    # Get last name
    authors = _parse_authors(author)
    last = authors[0]["last"].lower() if authors else "unknown"

    # Remove special characters
    last = re.sub(r'[^a-z]', '', last)

    # Get first significant word from title
    title_words = re.findall(r'[a-zA-Z]+', title)
    # Skip common words
    skip_words = {"the", "a", "an", "of", "in", "on", "for", "and", "to", "with"}
    first_word = ""
    for word in title_words:
        if word.lower() not in skip_words:
            first_word = word.lower()
            break

    year_str = year if year and year != "n.d." else "0000"

    return f"{last}{year_str}{first_word}"
```

---

## API Endpoints

### `GET /messages/{message_id}/citations`

Get formatted citations for all sources used in a specific message.

**Query Parameters:**
- `format` (optional, default `"all"`): `"apa"`, `"mla"`, `"bibtex"`, or `"all"`

**Success Response (200):**
```json
{
  "message_id": "msg-uuid-...",
  "citations": [
    {
      "source_number": 1,
      "document_id": "doc-uuid-1",
      "title": "Deep Learning in Medicine",
      "author": "Smith, John",
      "year": "2020",
      "page_number": 15,
      "formats": {
        "inline_apa": "(Smith, 2020)",
        "apa": "Smith, J. (2020). Deep Learning in Medicine. *Journal of AI Research*.",
        "mla": "Smith, John. \"Deep Learning in Medicine.\" *Journal of AI Research*, 2020.",
        "bibtex": "@article{smith2020deep,\n  title={Deep Learning in Medicine},\n  author={Smith, John},\n  journal={Journal of AI Research},\n  year={2020}\n}"
      }
    },
    {
      "source_number": 2,
      "document_id": "doc-uuid-2",
      "title": "CNN Challenges in Healthcare",
      "author": "Doe, Jane",
      "year": "2021",
      "page_number": 8,
      "formats": {
        "inline_apa": "(Doe, 2021)",
        "apa": "Doe, J. (2021). CNN Challenges in Healthcare.",
        "mla": "Doe, Jane. \"CNN Challenges in Healthcare.\" 2021.",
        "bibtex": "@misc{doe2021cnn,\n  title={CNN Challenges in Healthcare},\n  author={Doe, Jane},\n  year={2021}\n}"
      }
    }
  ]
}
```

---

### `GET /citations/export`

Export all citations from a message in a single format (for copy-paste).

**Query Parameters:**
- `message_id` (required): UUID of the message
- `format` (required): `"apa"`, `"mla"`, or `"bibtex"`

**Success Response (200) — format=bibtex:**
```
@article{smith2020deep,
  title={Deep Learning in Medicine},
  author={Smith, John},
  journal={Journal of AI Research},
  year={2020}
}

@misc{doe2021cnn,
  title={CNN Challenges in Healthcare},
  author={Doe, Jane},
  year={2021}
}
```

**Response Content-Type:** `text/plain` (for easy copy-paste)

---

## Citation Routes

**New file:** `src/routes/citation_routes.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.helpers.db import get_db
from src.helpers.security import get_current_user
from src.controllers.citation_controller import CitationController

router = APIRouter(prefix="/citations", tags=["Citations"])


@router.get("/messages/{message_id}")
async def get_message_citations(
    message_id: str,
    format: str = Query("all", regex="^(apa|mla|bibtex|all)$"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get formatted citations for a specific message's sources."""
    return await CitationController.get_citations(
        message_id, format, current_user, db
    )


@router.get("/export", response_class=PlainTextResponse)
async def export_citations(
    message_id: str = Query(...),
    format: str = Query(..., regex="^(apa|mla|bibtex)$"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Export citations in a single format as plain text."""
    return await CitationController.export(
        message_id, format, current_user, db
    )
```

---

## File Structure

### New Files to Create

| File | Purpose |
|---|---|
| `src/services/citation_service.py` | Citation generation logic (APA, MLA, BibTeX) |
| `src/routes/citation_routes.py` | Citation API endpoints |
| `src/controllers/citation_controller.py` | Citation business logic |

### Files to Modify

| File | Change |
|---|---|
| `src/main.py` | Register citation routes |

---

## Business Rules

1. **Metadata quality:** Citations are only as good as the metadata. If `author` or `title` is missing, the citation will show "Unknown Author" or "Untitled". Users can fix metadata via SPEC-02's PATCH endpoint.
2. **Deduplication:** If two chunks come from the same document, only one citation is generated for that document.
3. **BibTeX keys:** Must be unique within an export. If two papers would generate the same key, append a/b/c suffix.
4. **APA author formatting:** Single author → `Smith, J.`, Two authors → `Smith, J., & Doe, J.`, Three+ → `Smith, J., Doe, J., & Johnson, R.`
5. **Inline APA:** Single author → `(Smith, 2020)`, Two → `(Smith & Doe, 2020)`, Three+ → `(Smith et al., 2020)`

---

## Test Scenarios

| # | Scenario | Expected Result |
|---|---|---|
| 1 | APA: Single author | `Smith, J. (2020). Title. *Journal*.` |
| 2 | APA: Two authors | `Smith, J., & Doe, J. (2020). Title.` |
| 3 | APA: Three authors | `Smith, J., Doe, J., & Johnson, R. (2020). Title.` |
| 4 | APA: With DOI | Includes `https://doi.org/...` |
| 5 | APA: No year | Shows `(n.d.)` |
| 6 | APA inline: Single | `(Smith, 2020)` |
| 7 | APA inline: Two | `(Smith & Doe, 2020)` |
| 8 | APA inline: Three+ | `(Smith et al., 2020)` |
| 9 | MLA: Single author | `Smith, John. "Title." *Journal*, 2020.` |
| 10 | BibTeX: With journal | `@article{...}` |
| 11 | BibTeX: Without journal | `@misc{...}` |
| 12 | BibTeX: Key generation | `smith2020deep` from "Smith", "2020", "Deep Learning..." |
| 13 | Export: Multiple sources | All citations in one text block |
| 14 | Missing metadata | Graceful fallback to "Unknown Author", "Untitled" |
| 15 | Duplicate document | Only one citation per unique document |

---

## Acceptance Criteria

- [ ] APA inline citations are correctly formatted for 1, 2, and 3+ authors
- [ ] APA full references are correctly formatted with author, year, title, journal, DOI
- [ ] MLA references are correctly formatted
- [ ] BibTeX entries are valid and parseable
- [ ] BibTeX citation keys are generated deterministically
- [ ] `GET /messages/{id}/citations` returns formatted citations for all sources
- [ ] `GET /citations/export` returns plain text for copy-paste
- [ ] Missing metadata is handled gracefully (no crashes, shows fallback text)
- [ ] Duplicate documents produce only one citation
- [ ] All endpoints require authentication
- [ ] Users cannot access other users' message citations
