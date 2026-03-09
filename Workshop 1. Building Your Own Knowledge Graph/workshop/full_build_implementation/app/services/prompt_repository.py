from __future__ import annotations

from pathlib import Path

from app.models import PromptTemplate
from app.services.markdown_utils import note_title_from_path


class PromptRepository:
    def __init__(self, prompts_dir: Path) -> None:
        self.prompts_dir = prompts_dir

    def list_prompts(self) -> list[PromptTemplate]:
        return [
            PromptTemplate(
                slug=path.stem,
                title=note_title_from_path(path),
                path=str(path.relative_to(self.prompts_dir.parent.parent).as_posix()),
                content=path.read_text(encoding="utf-8"),
            )
            for path in sorted(self.prompts_dir.glob("*.md"))
        ]

    def get_prompt(self, slug: str) -> PromptTemplate:
        for prompt in self.list_prompts():
            if prompt.slug == slug:
                return prompt
        raise FileNotFoundError(f"Prompt not found: {slug}")
