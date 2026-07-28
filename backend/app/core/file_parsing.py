"""Lightweight text extraction for demo purposes only.

The assignment explicitly says production-grade OCR/document parsing is not
required - this just needs to get plain text out of a .txt/.eml file or a
text-based PDF so the LangGraph pipeline has something to work with.
"""
import io

from pypdf import PdfReader


def extract_text_from_bytes(filename: str, content: bytes) -> str:
    lower = filename.lower()

    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    # .txt, .eml, and anything else: best-effort decode as plain text.
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="ignore")
