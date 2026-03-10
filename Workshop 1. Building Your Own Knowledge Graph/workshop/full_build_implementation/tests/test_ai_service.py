from pathlib import Path

from app.models import AiTaskRequest
from app.services.ai_service import AiService
from app.services.note_repository import NoteRepository
from app.services.prompt_repository import PromptRepository


class FakeGeminiClient:
    def __init__(self) -> None:
        self.last_prompt = ""

    def generate(self, prompt: str, model: str) -> str:
        self.last_prompt = prompt
        if "User note body:" in prompt:
            return """## Summary

Mocked structured summary.

## Key Points

- Structured point one
- Structured point two

## Linked Notes

None yet.

## Evidence / Sources

- None cited yet

## Open Questions

- None yet"""
        return "## Summary\n\nMocked output.\n\n## Key Points\n\n- Mocked"

def test_ai_service_runs_question_answering_for_selected_notes() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    fake_client = FakeGeminiClient()
    service = AiService(
        NoteRepository(base_dir / "data" / "notes"),
        PromptRepository(base_dir / "data" / "prompts"),
        fake_client,
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
    )
    result = service.run_task(
        AiTaskRequest(
            task="question_answering",
            note_slugs=["concept-personal-knowledge-base", "concept-bounded-querying"],
            question="How do these notes connect?",
            model="gemini-2.5-flash-lite",
        )
    )
    assert result.task == "question_answering"
    assert "Question:\nHow do these notes connect?" in fake_client.last_prompt


def test_ai_service_question_answering_requires_question() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    service = AiService(
        NoteRepository(base_dir / "data" / "notes"),
        PromptRepository(base_dir / "data" / "prompts"),
        FakeGeminiClient(),
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
    )
    try:
        service.run_task(
            AiTaskRequest(task="question_answering", note_slugs=["concept-personal-knowledge-base", "concept-bounded-querying"])
        )
    except ValueError as exc:
        assert "question" in str(exc)
    else:
        raise AssertionError("Expected question_answering to require a question.")


def test_ai_service_structures_note_body() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    fake_client = FakeGeminiClient()
    service = AiService(
        NoteRepository(base_dir / "data" / "notes"),
        PromptRepository(base_dir / "data" / "prompts"),
        fake_client,
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
    )
    result = service.structure_note_body("My note", "A plain paragraph from the user.")
    assert "User note body:" in fake_client.last_prompt
    assert "## Key Points" in str(result["content"])
    assert result["prompt_slug"] == "05-note-body-structuring"
