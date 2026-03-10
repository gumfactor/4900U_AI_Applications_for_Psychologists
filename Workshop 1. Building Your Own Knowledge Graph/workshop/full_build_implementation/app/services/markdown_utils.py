from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from app.models import NoteLink, NoteMetadata

LINK_PATTERN = re.compile(r"-\s*`(?P<relationship>[^`]+)`:\s*\[(?P<title>[^\]]+)\]\((?P<target>[^)]+)\)")
SECTION_PATTERN = re.compile(r"^## (?P<name>.+)$", re.MULTILINE)

def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "untitled-note"


def today_iso() -> str:
    return date.today().isoformat()


def parse_frontmatter(markdown_text: str) -> tuple[dict[str, Any], str]:
    markdown_text = markdown_text.lstrip("\ufeff")
    if not markdown_text.startswith("---\n"):
        raise ValueError("Markdown file is missing YAML frontmatter.")
    try:
        _, frontmatter_text, body = markdown_text.split("---\n", 2)
    except ValueError as exc:
        raise ValueError("Markdown frontmatter is not properly delimited.") from exc
    data = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must parse to a mapping.")
    return data, body.strip()


def dump_frontmatter(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False).strip()


def split_sections(body: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(body))
    if not matches:
        return {}
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group("name").strip()] = body[start:end].strip()
    return sections


def bullet_lines(section_text: str) -> list[str]:
    items: list[str] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def extract_links(linked_notes_markdown: str) -> list[NoteLink]:
    links: list[NoteLink] = []
    for match in LINK_PATTERN.finditer(linked_notes_markdown):
        links.append(
            NoteLink(
                relationship=match.group("relationship"),
                title=match.group("title"),
                target=match.group("target"),
            )
        )
    return links


def validate_metadata(frontmatter: dict[str, Any]) -> NoteMetadata:
    normalized = dict(frontmatter)
    normalized.pop("status", None)
    normalized.pop("ai_assisted", None)
    normalized.pop("human_reviewed", None)
    for key in ("created", "updated"):
        if key in normalized and normalized[key] is not None:
            normalized[key] = str(normalized[key])
    legacy_type = normalized.pop("type", None)
    legacy_topic = normalized.pop("topic", None)
    normalized.setdefault("topics", [])
    normalized.setdefault("people", [])
    normalized.setdefault("sources", [])
    normalized.setdefault("projects", [])
    normalized.setdefault("tags", [])
    normalized.setdefault("source_refs", [])
    if legacy_topic:
        normalized["topics"] = [str(legacy_topic), *normalized["topics"]]
    normalized.pop("note_kind", None)
    title = str(normalized.get("title", "")).strip()
    legacy_concepts = normalized.pop("concepts", [])
    if legacy_concepts:
        normalized["tags"] = [*legacy_concepts, *normalized["tags"]]
    if legacy_type == "concept" and title and title not in normalized["tags"]:
        normalized["tags"] = [title, *normalized["tags"]]
    if legacy_type == "person" and title and not normalized["people"]:
        normalized["people"] = [title]
    if legacy_type == "project" and title and not normalized["projects"]:
        normalized["projects"] = [title]
    if legacy_type == "source" and title and not normalized["sources"]:
        normalized["sources"] = [title]
    return NoteMetadata(**normalized)


def ensure_note_body_structure(content: str) -> str:
    required = [
        "## Summary",
        "## Key Points",
        "## Linked Notes",
        "## Evidence / Sources",
        "## Open Questions",
    ]
    if all(heading in content for heading in required):
        return content.strip()
    cleaned = content.strip()
    return "\n".join(
        [
            "## Summary",
            "",
            cleaned or "Draft content pending review.",
            "",
            "## Key Points",
            "",
            "- Needs manual editing",
            "",
            "## Linked Notes",
            "",
            "- `related_to`: [Add a linked note](./replace-linked-note.md)",
            "",
            "## Evidence / Sources",
            "",
            "- Add supporting source",
            "",
            "## Open Questions",
            "",
            "- What still needs to be checked?",
        ]
    ).strip()


def build_note_markdown(
    title: str,
    topics: list[str],
    people: list[str],
    sources: list[str],
    projects: list[str],
    source_refs: list[str],
    tags: list[str],
    content: str,
) -> tuple[str, str]:
    slug = slugify(title)
    metadata = {
        "id": f"note-{slug}",
        "title": title,
        "topics": topics,
        "people": people,
        "sources": sources,
        "projects": projects,
        "tags": tags,
        "source_refs": source_refs,
        "created": today_iso(),
        "updated": today_iso(),
    }
    markdown = build_note_document(title, metadata, content)
    return f"note-{slug}.md", markdown


def build_note_document(title: str, metadata: dict[str, Any], content: str) -> str:
    note_body = ensure_note_body_structure(content)
    return f"---\n{dump_frontmatter(metadata)}\n---\n\n# {title}\n\n{note_body}\n"


def note_title_from_path(path: Path) -> str:
    return path.stem.replace("-", " ").title()
