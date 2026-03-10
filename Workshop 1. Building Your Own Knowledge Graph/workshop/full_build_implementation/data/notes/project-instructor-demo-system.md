---
id: project-instructor-demo-system
title: Instructor Demo System
topics:
  - workshop infrastructure
  - personal knowledge bases
people:
  - Workshop Instructor
sources:
  - PKB Design Principles
  - AI Review Discipline
  - Bounded Querying
projects:
  - Instructor Demo System
tags:
  - Personal Knowledge Base
  - AI Provenance Logging
  - Bounded Querying
  - demo
  - fastapi
  - workshop
source_refs:
  - data/sources/source-pkb-design-principles.md
  - data/sources/source-ai-review-discipline.md
  - data/sources/source-bounded-querying.md
created: 2026-03-08
updated: 2026-03-08
---

# Instructor Demo System

## Summary

The instructor demo system is a working reference implementation that shows how Markdown notes, YAML metadata, AI tasks, logs, and review workflows can be combined into a functioning personal knowledge base.

## Key Points

- The app keeps notes on disk as real Markdown files.
- Gemini is used only for bounded, inspectable tasks.
- Logs make AI use reproducible and teachable.

## Linked Notes

- `applies_to`: [Personal Knowledge Base](./concept-personal-knowledge-base.md)
- `applies_to`: [Structured Markdown Notes](./concept-structured-markdown-notes.md)
- `applies_to`: [AI Provenance Logging](./concept-ai-provenance-logging.md)
- `applies_to`: [Bounded Querying](./concept-bounded-querying.md)

## Evidence / Sources

- source-pkb-design-principles.md
- source-ai-review-discipline.md
- source-bounded-querying.md

## Open Questions

- Which optional enhancements belong in a later iteration rather than the main classroom demo?

