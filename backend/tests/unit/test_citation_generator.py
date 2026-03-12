"""
Unit tests for Citation Engine — CitationGenerator & helper functions (SPEC-06).
Following TDD: These tests are written BEFORE implementation.

Tests are organized by functionality:
  1. TestApaInline         — APA inline citation formatting
  2. TestApaReference      — APA 7th edition full reference
  3. TestMlaReference      — MLA 9th edition full reference
  4. TestBibtexEntry       — BibTeX entry generation
  5. TestGenerateAllFormats — Batch generation of all formats
  6. TestParseAuthors      — Author string parsing
  7. TestFormatAuthorsApa  — APA author formatting
  8. TestFormatAuthorMla   — MLA author formatting
  9. TestGenerateBibtexKey — BibTeX key generation

All tests are pure unit tests with no database or API dependencies.
"""

import pytest


# ═════════════════════════════════════════════════════════════════════════════
# 1. APA INLINE CITATION TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestApaInline:
    """Tests for CitationGenerator.apa_inline()."""

    # ── Scenario #6: Single author → (Smith, 2020) ───────────────────────

    @pytest.mark.asyncio
    async def test_apa_inline_single_author(self):
        """Single author → (LastName, Year)."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Deep Learning in Medicine",
        }
        result = CitationGenerator.apa_inline(metadata)
        assert result == "(Smith, 2020)"

    # ── Scenario #7: Two authors → (Smith & Doe, 2020) ───────────────────

    @pytest.mark.asyncio
    async def test_apa_inline_two_authors(self):
        """Two authors → (Last1 & Last2, Year)."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John and Doe, Jane",
            "year": "2020",
            "title": "Collaborative Study",
        }
        result = CitationGenerator.apa_inline(metadata)
        assert result == "(Smith & Doe, 2020)"

    # ── Scenario #8: Three+ authors → (Smith et al., 2020) ──────────────

    @pytest.mark.asyncio
    async def test_apa_inline_three_authors(self):
        """Three or more authors → (FirstLast et al., Year)."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John and Doe, Jane and Johnson, Robert",
            "year": "2020",
            "title": "Multi-Author Study",
        }
        result = CitationGenerator.apa_inline(metadata)
        assert result == "(Smith et al., 2020)"

    # ── No author → uses shortened title ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_apa_inline_no_author_uses_title(self):
        """Missing author → use shortened title as fallback."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "",
            "year": "2021",
            "title": "A Very Important Paper",
        }
        result = CitationGenerator.apa_inline(metadata)
        assert "2021" in result
        # Should contain title text since there's no author
        assert "A Very Important Paper" in result

    # ── No author, long title → title is truncated ───────────────────────

    @pytest.mark.asyncio
    async def test_apa_inline_no_author_long_title_truncated(self):
        """Missing author with long title → title truncated to 30 chars + '...'."""
        from src.services.citation_service import CitationGenerator

        long_title = "A" * 50  # 50 chars, should be truncated
        metadata = {
            "author": "",
            "year": "2021",
            "title": long_title,
        }
        result = CitationGenerator.apa_inline(metadata)
        # Shortened title should be 30 chars + "..."
        assert "..." in result
        assert "2021" in result

    # ── No year → uses "n.d." ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_apa_inline_no_year(self):
        """Missing year → shows (Author, n.d.)."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "title": "Timeless Study",
        }
        result = CitationGenerator.apa_inline(metadata)
        assert result == "(Smith, n.d.)"

    # ── Authors separated by "&" ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_apa_inline_authors_with_ampersand(self):
        """Authors separated by '&' → correctly parsed."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John & Doe, Jane",
            "year": "2020",
            "title": "Ampersand Test",
        }
        result = CitationGenerator.apa_inline(metadata)
        assert result == "(Smith & Doe, 2020)"

    # ── Authors separated by ";" ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_apa_inline_authors_with_semicolon(self):
        """Authors separated by ';' → correctly parsed."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John; Doe, Jane; Johnson, Robert",
            "year": "2020",
            "title": "Semicolon Test",
        }
        result = CitationGenerator.apa_inline(metadata)
        assert result == "(Smith et al., 2020)"

    # ── "First Last" format (no comma) ───────────────────────────────────

    @pytest.mark.asyncio
    async def test_apa_inline_first_last_format(self):
        """Author in 'First Last' format → correctly parsed."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "John Smith",
            "year": "2020",
            "title": "First-Last Format",
        }
        result = CitationGenerator.apa_inline(metadata)
        assert result == "(Smith, 2020)"


