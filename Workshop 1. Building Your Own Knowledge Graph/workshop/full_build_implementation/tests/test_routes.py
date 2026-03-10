from pathlib import Path
from shutil import copytree
from shutil import rmtree
import re

from fastapi.testclient import TestClient

from app.main import create_app


class FakeGeminiClient:
    def generate(self, prompt: str, model: str) -> str:
        if "Return the result in YAML only with exactly these keys" in prompt:
            return """topics:
  - Testing
people:
  - Test User
sources:
  - PKB Design Principles
projects:
  - Instructor Demo System
tags:
  - runtime
  - demo
source_refs: []
"""
        if "User note body:" in prompt:
            return """## Summary

Synthetic structured summary.

## Key Points

- Point one
- Point two

## Linked Notes

None yet.

## Evidence / Sources

- None cited yet

## Open Questions

- None yet"""
        return "## Summary\n\nSynthetic answer.\n\n## Key Points\n\n- Point one"


def build_test_client() -> TestClient:
    source_base_dir = Path(__file__).resolve().parent.parent
    copied_base_dir = source_base_dir / "_test_runtime" / "app_copy"
    rmtree(copied_base_dir, ignore_errors=True)
    copytree(source_base_dir / "app", copied_base_dir / "app")
    copytree(source_base_dir / "data", copied_base_dir / "data")
    return TestClient(create_app(base_dir=copied_base_dir, gemini_client=FakeGeminiClient()))


def test_notes_and_stats_routes() -> None:
    client = build_test_client()
    notes_page = client.get("/")
    stats_page = client.get("/stats")
    row_notes_page = client.get("/notes?view=row")
    searched_notes_page = client.get("/notes?q=provenance")
    dated_notes_page = client.get("/notes?created_since=2026-03-09")
    notes = client.get("/api/notes")
    assert notes_page.status_code == 200
    assert stats_page.status_code == 200
    assert row_notes_page.status_code == 200
    assert searched_notes_page.status_code == 200
    assert dated_notes_page.status_code == 200
    assert "AI Provenance Logging" in searched_notes_page.text
    assert '/notes/note-neuroimaging-in-psychopathy?return_to=/notes%3Fcreated_since%3D2026-03-09' in dated_notes_page.text
    assert '/notes/concept-ai-provenance-logging?return_to=/notes%3Fcreated_since%3D2026-03-09' not in dated_notes_page.text
    assert notes_page.text.count('<option value="Workshop Instructor"></option>') == 1
    assert "note-attachment-indicator" in notes_page.text
    assert notes.status_code == 200
    assert len(notes.json()) >= 7


def test_ai_run_and_save_draft_routes() -> None:
    client = build_test_client()
    ai_response = client.post(
        "/api/ai/run",
        json={
            "task": "question_answering",
            "note_slugs": ["concept-personal-knowledge-base", "concept-bounded-querying"],
            "model": "gemini-2.5-flash-lite",
            "question": "What do these notes say together?",
        },
    )
    assert ai_response.status_code == 200
    draft_response = client.post(
        "/api/notes/save-draft",
        json={
            "title": "Runtime Draft",
            "topics": ["Testing"],
            "people": ["Test User"],
            "sources": ["Instructor Notes"],
            "projects": ["Instructor Demo System"],
            "source_refs": [],
            "tags": ["runtime", "demo"],
            "content": ai_response.json()["output_text"],
        },
    )
    assert draft_response.status_code == 200
    assert draft_response.json()["metadata"]["topics"] == ["Testing"]
    assert draft_response.json()["metadata"]["people"] == ["Test User"]
    assert "runtime" in draft_response.json()["metadata"]["tags"]


def test_save_draft_structures_plain_note_body_with_ai() -> None:
    client = build_test_client()
    response = client.post(
        "/api/notes/save-draft",
        json={
            "title": "Plain Note",
            "topics": [],
            "people": [],
            "sources": [],
            "projects": [],
            "source_refs": [],
            "tags": [],
            "content": "This is a plain paragraph the user typed into New Note.",
        },
    )
    assert response.status_code == 200
    note_response = client.get(f"/api/notes/{response.json()['slug']}")
    assert note_response.status_code == 200
    assert note_response.json()["key_points"] == ["Point one", "Point two"]


