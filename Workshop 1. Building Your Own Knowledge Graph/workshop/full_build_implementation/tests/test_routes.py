from pathlib import Path
from shutil import copytree
from shutil import rmtree

from fastapi.testclient import TestClient

from app.main import create_app


class FakeGeminiClient:
    def generate(self, prompt: str, model: str) -> str:
        if "Return the result in YAML only with exactly these keys" in prompt:
            return """note_kind: brainstorming
topics:
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
    searched_notes_page = client.get("/notes?q=provenance")
    notes = client.get("/api/notes")
    assert notes_page.status_code == 200
    assert stats_page.status_code == 200
    assert row_notes_page.status_code == 200
    assert searched_notes_page.status_code == 200
    assert "AI Provenance Logging" in searched_notes_page.text
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
            "note_kind": "synthesis",
            "topics": ["Testing"],
            "people": ["Test User"],
            "sources": ["PKB Design Principles"],
            "projects": ["Instructor Demo System"],
            "source_refs": ["data/sources/source-pkb-design-principles.md"],
            "tags": ["runtime", "demo"],
            "content": ai_response.json()["output_text"],
            "ai_assisted": True,
        },
    )
    assert draft_response.status_code == 200
    assert draft_response.json()["metadata"]["status"] == "ai-drafted"
    assert draft_response.json()["metadata"]["note_kind"] == "synthesis"
    assert draft_response.json()["metadata"]["topics"] == ["Testing"]
    assert draft_response.json()["metadata"]["people"] == ["Test User"]
    assert "runtime" in draft_response.json()["metadata"]["tags"]


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
    assert response.json()["note_kind"] == "brainstorming"
    assert "Testing" in response.json()["topics"]


def test_edit_note_routes() -> None:
    client = build_test_client()
    edit_page = client.get("/notes/concept-personal-knowledge-base/edit")
    assert edit_page.status_code == 200
    update_response = client.put(
        "/api/notes/concept-personal-knowledge-base",
        json={
            "title": "Edited PKB Note",
            "note_kind": "reflection",
            "topics": ["Edited Topic"],
            "people": ["Workshop Instructor"],
            "sources": ["PKB Design Principles"],
            "projects": ["Instructor Demo System"],
            "source_refs": ["data/sources/source-pkb-design-principles.md"],
            "tags": ["edited"],
            "content": "Edited note body.",
            "status": "reviewed",
            "ai_assisted": True,
            "human_reviewed": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["metadata"]["title"] == "Edited PKB Note"
    assert update_response.json()["metadata"]["status"] == "reviewed"


def test_explore_route() -> None:
    client = build_test_client()
    response = client.get("/explore?kind=person&value=Workshop%20Instructor")
    assert response.status_code == 200
    assert "Workshop Instructor" in response.text


def test_note_detail_shows_provenance() -> None:
    client = build_test_client()
    response = client.get("/notes/concept-personal-knowledge-base")
    assert response.status_code == 200
    assert "Provenance" in response.text
    assert "Related AI logs" in response.text


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
            "note_kind": "synthesis",
            "topics": [],
            "people": [],
            "sources": [],
            "projects": [],
            "source_refs": ["data/sources/source-pkb-design-principles.md"],
            "tags": [],
            "content": "Draft body for log linkage.",
            "ai_assisted": True,
        },
    )
    logs_page = client.get("/logs")
    assert logs_page.status_code == 200
    assert "Open affected note" in logs_page.text
