"""Local document parsing and digest generation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from pypdf import PdfReader

from nanofolks.config.schema import DocumentToolsConfig
from nanofolks.utils.helpers import ensure_dir, safe_filename


@dataclass
class DocumentDigest:
    doc_id: str
    filename: str
    source_path: str
    text_path: str
    summary: str
    page_count: int
    extracted_chars: int
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "source_path": self.source_path,
            "text_path": self.text_path,
            "summary": self.summary,
            "page_count": self.page_count,
            "extracted_chars": self.extracted_chars,
            "created_at": self.created_at,
        }


class DocumentProcessor:
    """Extract text from PDFs and generate short digests."""

    def __init__(self, base_dir: Path, config: DocumentToolsConfig):
        self.base_dir = ensure_dir(base_dir / "documents")
        self.config = config

    def process_pdfs(
        self,
        paths: list[str],
        *,
        room_id: str,
        session_metadata: dict[str, Any],
    ) -> list[DocumentDigest]:
        digests: list[DocumentDigest] = []
        if not paths or not room_id:
            return digests

        for path in paths:
            if not self._is_pdf(path):
                continue
            digest = self._process_single_pdf(path, room_id, session_metadata)
            if digest:
                digests.append(digest)

        return digests

    def _process_single_pdf(
        self,
        path: str,
        room_id: str,
        session_metadata: dict[str, Any],
    ) -> DocumentDigest | None:
        source_path = Path(path)
        if not source_path.exists() or not source_path.is_file():
            return None

        doc_id = self._fingerprint(source_path)
        documents = session_metadata.setdefault("documents", [])
        for existing in documents:
            if existing.get("doc_id") == doc_id:
                return DocumentDigest(**existing)

        try:
            text, page_count = self._extract_pdf_text(source_path)
        except Exception as e:
            logger.warning(f"Failed to parse PDF {source_path}: {e}")
            return None

        extracted_chars = len(text)
        summary = self._summarize(text)

        room_dir = ensure_dir(self.base_dir / safe_filename(room_id))
        safe_name = safe_filename(source_path.stem)
        text_path = room_dir / f"{safe_name}_{doc_id[:10]}.txt"
        try:
            text_path.write_text(text, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write extracted text for {source_path}: {e}")
            return None

        digest = DocumentDigest(
            doc_id=doc_id,
            filename=source_path.name,
            source_path=str(source_path),
            text_path=str(text_path),
            summary=summary,
            page_count=page_count,
            extracted_chars=extracted_chars,
            created_at=datetime.now().isoformat(),
        )
        documents.append(digest.to_dict())
        session_metadata["documents"] = documents
        return digest

    def _extract_pdf_text(self, path: Path) -> tuple[str, int]:
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        max_pages = max(1, int(self.config.max_pages))
        max_chars = max(1000, int(self.config.max_chars))

        parts: list[str] = []
        chars = 0
        for page in reader.pages[:max_pages]:
            page_text = page.extract_text() or ""
            if page_text:
                parts.append(page_text)
                chars += len(page_text)
            if chars >= max_chars:
                break

        text = "\n".join(parts).strip()
        if len(text) > max_chars:
            text = text[:max_chars]
        return text, page_count

    def _summarize(self, text: str) -> str:
        if not text:
            return "No extractable text found (possibly scanned or image-based)."

        cleaned = re.sub(r"\s+", " ", text).strip()
        summary_chars = max(200, int(self.config.summary_chars))

        # Try sentence-based preview
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        if sentences and len(sentences) > 1:
            summary = " ".join(sentences[:5]).strip()
        else:
            summary = cleaned[:summary_chars].strip()

        if len(summary) > summary_chars:
            summary = summary[: summary_chars - 3].strip() + "..."
        return summary

    @staticmethod
    def _is_pdf(path: str) -> bool:
        return path.lower().endswith(".pdf")

    @staticmethod
    def _fingerprint(path: Path) -> str:
        stat = path.stat()
        raw = f"{path.resolve()}::{stat.st_size}::{stat.st_mtime_ns}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()
