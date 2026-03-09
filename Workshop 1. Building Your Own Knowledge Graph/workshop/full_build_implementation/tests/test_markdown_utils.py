from app.services.markdown_utils import build_note_markdown, extract_links, parse_frontmatter, split_sections, validate_metadata


def test_parse_frontmatter_and_sections() -> None:
    markdown = """---
id: concept-example
title: Example
status: captured
topics:
  - testing
concepts:
  - Example
people: []
sources: []
projects: []
tags:
  - demo
source_refs:
  - data/source.md
created: 2026-03-08
updated: 2026-03-08
ai_assisted: false
human_reviewed: false
---

# Example

## Summary

Summary text.

## Linked Notes

- `related_to`: [Other](./other.md)
"""
    frontmatter, body = parse_frontmatter(markdown)
    sections = split_sections(body)
    assert frontmatter["title"] == "Example"
    assert sections["Summary"] == "Summary text."
    assert extract_links(sections["Linked Notes"])[0].title == "Other"


def test_build_note_markdown_includes_required_sections() -> None:
    filename, markdown = build_note_markdown(
        title="Demo Note",
        note_kind="synthesis",
        topics=["Knowledge Work"],
        concepts=["Demo Note"],
        people=["Ada Lovelace"],
        sources=["Demo Source"],
        projects=["PKB Demo"],
        source_refs=["data/sources/example.md"],
        tags=["demo"],
        content="This is generated text.",
        ai_assisted=True,
    )
    assert filename == "note-demo-note.md"
    assert "note_kind: synthesis" in markdown
    assert "- Knowledge Work" in markdown
    assert "## Summary" in markdown
    assert "## Open Questions" in markdown


def test_validate_metadata_supports_legacy_type_and_topic() -> None:
    metadata = validate_metadata(
        {
            "id": "legacy-example",
            "title": "Legacy Concept",
            "type": "concept",
            "topic": "Legacy Topic",
            "status": "captured",
            "tags": ["legacy"],
            "source_refs": [],
            "created": "2026-03-08",
            "updated": "2026-03-08",
            "ai_assisted": False,
            "human_reviewed": False,
        }
    )
    assert metadata.note_kind is None
    assert metadata.topics == ["Legacy Topic"]
    assert metadata.concepts == ["Legacy Concept"]
