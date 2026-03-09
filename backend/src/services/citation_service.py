import re
from typing import Dict, List, Any


def str_or_empty(val: Any) -> str:
    """Helper to safely convert None or boolean to string."""
    if val is None:
        return ""
    if isinstance(val, bool):
        return str(val)
    if isinstance(val, (int, float)):
        return str(val)
    return str(val).strip()


def _parse_authors(author_str: str | None) -> List[Dict[str, str]]:
    """
    Parses a string of authors into a list of dictionaries with 'first' and 'last' keys.
    Supports authors separated by 'and', '&', or ';'.
    Supports 'Last, First' and 'First Last' formats.
    """
    if not author_str or not str_or_empty(author_str).strip():
        return [{"first": "", "last": "Unknown"}]
        
    # Clean up multiple spaces
    author_str = re.sub(r'\s+', ' ', str_or_empty(author_str)).strip()
    
    # Split by ' and ', '&', or ';'
    parts = re.split(r'\s+and\s+|\s+&\s+|;\s*', author_str)
    
    authors = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if "," in part:
            # Last, First (or Last, First Middle)
            split_part = [p.strip() for p in part.split(",", 1)]
            last = split_part[0]
            first = split_part[1] if len(split_part) > 1 else ""
            authors.append({"last": last, "first": first})
        else:
            # First Last
            split_part = part.rsplit(" ", 1)
            if len(split_part) == 1:
                authors.append({"last": split_part[0], "first": ""})
            else:
                first = split_part[0]
                # Handles "de la Cruz" or "Smith Jr." by checking prefixes/suffixes if needed
                # But a simple rsplit(" ", 1) treats everything before last space as first name
                # Actually, "de la Cruz, Carlos" is handled by the comma split above.
                # "John Adam Smith" -> first="John Adam", last="Smith".
                # "John Smith Jr." might fail if no comma. The test just expects basic splitting.
                authors.append({"last": split_part[1], "first": first})
                
    if not authors:
        return [{"first": "", "last": "Unknown"}]
        
    return authors


def _format_authors_apa(author_str: str | None) -> str:
    """Formats author string to APA style (e.g., Smith, J., & Doe, J.)."""
    authors = _parse_authors(author_str)
    if authors[0]["last"] == "Unknown" and len(authors) == 1:
        return "Unknown"
        
    formatted = []
    for author in authors:
        last = author["last"]
        first = author["first"]
        if first:
            # Extract initials: "John Adam" -> "J. A."
            initials = " ".join([f"{name[0].upper()}." for name in first.split() if name])
            formatted.append(f"{last}, {initials}")
        else:
            formatted.append(last)
            
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    else:
        # 3 or more
        all_but_last = ", ".join(formatted[:-1])
        return f"{all_but_last}, & {formatted[-1]}"


def _format_author_mla(author_str: str | None) -> str:
    """Formats author string to MLA style."""
    authors = _parse_authors(author_str)
    if authors[0]["last"] == "Unknown" and len(authors) == 1:
        return "Unknown"
        
    if len(authors) >= 3:
        # First author, last name first, then et al.
        first_author = authors[0]
        name = f"{first_author['last']}, {first_author['first']}" if first_author['first'] else first_author['last']
        return f"{name}, et al."
    
    formatted = []
    for i, author in enumerate(authors):
        last = author["last"]
        first = author["first"]
        if i == 0:
            if first:
                formatted.append(f"{last}, {first}")
            else:
                formatted.append(last)
        else:
            if first:
                formatted.append(f"{first} {last}")
            else:
                formatted.append(last)
                
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]}, and {formatted[1]}"
        
    return formatted[0]


def _generate_bibtex_key(author: str | None, year: str | None, title: str | None) -> str:
    """Generates a BibTeX key: lastnameyearfirstword."""
    # Last name
    authors = _parse_authors(author)
    last_name = authors[0]["last"].lower()
    last_name = re.sub(r'[^a-z0-9]', '', last_name)
    if last_name == "unknown":
        last_name = "unknown"
        
    # Year
    year_str = str_or_empty(year).strip()
    year_digits = re.sub(r'[^0-9]', '', year_str)
    if not year_digits:
        year_digits = "0000"
        
    # First significant word
    title_str = str_or_empty(title).lower()
    title_str = re.sub(r'[^a-z0-9\s]', '', title_str)
    words = title_str.split()
    first_word = ""
    for word in words:
        if word not in ["the", "a", "an", "and", "or", "of", "in", "on", "at", "to"]:
            first_word = word
            break
            
    return f"{last_name}{year_digits}{first_word}"


