from app.services.markdown_utils import build_note_markdown, extract_links, parse_frontmatter, split_sections


def test_parse_frontmatter_and_sections() -> None:
    markdown = """---
id: concept-example
title: Example
type: concept
status: captured
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
        note_type="concept",
        source_refs=["data/sources/example.md"],
        tags=["demo"],
        content="This is generated text.",
        ai_assisted=True,
    )
    assert filename == "concept-demo-note.md"
    assert "## Summary" in markdown
    assert "## Open Questions" in markdown
