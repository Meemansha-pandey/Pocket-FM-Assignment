"""
extractor.py — extract plain text from PDF, Markdown, or TXT files.
"""

import os
from pathlib import Path


def extract_text(file_path: str) -> str:
    """Extract plain text from a PDF, .md, or .txt file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(path)
    elif suffix in (".md", ".markdown", ".txt", ""):
        return _extract_text_file(path)
    else:
        raise ValueError(
            f"Unsupported file type: '{suffix}'. Supported: .pdf, .md, .txt"
        )


def _extract_pdf(path: Path) -> str:
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF support. Run: pip install pdfplumber")

    text_parts = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    full_text = "\n\n".join(text_parts).strip()
    if not full_text:
        raise ValueError(f"No text could be extracted from PDF: {path.name}. It may be a scanned image PDF.")

    return full_text


def _extract_text_file(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().strip()
