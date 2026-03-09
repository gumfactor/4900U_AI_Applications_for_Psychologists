from __future__ import annotations

from pathlib import Path

from app.models import SourceDocument
from app.services.markdown_utils import note_title_from_path


class SourceRepository:
    def __init__(self, sources_dir: Path) -> None:
        self.sources_dir = sources_dir

    def list_sources(self) -> list[SourceDocument]:
        return [
            SourceDocument(
                slug=path.stem,
                title=note_title_from_path(path),
                path=str(path.relative_to(self.sources_dir.parent.parent).as_posix()),
                content=path.read_text(encoding="utf-8"),
            )
            for path in sorted(self.sources_dir.glob("*.md"))
        ]

    def get_source(self, slug: str) -> SourceDocument:
        for source in self.list_sources():
            if source.slug == slug:
                return source
        raise FileNotFoundError(f"Source not found: {slug}")