def test_save_draft_keeps_existing_structured_key_points() -> None:
    client = build_test_client()
    response = client.post(
        "/api/notes/save-draft",
        json={
            "title": "Structured Note",
            "topics": [],
            "people": [],
            "sources": [],
            "projects": [],
            "source_refs": [],
            "tags": [],
            "content": "## Summary\n\nUser summary.\n\n## Key Points\n\n- User point\n\n## Linked Notes\n\nNone yet.\n\n## Evidence / Sources\n\n- None cited yet\n\n## Open Questions\n\n- None yet",
        },
    )
    assert response.status_code == 200
    note_response = client.get(f"/api/notes/{response.json()['slug']}")
    assert note_response.status_code == 200
    assert note_response.json()["key_points"] == ["User point"]


def test_save_draft_accepts_file_attachments() -> None:
    client = build_test_client()
    response = client.post(
        "/api/notes/save-draft",
        json={
            "title": "Attachment Draft",
            "topics": [],
            "people": [],
            "sources": [],
            "projects": [],
            "source_refs": [],
            "attachments": [],
            "attachment_uploads": [{"name": "reading.pdf", "content_base64": "cGRmLWJ5dGVz"}],
            "tags": [],
            "content": "Attachment-backed note body.",
        },
    )
    assert response.status_code == 200
    attachment_paths = response.json()["metadata"]["attachments"]
    assert len(attachment_paths) == 1
    assert attachment_paths[0].endswith("/reading.pdf")
    detail_response = client.get(f"/notes/{response.json()['slug']}")
    assert 'href="/attachments/note-attachment-draft/reading.pdf"' in detail_response.text
    assert "reading.pdf" in detail_response.text
    attachment_response = client.get("/attachments/note-attachment-draft/reading.pdf")
    assert attachment_response.status_code == 200
    assert attachment_response.content == b"pdf-bytes"


def test_infer_metadata_route() -> None:
    client = build_test_client()
    response = client.post(
        "/api/notes/infer-metadata",
        json={
            "title": "Metadata Test",
            "content": "This note discusses PKB Design Principles and the Instructor Demo System.",
            "source_refs": [],
        },
    )
    assert response.status_code == 200
    assert response.json()["ai_enabled"] is True
    assert "Testing" in response.json()["topics"]


