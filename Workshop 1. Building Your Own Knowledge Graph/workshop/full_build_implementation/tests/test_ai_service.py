from pathlib import Path
from shutil import rmtree

from app.models import AiTaskRequest
from app.services.ai_service import AiService
from app.services.log_service import LogService
from app.services.note_repository import NoteRepository
from app.services.prompt_repository import PromptRepository
from app.services.source_repository import SourceRepository


class FakeGeminiClient:
    def __init__(self) -> None:
        self.last_prompt = ""

    def generate(self, prompt: str, model: str) -> str:
        self.last_prompt = prompt
        return "## Summary\n\nMocked output.\n\n## Key Points\n\n- Mocked"


def build_logs_dir(base_dir: Path, name: str) -> Path:
    logs_dir = base_dir / "_test_runtime" / name
    rmtree(logs_dir, ignore_errors=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def test_ai_service_runs_source_summary() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    service = AiService(
        NoteRepository(base_dir / "data" / "notes"),
        SourceRepository(base_dir / "data" / "sources"),
        PromptRepository(base_dir / "data" / "prompts"),
        LogService(build_logs_dir(base_dir, "ai-service-summary")),
        FakeGeminiClient(),
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
    )
    result = service.run_task(
        AiTaskRequest(task="source_summary", source_slug="source-pkb-design-principles", model="gemini-2.5-flash-lite")
    )
    assert result.task == "source_summary"
    assert "Source text:" in service.gemini_client.last_prompt
    assert result.log_path is not None


def test_ai_service_question_answering_requires_question() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    service = AiService(
        NoteRepository(base_dir / "data" / "notes"),
        SourceRepository(base_dir / "data" / "sources"),
        PromptRepository(base_dir / "data" / "prompts"),
        LogService(build_logs_dir(base_dir, "ai-service-question")),
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