# ═════════════════════════════════════════════════════════════════════════════
# 2. APA FULL REFERENCE TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestApaReference:
    """Tests for CitationGenerator.apa_reference()."""

    # ── Scenario #1: Single author → Smith, J. (2020). Title. *Journal*. ─

    @pytest.mark.asyncio
    async def test_apa_reference_single_author(self):
        """Single author with journal → formatted APA reference."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Deep Learning in Medicine",
            "journal": "Journal of AI Research",
        }
        result = CitationGenerator.apa_reference(metadata)
        assert "Smith, J." in result
        assert "(2020)" in result
        assert "Deep Learning in Medicine" in result
        assert "*Journal of AI Research*" in result

    # ── Scenario #2: Two authors → Smith, J., & Doe, J. ─────────────────

    @pytest.mark.asyncio
    async def test_apa_reference_two_authors(self):
        """Two authors → 'Author1, & Author2 (Year). Title.'"""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John and Doe, Jane",
            "year": "2020",
            "title": "Collaborative Work",
            "journal": "Science Review",
        }
        result = CitationGenerator.apa_reference(metadata)
        assert "Smith, J." in result
        assert "& Doe, J." in result
        assert "(2020)" in result

    # ── Scenario #3: Three authors → all listed ──────────────────────────

    @pytest.mark.asyncio
    async def test_apa_reference_three_authors(self):
        """Three authors → all listed with '&' before last."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John and Doe, Jane and Johnson, Robert",
            "year": "2020",
            "title": "Multi-Author Work",
            "journal": "AI Journal",
        }
        result = CitationGenerator.apa_reference(metadata)
        assert "Smith, J." in result
        assert "Doe, J." in result
        assert "& Johnson, R." in result
        assert "(2020)" in result

    # ── Scenario #4: With DOI → includes https://doi.org/... ─────────────

    @pytest.mark.asyncio
    async def test_apa_reference_with_doi(self):
        """DOI provided → appended as URL."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "DOI Paper",
            "journal": "AI Journal",
            "doi": "10.1234/jair.2020.001",
        }
        result = CitationGenerator.apa_reference(metadata)
        assert "https://doi.org/10.1234/jair.2020.001" in result

    # ── DOI already has https:// prefix → not duplicated ─────────────────

    @pytest.mark.asyncio
    async def test_apa_reference_doi_with_url_prefix(self):
        """DOI that already starts with 'https://' → not duplicated."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "URL DOI Paper",
            "doi": "https://doi.org/10.1234/jair.2020.001",
        }
        result = CitationGenerator.apa_reference(metadata)
        # Should contain exactly one "https://doi.org/"
        assert result.count("https://doi.org/") == 1

    # ── Scenario #5: No year → (n.d.) ───────────────────────────────────

    @pytest.mark.asyncio
    async def test_apa_reference_no_year(self):
        """Missing year → shows (n.d.)."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "title": "Undated Paper",
            "journal": "AI Journal",
        }
        result = CitationGenerator.apa_reference(metadata)
        assert "(n.d.)" in result

    # ── No journal → no italicized journal part ──────────────────────────

    @pytest.mark.asyncio
    async def test_apa_reference_no_journal(self):
        """Missing journal → reference without journal part."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "No Journal Paper",
        }
        result = CitationGenerator.apa_reference(metadata)
        assert "Smith, J." in result
        assert "(2020)" in result
        assert "No Journal Paper" in result
        # Should NOT contain asterisks for journal
        assert "*" not in result

    # ── No author → "Unknown Author" ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_apa_reference_no_author(self):
        """Missing author → 'Unknown Author'."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "year": "2020",
            "title": "Anonymous Paper",
        }
        result = CitationGenerator.apa_reference(metadata)
        assert "Unknown" in result
        assert "(2020)" in result

    # ── No title → "Untitled" ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_apa_reference_no_title(self):
        """Missing title → 'Untitled'."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
        }
        result = CitationGenerator.apa_reference(metadata)
        assert "Untitled" in result

    # ── Author with middle name → initials abbreviated ───────────────────

    @pytest.mark.asyncio
    async def test_apa_reference_author_middle_name(self):
        """Author with middle name(s) → each initial abbreviated."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John Adam",
            "year": "2020",
            "title": "Middle Name Paper",
        }
        result = CitationGenerator.apa_reference(metadata)
        # "John Adam" → "J. A."
        assert "Smith, J. A." in result


# ═════════════════════════════════════════════════════════════════════════════
# 3. MLA REFERENCE TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestMlaReference:
    """Tests for CitationGenerator.mla_reference()."""

    # ── Scenario #9: Single author → Smith, John. "Title." *Journal*, 2020. ─

    @pytest.mark.asyncio
    async def test_mla_reference_single_author(self):
        """Single author with journal → MLA formatted reference."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Deep Learning in Medicine",
            "journal": "Journal of AI Research",
        }
        result = CitationGenerator.mla_reference(metadata)
        assert "Smith, John" in result
        assert '"Deep Learning in Medicine."' in result
        assert "*Journal of AI Research*" in result
        assert "2020" in result

    # ── Two authors → Smith, John, and Jane Doe ──────────────────────────

    @pytest.mark.asyncio
    async def test_mla_reference_two_authors(self):
        """Two authors → 'Last, First, and First2 Last2'."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John and Doe, Jane",
            "year": "2020",
            "title": "Collaborative Work",
            "journal": "Science Review",
        }
        result = CitationGenerator.mla_reference(metadata)
        assert "Smith, John" in result
        assert "and Jane Doe" in result
        assert "2020" in result

    # ── Three+ authors → Last, First, et al. ─────────────────────────────

    @pytest.mark.asyncio
    async def test_mla_reference_three_authors(self):
        """Three+ authors → 'Last, First, et al.'"""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John and Doe, Jane and Johnson, Robert",
            "year": "2020",
            "title": "Multi-Author Study",
            "journal": "AI Journal",
        }
        result = CitationGenerator.mla_reference(metadata)
        assert "Smith, John" in result
        assert "et al." in result
        # Should NOT include Doe or Johnson
        assert "Doe" not in result
        assert "Johnson" not in result

    # ── No journal → reference without journal ───────────────────────────

    @pytest.mark.asyncio
    async def test_mla_reference_no_journal(self):
        """Missing journal → reference without italicized journal."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "No Journal Paper",
        }
        result = CitationGenerator.mla_reference(metadata)
        assert "Smith, John" in result
        assert '"No Journal Paper."' in result
        assert "2020." in result
        assert "*" not in result

    # ── No year → "n.d." ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_mla_reference_no_year(self):
        """Missing year → shows 'n.d.'."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "title": "Undated Work",
        }
        result = CitationGenerator.mla_reference(metadata)
        assert "n.d." in result

    # ── No author → "Unknown Author" ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_mla_reference_no_author(self):
        """Missing author → 'Unknown Author'."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "year": "2021",
            "title": "Anonymous Study",
        }
        result = CitationGenerator.mla_reference(metadata)
        assert "Unknown" in result


