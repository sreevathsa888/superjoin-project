"""Page-aware PDF extraction with PyMuPDF preferred and pypdf fallback."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


class PDFExtractionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str
    extraction_note: str | None = None


def extract_pdf_pages(path: str | Path, max_pages: int = 150) -> list[ExtractedPage]:
    """Extract text per page without assuming a document-specific layout."""
    path = Path(path)
    if path.suffix.lower() != ".pdf":
        raise PDFExtractionError("Only PDF files are accepted.")
    try:
        try:
            import pymupdf as fitz  # type: ignore
            doc = fitz.open(path)
            pages = [ExtractedPage(i + 1, page.get_text("text").strip()) for i, page in enumerate(doc[:max_pages])]
        except ImportError:
            reader = PdfReader(str(path))
            pages = [ExtractedPage(i + 1, (page.extract_text() or "").strip()) for i, page in enumerate(reader.pages[:max_pages])]
    except Exception as error:
        raise PDFExtractionError(f"Could not read PDF: {error}") from error
    if not pages:
        raise PDFExtractionError("The PDF has no pages.")
    return [page if page.text else ExtractedPage(page.page_number, "", "No extractable text; OCR is required.") for page in pages]
