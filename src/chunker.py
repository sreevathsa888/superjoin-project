"""Page-bounded chunking that never loses source page information."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .pdf_parser import ExtractedPage


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    page_number: int
    text: str
    is_table_like: bool
    note: str | None = None


def _looks_table_like(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    return len(lines) > 4 and sum(1 for line in lines if "  " in line or "\t" in line) / len(lines) > 0.45


def chunk_pages(pages: list[ExtractedPage], size: int = 3500, overlap: int = 250) -> list[Chunk]:
    """Split each page by sentence-ish boundaries, retaining tables as flagged text."""
    chunks: list[Chunk] = []
    for page in pages:
        if not page.text:
            chunks.append(Chunk(str(uuid4()), page.page_number, "", False, page.extraction_note))
            continue
        start = 0
        while start < len(page.text):
            end = min(start + size, len(page.text))
            if end < len(page.text):
                break_at = max(page.text.rfind(". ", start, end), page.text.rfind("\n", start, end))
                if break_at > start + size // 2:
                    end = break_at + 1
            text = page.text[start:end].strip()
            chunks.append(Chunk(str(uuid4()), page.page_number, text, _looks_table_like(text)))
            if end >= len(page.text):
                break
            start = max(end - overlap, start + 1)
    return chunks
