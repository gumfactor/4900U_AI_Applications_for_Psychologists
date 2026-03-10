from __future__ import annotations

import base64
import re
from pathlib import Path

from app.models import AttachmentUpload


class AttachmentService:
    def __init__(self, attachments_dir: Path) -> None:
        self.attachments_dir = attachments_dir
        self.attachments_dir.mkdir(parents=True, exist_ok=True)

    def save_uploads(self, note_slug: str, uploads: list[AttachmentUpload]) -> list[str]:
        saved_paths: list[str] = []
        if not uploads:
            return saved_paths

        note_dir = self.attachments_dir / note_slug
        note_dir.mkdir(parents=True, exist_ok=True)
        for upload in uploads:
            filename = self._unique_filename(note_dir, upload.name or "attachment")
            target_path = note_dir / filename
            content = base64.b64decode(upload.content_base64)
            target_path.write_bytes(content)
            saved_paths.append(str(target_path.relative_to(self.attachments_dir.parent).as_posix()))
        return saved_paths

    def build_link(self, attachment_path: str) -> str:
        normalized = attachment_path.replace("\\", "/").removeprefix("data/attachments/")
        return f"/attachments/{normalized}"

    @staticmethod
    def display_name(attachment_path: str) -> str:
        return Path(attachment_path).name

    def _unique_filename(self, note_dir: Path, filename: str) -> str:
        stem = self._sanitize(Path(filename).stem) or "attachment"
        suffix = self._sanitize_suffix(Path(filename).suffix)
        candidate = f"{stem}{suffix}"
        counter = 2
        while (note_dir / candidate).exists():
            candidate = f"{stem}-{counter}{suffix}"
            counter += 1
        return candidate

    @staticmethod
    def _sanitize(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-")

    @staticmethod
    def _sanitize_suffix(value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9.]+", "", value)
        return cleaned if cleaned.startswith(".") else ""
