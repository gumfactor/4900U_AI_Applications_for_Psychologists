from pathlib import Path

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
        assert "concepts:" in text
        assert "people:" in text
        assert "sources:" in text
        assert "projects:" in text
        assert "\ntype:" not in text
        assert "\ntopic:" not in text