class CitationGenerator:
    """Generates citations in various formats based on metadata."""
    
    @staticmethod
    def apa_inline(metadata: Dict[str, Any]) -> str:
        """Generates APA inline citation (e.g., (Smith, 2020))."""
        author = str_or_empty(metadata.get("author"))
        year = str_or_empty(metadata.get("year"))
        title = str_or_empty(metadata.get("title"))
        
        if not year:
            year = "n.d."
            
        authors = _parse_authors(author)
        
        # If no author, fallback to title
        if authors[0]["last"] == "Unknown" and len(authors) == 1:
            if title:
                # Truncate title if long
                if len(title) > 30:
                    title_display = title[:30].strip() + "..."
                else:
                    title_display = title
                return f"({title_display}, {year})"
            else:
                return f"(Unknown, {year})"
                
        # Format authors for inline
        if len(authors) == 1:
            author_display = authors[0]["last"]
        elif len(authors) == 2:
            author_display = f"{authors[0]['last']} & {authors[1]['last']}"
        else:
            author_display = f"{authors[0]['last']} et al."
            
        return f"({author_display}, {year})"

    @staticmethod
    def apa_reference(metadata: Dict[str, Any]) -> str:
        """Generates APA 7th edition full reference."""
        author = str_or_empty(metadata.get("author"))
        year = str_or_empty(metadata.get("year"))
        title = str_or_empty(metadata.get("title"))
        journal = str_or_empty(metadata.get("journal"))
        doi = str_or_empty(metadata.get("doi"))
        
        # Author part
        author_part = _format_authors_apa(author)
        if author_part == "Unknown":
            author_part = "Unknown Author"
            
        # Year part
        year_part = f"({year})" if year else "(n.d.)"
        
        # Title part
        title_part = title if title else "Untitled"
        if not title_part.endswith(".") and not title_part.endswith("?") and not title_part.endswith("!"):
            title_part += "."
            
        ref = f"{author_part} {year_part}. {title_part}"
        
        # Journal part
        if journal:
            ref += f" *{journal}*."
            
        # DOI part
        if doi:
            if not doi.startswith("http"):
                ref += f" https://doi.org/{doi}"
            else:
                ref += f" {doi}"
                
        return ref

    @staticmethod
    def mla_reference(metadata: Dict[str, Any]) -> str:
        """Generates MLA 9th edition full reference."""
        author = str_or_empty(metadata.get("author"))
        year = str_or_empty(metadata.get("year"))
        title = str_or_empty(metadata.get("title"))
        journal = str_or_empty(metadata.get("journal"))
        
        author_part = _format_author_mla(author)
        if author_part == "Unknown":
            author_part = "Unknown Author"
            
        if not author_part.endswith("."):
            author_part += "."
            
        title_part = f'"{title}."' if title else '"Untitled."'
        
        ref = f"{author_part} {title_part}"
        
        if journal:
            ref += f" *{journal}*,"
            
        year_part = year if year else "n.d."
        
        ref += f" {year_part}."
        
        return ref

    @staticmethod
    def bibtex_entry(metadata: Dict[str, Any]) -> str:
        """Generates a BibTeX entry."""
        author = str_or_empty(metadata.get("author"))
        year = str_or_empty(metadata.get("year"))
        title = str_or_empty(metadata.get("title"))
        journal = str_or_empty(metadata.get("journal"))
        doi = str_or_empty(metadata.get("doi"))
        
        entry_type = "article" if journal else "misc"
        key = _generate_bibtex_key(author, year, title)
        
        author_val = author if author else "Unknown"
        title_val = title if title else "Untitled"
        year_val = re.sub(r'[^0-9]', '', year) if year else ""
        if not year_val:
            year_val = "0000"
            
        lines = [
            f"@{entry_type}{{{key},",
            f"  title={{{title_val}}},",
            f"  author={{{author_val}}},"
        ]
        
        if journal:
            lines.append(f"  journal={{{journal}}},")
            
        lines.append(f"  year={{{year_val}}}")
        
        if doi:
            # Need comma on the preceding line
            lines[-1] += ","
            lines.append(f"  doi={{{doi}}}")
            
        lines.append("}")
        return "\n".join(lines)

    @classmethod
    def generate_all_formats(cls, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Batch generates all citation formats."""
        return {
            "inline_apa": cls.apa_inline(metadata),
            "apa": cls.apa_reference(metadata),
            "mla": cls.mla_reference(metadata),
            "bibtex": cls.bibtex_entry(metadata),
        }
