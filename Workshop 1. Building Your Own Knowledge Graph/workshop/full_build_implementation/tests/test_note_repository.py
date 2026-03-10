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
    assert parsed["topics"] == ["Knowledge Bases"]
    assert parsed["people"] == ["Ada Lovelace"]
    assert parsed["source_refs"] == ["data/sources/example.md"]


def test_ai_service_parses_relaxed_metadata_output() -> None:
    parsed = AiService._parse_metadata_yaml(
        """topics:
- Knowledge Bases
people:
- Ada Lovelace
sources:
- Example Source
projects:
- Demo Project
tags:
- structure
source_refs:
- data/sources/example.md
"""
    )
    assert parsed["topics"] == ["Knowledge Bases"]
    assert parsed["projects"] == ["Demo Project"]


def test_note_repository_updates_existing_note() -> None:
    source_base_dir = Path(__file__).resolve().parent.parent
    copied_base_dir = source_base_dir / "_test_runtime" / "repo_copy"
    rmtree(copied_base_dir, ignore_errors=True)
    copytree(source_base_dir / "data", copied_base_dir / "data")
    repository = NoteRepository(copied_base_dir / "data" / "notes")
    updated = repository.update_note(
        slug="concept-personal-knowledge-base",
        title="Updated PKB Note",
        topics=["Knowledge Work"],
        people=["Workshop Instructor"],
        sources=["PKB Design Principles"],
        projects=["Instructor Demo System"],
        source_refs=["data/sources/source-pkb-design-principles.md"],
        attachments=["data/attachments/concept-personal-knowledge-base/example.pdf"],
        tags=["updated"],
        content="Updated content for the repository test.",
    )
    assert updated.metadata.title == "Updated PKB Note"
    assert updated.summary == "Updated content for the repository test."


def test_note_repository_uses_plain_note_body_as_summary() -> None:
    source_base_dir = Path(__file__).resolve().parent.parent
    copied_base_dir = source_base_dir / "_test_runtime" / "repo_plain_copy"
    rmtree(copied_base_dir, ignore_errors=True)
    copytree(source_base_dir / "data", copied_base_dir / "data")
    repository = NoteRepository(copied_base_dir / "data" / "notes")
    note = repository.update_note(
        slug="concept-personal-knowledge-base",
        title="Plain Body Note",
        topics=["Knowledge Work"],
        people=["Workshop Instructor"],
        sources=["PKB Design Principles"],
        projects=["Instructor Demo System"],
        source_refs=["data/sources/source-pkb-design-principles.md"],
        attachments=[],
        tags=["plain-body"],
        content="This is the actual note body.\n\nIt has two paragraphs.",
    )
    assert note.summary == "This is the actual note body.\n\nIt has two paragraphs."
    assert note.raw_body.startswith("# Plain Body Note")


def test_note_repository_deletes_existing_note() -> None:
    source_base_dir = Path(__file__).resolve().parent.parent
    copied_base_dir = source_base_dir / "_test_runtime" / "repo_delete_copy"
    rmtree(copied_base_dir, ignore_errors=True)
    copytree(source_base_dir / "data", copied_base_dir / "data")
    repository = NoteRepository(copied_base_dir / "data" / "notes")
    deleted = repository.delete_note("concept-personal-knowledge-base")
    assert deleted.slug == "concept-personal-knowledge-base"
    assert not (copied_base_dir / "data" / "notes" / "concept-personal-knowledge-base.md").exists()
