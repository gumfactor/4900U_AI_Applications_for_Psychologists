from __future__ import annotations

import re

import yaml

from app.models import AiTaskRequest, AiTaskResult, Note
from app.services.gemini_client import GeminiClient
from app.services.note_repository import NoteRepository
from app.services.prompt_repository import PromptRepository


class AiService:
    TASK_PROMPTS = {
        "question_answering": "04-question-answering",
    }
    METADATA_PROMPT = "02-metadata-extraction"
    NOTE_BODY_PROMPT = "05-note-body-structuring"

    def __init__(
        self,
        note_repository: NoteRepository,
        prompt_repository: PromptRepository,
        gemini_client: GeminiClient | None,
        default_model: str,
        high_quality_model: str,
    ) -> None:
        self.note_repository = note_repository
        self.prompt_repository = prompt_repository
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

        if request.task == "question_answering":
            if not request.question:
                raise ValueError("question is required for question_answering.")
            notes = self._load_selected_notes(request.note_slugs, minimum=1)
            input_paths.extend(note.path for note in notes)
            blocks.extend([f"", f"Question:\n{request.question}", "", "Notes:"])
            blocks.extend(self._render_note_context(note) for note in notes)
        else:
            raise ValueError(f"Unsupported task: {request.task}")

        prompt_text = "\n\n".join(blocks).strip()
        output_text = self.gemini_client.generate(prompt_text, model)
        return AiTaskResult(
            task=request.task,
            model=model,
            prompt_slug=prompt_slug,
            prompt_text=prompt_text,
            output_text=output_text,
            input_paths=input_paths,
        )

    def infer_note_metadata(
        self,
        title: str,
        content: str,
        source_refs: list[str] | None = None,
        model: str | None = None,
    ) -> dict[str, object]:
        if not self.gemini_client:
            return {
                "topics": [],
                "people": [],
                "sources": [],
                "projects": [],
                "tags": [],
                "source_refs": source_refs or [],
                "model": None,
                "prompt_slug": self.METADATA_PROMPT,
                "raw_output": "",
                "input_paths": source_refs or [],
            }

        prompt_slug = self.METADATA_PROMPT
        prompt_template = self.prompt_repository.get_prompt(prompt_slug)
        selected_model = model or self.default_model
        prompt_text = "\n\n".join(
            [
                prompt_template.content.strip(),
                "",
                f"Title: {title.strip()}",
                "",
                "Note body:",
                content.strip(),
            ]
        ).strip()
        raw_output = self.gemini_client.generate(prompt_text, selected_model)
        parsed = self._parse_metadata_yaml(raw_output)
        parsed["model"] = selected_model
        parsed["prompt_slug"] = prompt_slug
        parsed["raw_output"] = raw_output
        parsed["input_paths"] = source_refs or []
        return parsed

    def structure_note_body(
        self,
        title: str,
        content: str,
        model: str | None = None,
    ) -> dict[str, object]:
        if not self.gemini_client:
            return {
                "content": content,
                "model": None,
                "prompt_slug": self.NOTE_BODY_PROMPT,
                "raw_output": "",
                "input_paths": [],
            }

        prompt_template = self.prompt_repository.get_prompt(self.NOTE_BODY_PROMPT)
        selected_model = model or self.default_model
        prompt_text = "\n\n".join(
            [
                prompt_template.content.strip(),
                "",
                f"Title: {title.strip()}",
                "",
                "User note body:",
                content.strip(),
            ]
        ).strip()
        raw_output = self.gemini_client.generate(prompt_text, selected_model).strip()
        return {
            "content": raw_output or content,
            "model": selected_model,
            "prompt_slug": self.NOTE_BODY_PROMPT,
            "raw_output": raw_output,
            "input_paths": [],
        }

    def _load_selected_notes(self, slugs: list[str], minimum: int = 2, maximum: int = 5) -> list[Note]:
        if len(slugs) < minimum or len(slugs) > maximum:
            if minimum == maximum:
                raise ValueError(f"Select exactly {minimum} notes for this task.")
            raise ValueError(f"Select between {minimum} and {maximum} notes for this task.")
        return [self.note_repository.get_note(slug) for slug in slugs]

    @staticmethod
    def _render_note_context(note: Note) -> str:
        return "\n".join(
            list(
                filter(
                    None,
                    [
                        f"Title: {note.metadata.title}",
                        f"Topics: {', '.join(note.metadata.topics)}",
                        f"Tags: {', '.join(note.metadata.tags)}",
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

    @staticmethod
    def _parse_metadata_yaml(raw_output: str) -> dict[str, object]:
        cleaned = raw_output.strip()
        fenced_match = re.search(r"```(?:yaml)?\s*(.*?)```", cleaned, re.DOTALL)
        if fenced_match:
            cleaned = fenced_match.group(1).strip()
        try:
            parsed = yaml.safe_load(cleaned) or {}
        except yaml.YAMLError:
            parsed = AiService._fallback_metadata_mapping(cleaned)
        if not isinstance(parsed, dict):
            parsed = AiService._fallback_metadata_mapping(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("Metadata extraction did not return a usable metadata mapping.")
        return {
            "topics": AiService._normalize_list(parsed.get("topics")),
            "people": AiService._normalize_list(parsed.get("people")),
            "sources": AiService._normalize_list(parsed.get("sources")),
            "projects": AiService._normalize_list(parsed.get("projects")),
            "tags": AiService._normalize_list(parsed.get("tags")),
            "source_refs": AiService._normalize_list(parsed.get("source_refs")),
        }

    @staticmethod
    def _normalize_list(value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            values = [value]
        elif isinstance(value, list):
            values = [str(item).strip() for item in value]
        else:
            values = [str(value).strip()]
        seen: set[str] = set()
        normalized: list[str] = []
        for item in values:
            if not item:
                continue
            if item not in seen:
                seen.add(item)
                normalized.append(item)
        return normalized

    @staticmethod
    def _normalize_scalar(value: object) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @staticmethod
    def _fallback_metadata_mapping(cleaned: str) -> dict[str, object]:
        allowed_keys = {"topics", "people", "sources", "projects", "tags", "source_refs"}
        parsed: dict[str, object] = {}
        current_list_key: str | None = None
        for line in cleaned.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if ":" in stripped and not stripped.startswith("- "):
                key, raw_value = stripped.split(":", 1)
                key = key.strip()
                if key not in allowed_keys:
                    current_list_key = None
                    continue
                value = raw_value.strip()
                if value in {"", "null", "None"}:
                    parsed[key] = []
                    current_list_key = key
                else:
                    parsed[key] = value
                    current_list_key = None
                continue
            if stripped.startswith("- ") and current_list_key:
                parsed.setdefault(current_list_key, [])
                if isinstance(parsed[current_list_key], list):
                    parsed[current_list_key].append(stripped[2:].strip())
        return parsed
