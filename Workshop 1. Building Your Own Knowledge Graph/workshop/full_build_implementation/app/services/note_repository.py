from __future__ import annotations

from pathlib import Path
import re

from app.models import Note
from app.services.markdown_utils import (
    build_note_document,
    build_note_markdown,
    bullet_lines,
    dump_frontmatter,
    extract_links,
    parse_frontmatter,
    split_sections,
    today_iso,
    validate_metadata,
)


class NoteRepository:
    def __init__(self, notes_dir: Path) -> None:
        self.notes_dir = notes_dir

    def list_notes(self) -> list[Note]:
        return [self._load_note(path) for path in sorted(self.notes_dir.glob("*.md"))]

    def get_note(self, slug: str) -> Note:
        for note in self.list_notes():
            if note.slug == slug:
                return note
        raise FileNotFoundError(f"Note not found: {slug}")

    def save_draft(
        self,
        title: str,
        status: str,
        topics: list[str],
        people: list[str],
        sources: list[str],
        projects: list[str],
        source_refs: list[str],
        attachments: list[str],
        tags: list[str],
        due_date: str | None,
        content: str,
    ) -> Note:
        filename, markdown = build_note_markdown(
            title,
            status,
            topics,
            people,
            sources,
            projects,
            source_refs,
            attachments,
            tags,
            due_date,
            content,
        )
        path = self.notes_dir / filename
        path.write_text(markdown, encoding="utf-8")
        return self._load_note(path)

    def update_note(
        self,
        slug: str,
        title: str,
        status: str,
        topics: list[str],
        people: list[str],
        sources: list[str],
        projects: list[str],
        source_refs: list[str],
        attachments: list[str],
        tags: list[str],
        due_date: str | None,
        content: str,
    ) -> Note:
        note = self.get_note(slug)
        path = self.notes_dir / f"{note.slug}.md"
        metadata = {
            "id": note.metadata.id,
            "title": title,
            "status": status,
            "topics": topics,
            "people": people,
            "sources": sources,
            "projects": projects,
            "tags": tags,
            "source_refs": source_refs,
            "attachments": attachments,
            "due_date": due_date,
            "created": note.metadata.created,
            "updated": today_iso(),
        }
        path.write_text(build_note_document(title, metadata, content), encoding="utf-8")
        return self._load_note(path)

    def delete_note(self, slug: str) -> Note:
        note = self.get_note(slug)
        path = self.notes_dir / f"{note.slug}.md"
        path.unlink()
        return note

    def _load_note(self, path: Path) -> Note:
        frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        metadata = validate_metadata(frontmatter)
        sections = split_sections(body)
        linked_notes_markdown = sections.get("Linked Notes", "")
        return Note(
            metadata=metadata,
            slug=path.stem,
            path=str(path.relative_to(self.notes_dir.parent.parent).as_posix()),
            raw_body=body,
            summary=sections.get("Summary", "") or self._plain_note_body(body),
            key_points=bullet_lines(sections.get("Key Points", "")),
            evidence=bullet_lines(sections.get("Evidence / Sources", "")),
            open_questions=bullet_lines(sections.get("Open Questions", "")),
            linked_notes_markdown=linked_notes_markdown,
            links=extract_links(linked_notes_markdown),
        )

    @staticmethod
    def _plain_note_body(body: str) -> str:
        return re.sub(r"^# .+\n+", "", body.strip(), count=1).strip()
