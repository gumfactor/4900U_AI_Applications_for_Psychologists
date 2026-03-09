from pathlib import Path

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
