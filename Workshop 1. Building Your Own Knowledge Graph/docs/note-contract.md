# Canonical Note Contract

Each note is one Markdown file with YAML frontmatter and a structured body.

## Required Frontmatter

```yaml
id: unique-note-id
title: Human readable title
type: concept | source | person | project
status: captured | ai-drafted | reviewed | final
tags:
  - example-tag
source_refs:
  - relative/path/or/reference
created: YYYY-MM-DD
updated: YYYY-MM-DD
ai_assisted: true | false
human_reviewed: true | false
```

## Body Sections

Each note should contain:

1. `Summary`
2. `Key Points`
3. `Linked Notes`
4. `Evidence / Sources`
5. `Open Questions`

## Linking Rules

Use standard Markdown links so the graph remains portable.

Examples:

- `[Knowledge Graph Basics](./concept-knowledge-graph-basics.md)`
- `[AI Workflow Demo](./project-ai-workflow-demo.md)`

Use relationship labels in prose or bullets inside `Linked Notes`.

Example:

```md
- `related_to`: [Knowledge Graph Basics](./concept-knowledge-graph-basics.md)
- `supports`: [Source on Structured Notes](./source-structured-notes.md)
```

## Filename Rules

Use one of these conventions:

- `type-short-title.md` for canonical notes
- `YYYYMMDD-short-title.md` for capture-oriented notes

Keep names stable after creation.
