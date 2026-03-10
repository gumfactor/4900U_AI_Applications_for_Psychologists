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
    searched_notes_page = client.get("/notes?q=provenance")`n    dated_notes_page = client.get("/notes?created_since=2026-03-09")
    notes = client.get("/api/notes")
    assert notes_page.status_code == 200
    assert stats_page.status_code == 200
    assert row_notes_page.status_code == 200
    assert searched_notes_page.status_code == 200`n    assert dated_notes_page.status_code == 200
    assert "AI Provenance Logging" in searched_notes_page.text`n    assert '/notes/note-neuroimaging-in-psychopathy?return_to=/notes%3Fcreated_since%3D2026-03-09' in dated_notes_page.text`n    assert '/notes/concept-ai-provenance-logging?return_to=/notes%3Fcreated_since%3D2026-03-09' not in dated_notes_page.text
    assert notes_page.text.count('<option value="Workshop Instructor"></option>') == 1
    assert notes.status_code == 200
    assert len(notes.json()) >= 7


def test_ai_run_and_save_draft_routes() -> None:
    client = build_test_client()
    ai_response = client.post(
        "/api/ai/run",
        json={"task": "source_summary", "source_slug": "source-pkb-design-principles", "model": "gemini-2.5-flash-lite"},
    )
    assert ai_response.status_code == 200
    draft_response = client.post(
        "/api/notes/save-draft",
        json={
            "title": "Runtime Draft",
            "topics": ["Testing"],
            "people": ["Test User"],
            "sources": ["PKB Design Principles"],
            "projects": ["Instructor Demo System"],
            "source_refs": ["data/sources/source-pkb-design-principles.md"],
            "tags": ["runtime", "demo"],
            "content": ai_response.json()["output_text"],
        },
    )
    assert draft_response.status_code == 200
    assert draft_response.json()["metadata"]["topics"] == ["Testing"]
    assert draft_response.json()["metadata"]["people"] == ["Test User"]
    assert "runtime" in draft_response.json()["metadata"]["tags"]


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
    assert "Related Notes" in response.text


def test_note_detail_replaces_placeholder_scaffolding_with_review_callouts() -> None:
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
    assert "Key Points" not in detail_response.text
    assert "Evidence / Sources" not in detail_response.text
    assert "Open Questions" not in detail_response.text
    assert "Needs manual editing" not in detail_response.text


def test_source_detail_supports_draft_generation() -> None:
    client = build_test_client()
    response = client.get("/sources/source-pkb-design-principles")
    assert response.status_code == 200
    assert "Create Draft From Source" in response.text


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