# ═════════════════════════════════════════════════════════════════════════════
# 4. BIBTEX ENTRY TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestBibtexEntry:
    """Tests for CitationGenerator.bibtex_entry()."""

    # ── Scenario #10: With journal → @article{...} ──────────────────────

    @pytest.mark.asyncio
    async def test_bibtex_with_journal_is_article(self):
        """Paper with journal → @article{} type."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Deep Learning in Medicine",
            "journal": "Journal of AI Research",
            "doi": "10.1234/jair.2020.001",
        }
        result = CitationGenerator.bibtex_entry(metadata)
        assert result.startswith("@article{")
        assert "title={Deep Learning in Medicine}" in result
        assert "author={Smith, John}" in result
        assert "journal={Journal of AI Research}" in result
        assert "year={2020}" in result
        assert "doi={10.1234/jair.2020.001}" in result
        assert result.strip().endswith("}")

    # ── Scenario #11: Without journal → @misc{...} ──────────────────────

    @pytest.mark.asyncio
    async def test_bibtex_without_journal_is_misc(self):
        """Paper without journal → @misc{} type."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Misc Paper",
        }
        result = CitationGenerator.bibtex_entry(metadata)
        assert result.startswith("@misc{")
        assert "journal" not in result
        assert "title={Misc Paper}" in result

    # ── Scenario #12: Key generation → smith2020deep ─────────────────────

    @pytest.mark.asyncio
    async def test_bibtex_key_generation(self):
        """Key = 'lastnameyearfirstword' → smith2020deep."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Deep Learning in Medicine",
            "journal": "Journal of AI Research",
        }
        result = CitationGenerator.bibtex_entry(metadata)
        assert "@article{smith2020deep," in result

    # ── No DOI → no doi field ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_bibtex_without_doi(self):
        """No DOI → bibtex entry has no doi field."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "No DOI Paper",
            "journal": "AI Journal",
        }
        result = CitationGenerator.bibtex_entry(metadata)
        assert "doi=" not in result

    # ── Valid multiline BibTeX structure ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_bibtex_structure_is_valid(self):
        """BibTeX entry should have proper multiline structure."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Valid Structure",
            "journal": "Test Journal",
        }
        result = CitationGenerator.bibtex_entry(metadata)
        lines = result.split("\n")
        # First line should start with @
        assert lines[0].startswith("@")
        # Last line should be just "}"
        assert lines[-1].strip() == "}"
        # Inner lines should have key={value},
        for line in lines[1:-1]:
            line_stripped = line.strip()
            assert "=" in line_stripped or line_stripped == ""

    # ── No author → "Unknown" ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_bibtex_no_author(self):
        """Missing author → uses 'Unknown'."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "year": "2020",
            "title": "Anonymous Paper",
        }
        result = CitationGenerator.bibtex_entry(metadata)
        assert "author={Unknown}" in result

    # ── No year → uses "0000" ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_bibtex_no_year(self):
        """Missing year → uses '0000'."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "title": "Undated Paper",
        }
        result = CitationGenerator.bibtex_entry(metadata)
        assert "year={0000}" in result


# ═════════════════════════════════════════════════════════════════════════════
# 5. GENERATE ALL FORMATS TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestGenerateAllFormats:
    """Tests for CitationGenerator.generate_all_formats()."""

    @pytest.mark.asyncio
    async def test_generate_all_formats_returns_all_keys(self):
        """generate_all_formats() returns dict with all 4 format keys."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Test Paper",
            "journal": "Test Journal",
        }
        result = CitationGenerator.generate_all_formats(metadata)

        assert isinstance(result, dict)
        assert "inline_apa" in result
        assert "apa" in result
        assert "mla" in result
        assert "bibtex" in result

    @pytest.mark.asyncio
    async def test_generate_all_formats_values_are_strings(self):
        """All values in the result dict should be non-empty strings."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Test Paper",
            "journal": "Test Journal",
        }
        result = CitationGenerator.generate_all_formats(metadata)

        for key, value in result.items():
            assert isinstance(value, str), f"{key} should be a string"
            assert len(value) > 0, f"{key} should not be empty"

    @pytest.mark.asyncio
    async def test_generate_all_formats_consistency(self):
        """Individual methods should produce same output as batch method."""
        from src.services.citation_service import CitationGenerator

        metadata = {
            "author": "Smith, John",
            "year": "2020",
            "title": "Deep Learning in Medicine",
            "journal": "Journal of AI Research",
            "doi": "10.1234/jair.2020.001",
        }
        batch = CitationGenerator.generate_all_formats(metadata)

        # Each value should match the individual method call
        assert batch["inline_apa"] == CitationGenerator.apa_inline(metadata)
        assert batch["apa"] == CitationGenerator.apa_reference(metadata)
        assert batch["mla"] == CitationGenerator.mla_reference(metadata)
        assert batch["bibtex"] == CitationGenerator.bibtex_entry(metadata)


# ═════════════════════════════════════════════════════════════════════════════
# 6. PARSE AUTHORS HELPER TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestParseAuthors:
    """Tests for _parse_authors() helper function."""

    @pytest.mark.asyncio
    async def test_parse_single_author_last_first(self):
        """'Last, First' → [{last: 'Last', first: 'First'}]."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("Smith, John")
        assert len(result) == 1
        assert result[0]["last"] == "Smith"
        assert result[0]["first"] == "John"

    @pytest.mark.asyncio
    async def test_parse_single_author_first_last(self):
        """'First Last' → [{last: 'Last', first: 'First'}]."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("John Smith")
        assert len(result) == 1
        assert result[0]["last"] == "Smith"
        assert result[0]["first"] == "John"

    @pytest.mark.asyncio
    async def test_parse_two_authors_with_and(self):
        """'Author1 and Author2' → 2 author dicts."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("Smith, John and Doe, Jane")
        assert len(result) == 2
        assert result[0]["last"] == "Smith"
        assert result[1]["last"] == "Doe"

    @pytest.mark.asyncio
    async def test_parse_authors_with_ampersand(self):
        """'Author1 & Author2' → 2 author dicts."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("Smith, John & Doe, Jane")
        assert len(result) == 2
        assert result[0]["last"] == "Smith"
        assert result[1]["last"] == "Doe"

    @pytest.mark.asyncio
    async def test_parse_authors_with_semicolon(self):
        """'Author1; Author2' → 2 author dicts."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("Smith, John; Doe, Jane")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_parse_three_authors(self):
        """Three authors → 3 author dicts."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("Smith, John and Doe, Jane and Johnson, Robert")
        assert len(result) == 3
        assert result[0]["last"] == "Smith"
        assert result[1]["last"] == "Doe"
        assert result[2]["last"] == "Johnson"

    @pytest.mark.asyncio
    async def test_parse_empty_string(self):
        """Empty author string → [{first: '', last: 'Unknown'}]."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("")
        assert len(result) == 1
        assert result[0]["last"] == "Unknown"

    @pytest.mark.asyncio
    async def test_parse_none_returns_unknown(self):
        """None author string → [{first: '', last: 'Unknown'}]."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors(None)
        assert len(result) == 1
        assert result[0]["last"] == "Unknown"

    @pytest.mark.asyncio
    async def test_parse_single_name_only(self):
        """Single word name → last name only, no first."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("Aristotle")
        assert len(result) == 1
        assert result[0]["last"] == "Aristotle"
        assert result[0]["first"] == ""

    @pytest.mark.asyncio
    async def test_parse_author_with_middle_name(self):
        """'Last, First Middle' → first includes middle."""
        from src.services.citation_service import _parse_authors

        result = _parse_authors("Smith, John Adam")
        assert len(result) == 1
        assert result[0]["last"] == "Smith"
        assert result[0]["first"] == "John Adam"


