"""
Legal Act Parser — section-aware PDF parser for Indian legal documents.

WHAT IT DOES:
  Unlike a generic PDF loader that treats a document as a flat stream of text,
  this parser understands the STRUCTURE of Indian legal acts:

    Act Title
      └── Chapter (CHAPTER I, CHAPTER II, ...)
            └── Section (Section 1, Section 2, ...)
                  └── Sub-sections, clauses, etc.

  It splits the PDF at section boundaries and attaches rich metadata to each
  section (act_name, section_number, chapter, category, etc.).

WHY THIS MATTERS:
  With rich metadata on every chunk, we can:
    1. Filter searches to specific acts or categories
    2. Show exact section citations in the UI
    3. Keep legal sections intact (not split mid-sentence)

REGEX PATTERNS:
  Indian legal acts consistently use patterns like:
    "Section 42." or "S. 42" for sections
    "CHAPTER VI" or "Chapter 6" for chapters
  We detect these with regular expressions to find boundaries.
"""

import re
from pathlib import Path
from typing import Dict, List

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from loguru import logger


class LegalActParser:
    """Parse Indian legal act PDFs into structured Document objects.

    Usage:
        parser = LegalActParser(
            act_name="Consumer Protection Act",
            act_year="2019",
            act_category="consumer"
        )
        documents = parser.load_and_parse("data/legal_acts/consumer_protection_2019.pdf")
        # Each document has metadata: {act_name, section_number, chapter, category, ...}
    """

    # Regex patterns for detecting legal document structure
    SECTION_PATTERN = re.compile(
        r"(?:Section|S\.)\s*(\d+[A-Z]?)[\.\s\-—:]+(.{0,100}?)(?:\n|\.)",
        re.IGNORECASE,
    )
    CHAPTER_PATTERN = re.compile(
        r"(?:CHAPTER|Chapter)\s+([IVXLC\d]+)[\.\s\-—:]*(.{0,100}?)(?:\n|$)",
    )

    def __init__(self, act_name: str, act_year: str, act_category: str):
        """
        Initialize the parser for a specific legal act.

        Args:
            act_name: Full name of the act (e.g., "Consumer Protection Act")
            act_year: Year of the act (e.g., "2019")
            act_category: Category for filtering (e.g., "consumer", "rti", "property")
        """
        self.act_name = act_name
        self.act_year = act_year
        self.act_category = act_category

    def load_and_parse(self, pdf_path: str) -> List[Document]:
        """
        Load a PDF and parse it into section-level documents with rich metadata.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            List of Document objects, one per detected section (or per page
            if no sections are detected).
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info(f"Loading and parsing: {path.name}")

        # Step 1: Load raw pages using PyMuPDF (fast and accurate)
        loader = PyMuPDFLoader(str(path))
        raw_pages = loader.load()
        logger.info(f"Loaded {len(raw_pages)} pages from {path.name}")

        # Step 2: Try to extract sections from the raw pages
        sections = self._extract_sections(raw_pages)

        if sections:
            logger.success(
                f"Extracted {len(sections)} sections from '{self.act_name}'"
            )
            return sections
        else:
            # Fallback: if no sections detected, return page-level documents
            # with basic metadata
            logger.warning(
                f"No sections detected in '{path.name}'. "
                f"Using page-level documents as fallback."
            )
            return self._pages_as_documents(raw_pages)

    def _extract_sections(self, raw_pages: List[Document]) -> List[Document]:
        """
        Split raw pages into individual legal sections.

        Strategy:
          1. Concatenate all pages into one big text (with page markers)
          2. Find all section boundaries using regex
          3. Split text at those boundaries
          4. Create a Document for each section with rich metadata
        """
        # Combine all pages with markers so we can track page numbers
        full_text = ""
        page_markers = []  # List of (char_position, page_number) tuples

        for page_doc in raw_pages:
            page_markers.append((len(full_text), page_doc.metadata.get("page", 0)))
            full_text += page_doc.page_content + "\n\n"

        # Find all section boundaries
        section_matches = list(self.SECTION_PATTERN.finditer(full_text))
        if not section_matches:
            return []

        # Track current chapter
        chapter_matches = list(self.CHAPTER_PATTERN.finditer(full_text))
        chapters = [(m.start(), m.group(1).strip(), m.group(2).strip()) for m in chapter_matches]

        documents = []
        for i, match in enumerate(section_matches):
            section_num = match.group(1).strip()
            section_title = match.group(2).strip() if match.group(2) else ""

            # Extract text from this section start to next section start (or end)
            start = match.start()
            end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(full_text)
            section_text = full_text[start:end].strip()

            # Skip very short sections (likely false positives from regex)
            if len(section_text) < 50:
                continue

            # Determine which page this section falls on
            page_num = 0
            for char_pos, pnum in reversed(page_markers):
                if start >= char_pos:
                    page_num = pnum
                    break

            # Determine which chapter this section belongs to
            current_chapter = ""
            for ch_pos, ch_num, ch_title in reversed(chapters):
                if start >= ch_pos:
                    current_chapter = f"{ch_num} - {ch_title}" if ch_title else ch_num
                    break

            metadata = self._build_metadata(
                section_num=section_num,
                section_title=section_title,
                chapter=current_chapter,
                page=page_num,
            )
            documents.append(Document(page_content=section_text, metadata=metadata))

        return documents

    def _pages_as_documents(self, raw_pages: List[Document]) -> List[Document]:
        """Fallback: convert raw pages to Documents with basic act metadata."""
        documents = []
        for page_doc in raw_pages:
            if len(page_doc.page_content.strip()) < 50:
                continue  # Skip near-empty pages

            metadata = {
                "act_name": self.act_name,
                "act_year": self.act_year,
                "category": self.act_category,
                "page": page_doc.metadata.get("page", 0),
                "source_type": "legal_act",
                "source_file": page_doc.metadata.get("source", "unknown"),
            }
            documents.append(
                Document(page_content=page_doc.page_content, metadata=metadata)
            )
        return documents

    def _build_metadata(
        self, section_num: str, section_title: str, chapter: str, page: int
    ) -> Dict:
        """Build rich metadata dict for a parsed section."""
        return {
            "act_name": self.act_name,
            "act_year": self.act_year,
            "category": self.act_category,
            "section_number": section_num,
            "section_title": section_title,
            "chapter": chapter,
            "page": page,
            "source_type": "legal_act",
        }
