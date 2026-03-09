from pathlib import Path
from shutil import copytree
from shutil import rmtree

from fastapi.testclient import TestClient

from app.main import create_app


class FakeGeminiClient:
    def generate(self, prompt: str, model: str) -> str:
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
    notes = client.get("/api/notes")
    assert notes_page.status_code == 200
    assert stats_page.status_code == 200
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
