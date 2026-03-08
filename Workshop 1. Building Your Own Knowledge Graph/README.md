# AI-Assisted Personal Knowledge Base Workshop

This starter repository is the hands-on scaffold for building a personal knowledge base in VS Code with:

- Markdown notes
- YAML frontmatter
- Git/GitHub
- Gemini 2.5 Flash-Lite for default AI tasks
- Gemini 2.5 Flash for optional higher-quality synthesis

The repository is designed so the knowledge base works without AI. AI is an assistive layer for drafting, extracting, linking, and answering questions over a bounded set of notes.

## Learning Goals

By the end of the workshop, students should be able to:

1. Create notes using a consistent metadata contract.
2. Link notes so the collection behaves like a small knowledge graph.
3. Use AI to draft or enrich notes without treating AI output as final truth.
4. Track changes with Git and keep AI work reproducible with logs.

## Repository Layout

```text
.
|-- .env.example
|-- .gitignore
|-- README.md
|-- addons/
|-- docs/
|-- logs/
|-- notes/
|-- prompts/
|-- sources/
`-- templates/
```

## Mandatory Workflow

### 1. Start with a source

Place a source document, excerpt, or summary in [`sources/`](./sources/).

### 2. Draft a note

Copy the most relevant template from [`templates/`](./templates/) into [`notes/`](./notes/) and fill in the required YAML frontmatter.

Allowed note types:

- `concept`
- `source`
- `person`
- `project`

Allowed relationship labels:

- `related_to`
- `supports`
- `contradicts`
- `applies_to`
- `mentions`

### 3. Use AI on bounded inputs

Use a prompt from [`prompts/`](./prompts/) with one source or a small bundle of notes. Default model: `Gemini 2.5 Flash-Lite`.

Keep prompts bounded:

- one source at a time for summaries
- one note at a time for metadata extraction
- two to five notes at a time for link suggestions or Q&A

Do not ask the model to reason over the entire repository during the mandatory portion.

### 4. Review before finalizing

Every AI-assisted note must move through this status lifecycle:

- `captured`
- `ai-drafted`
- `reviewed`
- `final`

Markdown notes remain the source of truth. AI output is a draft unless a human updates the note and marks it reviewed.

### 5. Log the AI step

Every AI interaction that changes a note should be logged in [`logs/`](./logs/) using the log template.

Minimum log data:

- date/time
- prompt template used
- input file(s)
- model
- output location
- review outcome

## Recommended Commit Milestones

Use Git from the start. Keep commits short and meaningful.

Suggested milestone commits:

1. `Initial scaffold`
2. `Add starter templates and note contract`
3. `Add first notes from source material`
4. `Add AI-assisted enrichment`
5. `Review notes and finalize links`

## Retrieval Paths

Students should be able to retrieve information in three ways:

1. VS Code search over filenames, text, and tags.
2. Manual navigation using Markdown links.
3. AI question answering over a supplied subset of notes.

## AI Model Guidance

### Default model

Use `Gemini 2.5 Flash-Lite` for:

- source-to-note summaries
- metadata extraction
- tag suggestions
- related note suggestions
- limited Q&A over a small note bundle

### Optional upgrade

Use `Gemini 2.5 Flash` for:

- higher-quality cross-note synthesis
- comparison across several notes
- literature-style summaries
- more nuanced question answering

## Setup Notes

1. Open this folder in VS Code.
2. Initialize a Git repository if one does not already exist.
3. Copy `.env.example` to a local environment file or set variables in your shell.
4. Do not commit API keys.
5. Use the example notes as reference, then create your own notes from the workshop topic.

## What Success Looks Like

By the end of the workshop, a student repository should contain:

- at least 5 notes using the canonical note contract
- links between notes
- at least 1 AI-assisted note
- at least 1 reviewed note that was AI-assisted
- at least 1 AI interaction log
- a clear Git history with milestone commits

## Optional Addons

Optional addons live in [`addons/`](./addons/):

- better synthesis with `Gemini 2.5 Flash`
- prompt-to-script automation
- structured export to `JSON` or `CSV`
- lightweight query tooling
- retrieval augmentation
