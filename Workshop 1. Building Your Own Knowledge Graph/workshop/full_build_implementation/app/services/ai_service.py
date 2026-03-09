from __future__ import annotations

from app.models import AiTaskRequest, AiTaskResult, Note
from app.services.gemini_client import GeminiClient
from app.services.log_service import LogService
from app.services.note_repository import NoteRepository
from app.services.prompt_repository import PromptRepository
from app.services.source_repository import SourceRepository


class AiService:
    TASK_PROMPTS = {
        "source_summary": "01-source-to-note-summary",
        "metadata_extraction": "02-metadata-extraction",
        "related_note_suggestion": "03-related-note-suggestion",
        "question_answering": "04-question-answering",
    }

    def __init__(
        self,
        note_repository: NoteRepository,
        source_repository: SourceRepository,
        prompt_repository: PromptRepository,
        log_service: LogService,
        gemini_client: GeminiClient | None,
        default_model: str,
        high_quality_model: str,
    ) -> None:
        self.note_repository = note_repository
        self.source_repository = source_repository
        self.prompt_repository = prompt_repository
        self.log_service = log_service
        self.gemini_client = gemini_client
        self.default_model = default_model
        self.high_quality_model = high_quality_model

    def run_task(self, request: AiTaskRequest) -> AiTaskResult:
        if not self.gemini_client:
            raise RuntimeError("AI features are disabled because no Gemini API key is configured.")

        prompt_slug = request.prompt_slug or self.TASK_PROMPTS[request.task]
        prompt_template = self.prompt_repository.get_prompt(prompt_slug)
        model = request.model or self.default_model
        input_paths: list[str] = []
        blocks: list[str] = [prompt_template.content.strip()]

        if request.task == "source_summary":
            if not request.source_slug:
                raise ValueError("source_slug is required for source_summary.")
            source = self.source_repository.get_source(request.source_slug)
            input_paths.append(source.path)
            blocks.extend(["", "Source text:", source.content])
        elif request.task == "metadata_extraction":
            if request.source_slug:
                source = self.source_repository.get_source(request.source_slug)
                input_paths.append(source.path)
                blocks.extend(["", "Text:", source.content])
            elif request.note_slugs:
                note = self.note_repository.get_note(request.note_slugs[0])
                input_paths.append(note.path)
                blocks.extend(["", "Text:", note.raw_body])
            else:
                raise ValueError("metadata_extraction requires a source_slug or one note slug.")
        elif request.task == "related_note_suggestion":
            notes = self._load_selected_notes(request.note_slugs)
            input_paths.extend(note.path for note in notes)
            blocks.extend(["", "Notes:"])
            blocks.extend(self._render_note_context(note) for note in notes)
        elif request.task == "question_answering":
            if not request.question:
                raise ValueError("question is required for question_answering.")
            notes = self._load_selected_notes(request.note_slugs)
            input_paths.extend(note.path for note in notes)
            blocks.extend([f"", f"Question:\n{request.question}", "", "Notes:"])
            blocks.extend(self._render_note_context(note) for note in notes)
        else:
            raise ValueError(f"Unsupported task: {request.task}")

        prompt_text = "\n\n".join(blocks).strip()
        output_text = self.gemini_client.generate(prompt_text, model)
        log_path = self.log_service.write_log(
            task=request.task,
            prompt_slug=prompt_slug,
            model=model,
            input_files=input_paths,
            output_target="ui-preview",
            notes="Generated through instructor demo UI.",
        )
        return AiTaskResult(
            task=request.task,
            model=model,
            prompt_slug=prompt_slug,
            prompt_text=prompt_text,
            output_text=output_text,
            input_paths=input_paths,
            log_path=log_path,
        )

    def _load_selected_notes(self, slugs: list[str]) -> list[Note]:
        if len(slugs) < 2 or len(slugs) > 5:
            raise ValueError("Select between 2 and 5 notes for this task.")
        return [self.note_repository.get_note(slug) for slug in slugs]

    @staticmethod
    def _render_note_context(note: Note) -> str:
        return "\n".join(
            list(
                filter(
                    None,
                    [
                        f"Title: {note.metadata.title}",
                        f"Note Kind: {note.metadata.note_kind}" if note.metadata.note_kind else "",
                        f"Status: {note.metadata.status}",
                        f"Topics: {', '.join(note.metadata.topics)}",
                        f"Concepts: {', '.join(note.metadata.concepts)}",
                        f"People: {', '.join(note.metadata.people)}",
                        f"Sources: {', '.join(note.metadata.sources)}",
                        f"Projects: {', '.join(note.metadata.projects)}",
                        "Summary:",
                        note.summary,
                        "Key Points:",
                        "\n".join(f"- {point}" for point in note.key_points),
                    ],
                )
            )
        ).strip()
