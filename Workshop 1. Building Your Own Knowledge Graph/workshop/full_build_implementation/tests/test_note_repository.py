from pathlib import Path
from shutil import copytree, rmtree

from app.services.ai_service import AiService
from app.services.note_repository import NoteRepository


def test_note_repository_loads_seeded_notes() -> None:
    notes_dir = Path(__file__).resolve().parent.parent / "data" / "notes"
    repository = NoteRepository(notes_dir)
    notes = repository.list_notes()
    assert len(notes) >= 7
    assert any(note.metadata.title == "Instructor Demo System" for note in notes)
    assert any(note.metadata.note_kind is None for note in notes)


def test_note_repository_extracts_links() -> None:
    notes_dir = Path(__file__).resolve().parent.parent / "data" / "notes"
    repository = NoteRepository(notes_dir)
    note = repository.get_note("concept-personal-knowledge-base")
    assert note.links
    assert any(link.relationship == "related_to" for link in note.links)


def test_seeded_notes_use_refactored_schema() -> None:
    notes_dir = Path(__file__).resolve().parent.parent / "data" / "notes"
    for path in notes_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert "topics:" in text
        assert "people:" in text
        assert "sources:" in text
        assert "projects:" in text
        assert "\ntype:" not in text
        assert "\ntopic:" not in text


def test_ai_service_parses_metadata_yaml_output() -> None:
    parsed = AiService._parse_metadata_yaml(
        """```yaml
note_kind: method-note
topics:
  - Knowledge Bases
people:
  - Ada Lovelace
sources:
  - Example Source
projects:
  - Demo Project
tags:
  - structure
  - workflow
source_refs:
  - data/sources/example.md
```"""
    )
    assert parsed["note_kind"] == "method-note"
    assert parsed["topics"] == ["Knowledge Bases"]
    assert parsed["people"] == ["Ada Lovelace"]
    assert parsed["source_refs"] == ["data/sources/example.md"]


def test_note_repository_updates_existing_note() -> None:
    source_base_dir = Path(__file__).resolve().parent.parent
    copied_base_dir = source_base_dir / "_test_runtime" / "repo_copy"
    rmtree(copied_base_dir, ignore_errors=True)
    copytree(source_base_dir / "data", copied_base_dir / "data")
    repository = NoteRepository(copied_base_dir / "data" / "notes")
    updated = repository.update_note(
        slug="concept-personal-knowledge-base",
        title="Updated PKB Note",
        note_kind="reflection",
        topics=["Knowledge Work"],
        people=["Workshop Instructor"],
        sources=["PKB Design Principles"],
        projects=["Instructor Demo System"],
        source_refs=["data/sources/source-pkb-design-principles.md"],
        tags=["updated"],
        content="Updated content for the repository test.",
        status="reviewed",
        ai_assisted=True,
        human_reviewed=True,
    )
    assert updated.metadata.title == "Updated PKB Note"
    assert updated.metadata.note_kind == "reflection"
    assert updated.metadata.status == "reviewed"
    assert updated.metadata.human_reviewed is True