# ═════════════════════════════════════════════════════════════════════════════
# 7. FORMAT AUTHORS APA HELPER TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestFormatAuthorsApa:
    """Tests for _format_authors_apa() helper function."""

    @pytest.mark.asyncio
    async def test_format_single_author_apa(self):
        """Single author → 'Smith, J.'."""
        from src.services.citation_service import _format_authors_apa

        result = _format_authors_apa("Smith, John")
        assert result == "Smith, J."

    @pytest.mark.asyncio
    async def test_format_two_authors_apa(self):
        """Two authors → 'Smith, J., & Doe, J.'."""
        from src.services.citation_service import _format_authors_apa

        result = _format_authors_apa("Smith, John and Doe, Jane")
        assert result == "Smith, J., & Doe, J."

    @pytest.mark.asyncio
    async def test_format_three_authors_apa(self):
        """Three authors → 'Smith, J., Doe, J., & Johnson, R.'."""
        from src.services.citation_service import _format_authors_apa

        result = _format_authors_apa("Smith, John and Doe, Jane and Johnson, Robert")
        assert result == "Smith, J., Doe, J., & Johnson, R."

    @pytest.mark.asyncio
    async def test_format_author_with_middle_name_apa(self):
        """Author with middle name → 'Smith, J. A.'."""
        from src.services.citation_service import _format_authors_apa

        result = _format_authors_apa("Smith, John Adam")
        assert result == "Smith, J. A."


