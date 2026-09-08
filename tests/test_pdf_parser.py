from pathlib import Path
from pypdf import PdfWriter
from src.pdf_parser import extract_pdf_pages


def test_empty_pdf_page_is_reported(tmp_path: Path):
    path = tmp_path / "empty.pdf"; writer = PdfWriter(); writer.add_blank_page(width=100, height=100)
    with path.open("wb") as output: writer.write(output)
    page = extract_pdf_pages(path)[0]
    assert page.page_number == 1
    assert page.extraction_note is not None