def test_edit_note_routes() -> None:
    client = build_test_client()
    edit_page = client.get("/notes/concept-personal-knowledge-base/edit")
    assert edit_page.status_code == 200
    update_response = client.put(
        "/api/notes/concept-personal-knowledge-base",
        json={
            "title": "Edited PKB Note",
            "topics": ["Edited Topic"],
            "people": ["Workshop Instructor"],
            "sources": ["PKB Design Principles"],
            "projects": ["Instructor Demo System"],
            "source_refs": ["data/sources/source-pkb-design-principles.md"],
            "tags": ["edited"],
            "content": "Edited note body.",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["metadata"]["title"] == "Edited PKB Note"


def test_edit_note_route_merges_existing_and_new_attachments() -> None:
    client = build_test_client()
    created = client.post(
        "/api/notes/save-draft",
        json={
            "title": "Editable Attachments",
            "topics": [],
            "people": [],
            "sources": [],
            "projects": [],
            "source_refs": [],
            "attachments": [],
            "tags": [],
            "content": "Initial content.",
        },
    )
    assert created.status_code == 200
    updated = client.put(
        f"/api/notes/{created.json()['slug']}",
        json={
            "title": "Editable Attachments",
            "topics": [],
            "people": [],
            "sources": [],
            "projects": [],
            "source_refs": [],
            "attachments": created.json()["metadata"]["attachments"],
            "attachment_uploads": [{"name": "appendix.txt", "content_base64": "bm90ZXM="}],
            "tags": [],
            "content": "Updated content.",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["metadata"]["attachments"][0].endswith("/appendix.txt")


def test_delete_note_route_removes_note_attachments_and_history() -> None:
    client = build_test_client()
    created = client.post(
        "/api/notes/save-draft",
        json={
            "title": "Delete Me",
            "topics": [],
            "people": [],
            "sources": [],
            "projects": [],
            "source_refs": [],
            "attachments": [],
            "attachment_uploads": [{"name": "to-delete.txt", "content_base64": "ZGVsZXRl"}],
            "tags": [],
            "content": "Draft content.",
        },
    )
    assert created.status_code == 200
    slug = created.json()["slug"]
    client.get(f"/notes/{slug}")
    deleted = client.delete(f"/api/notes/{slug}")
    assert deleted.status_code == 200
    assert deleted.json() == {"slug": slug, "deleted": True}
    assert client.get(f"/api/notes/{slug}").status_code == 404
    assert client.get(f"/notes/{slug}").status_code == 404
    runtime_data_dir = Path(__file__).resolve().parent.parent / "_test_runtime" / "app_copy" / "data"
    assert not (runtime_data_dir / "attachments" / slug).exists()
    assert not (runtime_data_dir / "history" / slug).exists()


def test_explore_route() -> None:
    client = build_test_client()
    response = client.get("/explore?kind=person&value=Workshop%20Instructor")
    assert response.status_code == 200
    assert "Workshop Instructor" in response.text


def test_note_detail_shows_version_history() -> None:
    client = build_test_client()
    response = client.get("/notes/concept-personal-knowledge-base")
    assert response.status_code == 200
    assert "Version History" in response.text
    assert "Version 1" in response.text
    assert "Connections" in response.text


def test_note_version_detail_shows_change_summary() -> None:
    client = build_test_client()
    update_response = client.put(
        "/api/notes/concept-personal-knowledge-base",
        json={
            "title": "Edited PKB Note",
            "topics": ["Edited Topic"],
            "people": ["Workshop Instructor"],
            "sources": ["PKB Design Principles"],
            "projects": ["Instructor Demo System"],
            "source_refs": ["data/sources/source-pkb-design-principles.md"],
            "tags": ["edited"],
            "content": "## Summary\n\nUpdated summary.\n\n## Key Points\n\n- Revised point\n\n## Linked Notes\n\n- `related_to`: [AI Provenance Logging](./concept-ai-provenance-logging.md)\n\n## Evidence / Sources\n\n- Updated evidence\n\n## Open Questions\n\n- Updated question",
        },
    )
    assert update_response.status_code == 200
    detail_response = client.get("/notes/concept-personal-knowledge-base")
    assert detail_response.status_code == 200
    assert "View version" in detail_response.text
    match = re.search(r'href="(/notes/concept-personal-knowledge-base/history/[^"]+)"[^>]*>View version</a>', detail_response.text)
    assert match is not None
    version_response = client.get(match.group(1))
    assert version_response.status_code == 200
    assert "Change Summary" in version_response.text
    assert any(
        phrase in version_response.text
        for phrase in ("Retitled to Edited PKB Note.", "Summary changed.", "Topics added Edited Topic.")
    )


def test_note_detail_preserves_navigation_context() -> None:
    client = build_test_client()
    response = client.get("/notes/concept-personal-knowledge-base?return_to=%2Fnotes%3Ftopic%3Dknowledge%2520management")
    assert response.status_code == 200
    assert "&larr;" in response.text
    assert response.text.index("Ask a Question") < response.text.index("Related Notes")
    assert 'data-note-slug="concept-personal-knowledge-base"' in response.text
    assert "Related Notes" in response.text


def test_note_detail_question_answering_accepts_single_note() -> None:
    client = build_test_client()
    response = client.post(
        "/api/ai/run",
        json={
            "task": "question_answering",
            "note_slugs": ["concept-personal-knowledge-base"],
            "question": "What is this note about?",
        },
    )
    assert response.status_code == 200
    assert "Synthetic answer." in response.json()["output_text"]


def test_note_detail_shows_ai_structured_sections_for_plain_new_note_text() -> None:
    client = build_test_client()
    draft_response = client.post(
        "/api/notes/save-draft",
        json={
            "title": "Placeholder Draft",
            "topics": [],
            "people": [],
            "sources": [],
            "projects": [],
            "source_refs": [],
            "tags": [],
            "content": "Unstructured draft body.",
        },
    )
    assert draft_response.status_code == 200
    detail_response = client.get(f"/notes/{draft_response.json()['slug']}")
    assert detail_response.status_code == 200
    assert "Key Points" in detail_response.text
    assert "Point one" in detail_response.text
    assert "Evidence / Sources" in detail_response.text
    assert "Needs manual editing" not in detail_response.text


def test_logs_link_to_affected_notes() -> None:
    client = build_test_client()
    client.post(
        "/api/notes/save-draft",
        json={
            "title": "Log Link Draft",
            "topics": [],
            "people": [],
            "sources": [],
            "projects": [],
            "source_refs": ["data/sources/source-pkb-design-principles.md"],
            "tags": [],
            "content": "Draft body for log linkage.",
        },
    )
    logs_page = client.get("/logs")
    assert logs_page.status_code == 200
    assert "Open affected note" in logs_page.text
