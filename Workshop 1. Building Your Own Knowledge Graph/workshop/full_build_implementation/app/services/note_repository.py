from __future__ import annotations

from pathlib import Path

from app.models import Note
from app.services.markdown_utils import (
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
        note_type: str,
        source_refs: list[str],
        tags: list[str],
        content: str,
        ai_assisted: bool,
    ) -> Note:
        filename, markdown = build_note_markdown(title, note_type, source_refs, tags, content, ai_assisted)
        path = self.notes_dir / filename
        path.write_text(markdown, encoding="utf-8")
        return self._load_note(path)

    def update_status(self, slug: str, status: str, human_reviewed: bool) -> Note:
        note = self.get_note(slug)
        path = self.notes_dir / f"{note.slug}.md"
        frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        frontmatter["status"] = status
        frontmatter["human_reviewed"] = human_reviewed
        frontmatter["updated"] = today_iso()
        updated_note_text = f"---\n{dump_frontmatter(frontmatter)}\n---\n\n{body}\n"
        path.write_text(updated_note_text, encoding="utf-8")
        return self._load_note(path)

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
            summary=sections.get("Summary", ""),
            key_points=bullet_lines(sections.get("Key Points", "")),
            evidence=bullet_lines(sections.get("Evidence / Sources", "")),
            open_questions=bullet_lines(sections.get("Open Questions", "")),
            linked_notes_markdown=linked_notes_markdown,
            links=extract_links(linked_notes_markdown),
        )