# ═════════════════════════════════════════════════════════════════════════════
# 8. FORMAT AUTHOR MLA HELPER TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestFormatAuthorMla:
    """Tests for _format_author_mla() helper function."""

    @pytest.mark.asyncio
    async def test_format_single_author_mla(self):
        """Single author → 'Smith, John'."""
        from src.services.citation_service import _format_author_mla

        result = _format_author_mla("Smith, John")
        assert result == "Smith, John"

    @pytest.mark.asyncio
    async def test_format_two_authors_mla(self):
        """Two authors → 'Smith, John, and Jane Doe'."""
        from src.services.citation_service import _format_author_mla

        result = _format_author_mla("Smith, John and Doe, Jane")
        assert result == "Smith, John, and Jane Doe"

    @pytest.mark.asyncio
    async def test_format_three_authors_mla(self):
        """Three+ authors → 'Smith, John, et al.'."""
        from src.services.citation_service import _format_author_mla

        result = _format_author_mla("Smith, John and Doe, Jane and Johnson, Robert")
        assert result == "Smith, John, et al."


# ═════════════════════════════════════════════════════════════════════════════
# 9. GENERATE BIBTEX KEY HELPER TESTS
# ═════════════════════════════════════════════════════════════════════════════


class TestGenerateBibtexKey:
    """Tests for _generate_bibtex_key() helper function."""

    @pytest.mark.asyncio
    async def test_basic_key_generation(self):
        """'Smith', '2020', 'Deep Learning in Medicine' → 'smith2020deep'."""
        from src.services.citation_service import _generate_bibtex_key

        result = _generate_bibtex_key("Smith, John", "2020", "Deep Learning in Medicine")
        assert result == "smith2020deep"

    @pytest.mark.asyncio
    async def test_key_skips_common_words(self):
        """Title starting with 'The' → skips to first significant word."""
        from src.services.citation_service import _generate_bibtex_key

        result = _generate_bibtex_key("Smith, John", "2020", "The Art of Machine Learning")
        assert result == "smith2020art"

    @pytest.mark.asyncio
    async def test_key_skips_articles(self):
        """Title starting with 'A' → skips to first significant word."""
        from src.services.citation_service import _generate_bibtex_key

        result = _generate_bibtex_key("Doe, Jane", "2021", "A Survey of Neural Networks")
        assert result == "doe2021survey"

    @pytest.mark.asyncio
    async def test_key_lowercase(self):
        """Key should be all lowercase."""
        from src.services.citation_service import _generate_bibtex_key

        result = _generate_bibtex_key("SMITH, JOHN", "2020", "DEEP LEARNING")
        assert result == result.lower()

    @pytest.mark.asyncio
    async def test_key_no_year(self):
        """No year → uses '0000'."""
        from src.services.citation_service import _generate_bibtex_key

        result = _generate_bibtex_key("Smith, John", "n.d.", "Deep Learning")
        assert "0000" in result

    @pytest.mark.asyncio
    async def test_key_special_characters_removed(self):
        """Special characters in author name → removed from key."""
        from src.services.citation_service import _generate_bibtex_key

        result = _generate_bibtex_key("O'Brien, John", "2020", "Test Paper")
        # apostrophe removed, should be "obrien2020test"
        assert "'" not in result
        assert result == "obrien2020test"

    @pytest.mark.asyncio
    async def test_key_empty_author(self):
        """Empty author → key starts with 'unknown'."""
        from src.services.citation_service import _generate_bibtex_key

        result = _generate_bibtex_key("", "2020", "Deep Learning")
        assert result.startswith("unknown")
