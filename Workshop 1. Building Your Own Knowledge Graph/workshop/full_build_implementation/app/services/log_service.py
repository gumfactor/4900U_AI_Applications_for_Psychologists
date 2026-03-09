from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.models import AiLogEntry
from app.services.markdown_utils import note_title_from_path, slugify


class LogService:
    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = logs_dir

    def list_logs(self) -> list[AiLogEntry]:
        entries: list[AiLogEntry] = []
        for path in sorted(self.logs_dir.glob("*.md"), reverse=True):
            entries.append(self._parse_entry(path, path.read_text(encoding="utf-8")))
        return entries

    def get_log(self, slug: str) -> AiLogEntry:
        for entry in self.list_logs():
            if entry.slug == slug:
                return entry
        raise FileNotFoundError(f"Log entry not found: {slug}")

    def write_log(
        self,
        task: str,
        prompt_slug: str,
        model: str,
        input_files: list[str],
        output_target: str,
        review_outcome: str = "pending-review",
        notes: str = "",
    ) -> str:
        timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        slug = slugify(f"{timestamp}-{task}")
        content = "\n".join(
            [
                "# AI Interaction Log",
                "",
                f"- `timestamp`: {timestamp}",
                f"- `task`: {task}",
                f"- `prompt_slug`: {prompt_slug}",
                f"- `model`: {model}",
                f"- `input_files`: {', '.join(input_files) if input_files else 'none'}",
                f"- `output_target`: {output_target}",
                f"- `review_outcome`: {review_outcome}",
                f"- `notes`: {notes or 'n/a'}",
                "",
            ]
        )
        path = self.logs_dir / f"{slug}.md"
        path.write_text(content, encoding="utf-8")
        return str(path.relative_to(self.logs_dir.parent.parent).as_posix())

    def _parse_entry(self, path: Path, content: str) -> AiLogEntry:
        values: dict[str, str] = {}
        for line in content.splitlines():
            if line.startswith("- `") and "`:" in line:
                key_part, value = line[2:].split("`:", 1)
                values[key_part.strip("`")] = value.strip()
        input_files = [
            item.strip()
            for item in values.get("input_files", "").split(",")
            if item.strip() and item.strip() != "none"
        ]
        return AiLogEntry(
            slug=path.stem,
            timestamp=values.get("timestamp", ""),
            task=values.get("task", note_title_from_path(path)),
            prompt_slug=values.get("prompt_slug", ""),
            model=values.get("model", ""),
            input_files=input_files,
            output_target=values.get("output_target", ""),
            review_outcome=values.get("review_outcome", ""),
            notes=values.get("notes", ""),
            raw_content=content,
        )
