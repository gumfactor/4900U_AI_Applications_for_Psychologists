from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from shutil import rmtree

import yaml

from app.models import Note, NoteVersion
from app.services.markdown_utils import bullet_lines, extract_links, parse_frontmatter, slugify, split_sections, validate_metadata


class NoteHistoryService:
    def __init__(self, history_dir: Path, notes_dir: Path) -> None:
        self.history_dir = history_dir
        self.notes_dir = notes_dir

    def list_versions(self, note_slug: str) -> list[NoteVersion]:
        version_dir = self.history_dir / note_slug
        if not version_dir.exists():
            return []
        versions = [self._load_version(path) for path in sorted(version_dir.glob("*.md"))]
        versions.sort(key=lambda version: version.timestamp)
        return versions

    def get_version(self, note_slug: str, version_slug: str) -> NoteVersion:
        version_path = self.history_dir / note_slug / f"{version_slug}.md"
        if not version_path.exists():
            raise FileNotFoundError(f"Version not found: {version_slug}")
        return self._load_version(version_path)

    def record_version(self, note: Note, action: str) -> NoteVersion:
        timestamp = datetime.now(UTC).astimezone().isoformat(timespec="seconds")
        version_slug = slugify(f"{timestamp}-{action}")
        version_dir = self.history_dir / note.slug
        version_dir.mkdir(parents=True, exist_ok=True)
        note_path = self.notes_dir / f"{note.slug}.md"
        note_markdown = note_path.read_text(encoding="utf-8")
        payload = {
            "note_slug": note.slug,
            "captured_at": timestamp,
            "action": action,
            "title": note.metadata.title,
        }
        document = f"---\n{yaml.safe_dump(payload, sort_keys=False, allow_unicode=False).strip()}\n---\n\n{note_markdown}"
        path = version_dir / f"{version_slug}.md"
        path.write_text(document, encoding="utf-8")
        return self._load_version(path)

    def ensure_history(self, note: Note) -> list[NoteVersion]:
        versions = self.list_versions(note.slug)
        if versions:
            return versions
        self.record_version(note, action="imported")
        return self.list_versions(note.slug)

    def delete_history(self, note_slug: str) -> None:
        rmtree(self.history_dir / note_slug, ignore_errors=True)

    def _load_version(self, path: Path) -> NoteVersion:
        version_meta, note_markdown = parse_frontmatter(path.read_text(encoding="utf-8"))
        note_frontmatter, body = parse_frontmatter(note_markdown)
        metadata = validate_metadata(note_frontmatter)
        sections = split_sections(body)
        linked_notes_markdown = sections.get("Linked Notes", "")
        note = Note(
            metadata=metadata,
            slug=str(version_meta.get("note_slug", path.parent.name)),
            path=str((self.notes_dir / f"{version_meta.get('note_slug', path.parent.name)}.md").relative_to(self.notes_dir.parent.parent).as_posix()),
            raw_body=body,
            summary=sections.get("Summary", ""),
            key_points=bullet_lines(sections.get("Key Points", "")),
            evidence=bullet_lines(sections.get("Evidence / Sources", "")),
            open_questions=bullet_lines(sections.get("Open Questions", "")),
            linked_notes_markdown=linked_notes_markdown,
            links=extract_links(linked_notes_markdown),
        )
        return NoteVersion(
            slug=path.stem,
            note_slug=str(version_meta.get("note_slug", path.parent.name)),
            timestamp=str(version_meta.get("captured_at", "")),
            action=str(version_meta.get("action", "updated")),
            title=str(version_meta.get("title", metadata.title)),
            path=str(path.relative_to(self.notes_dir.parent.parent).as_posix()),
            raw_markdown=note_markdown,
            note=note,
        )
