# Prompt: Metadata Extraction

Recommended model: `Gemini 2.5 Flash-Lite`

Use this prompt with one note draft or one source at a time.

```text
You are helping build a structured Markdown knowledge base.

Based only on the text below, propose values for the following YAML fields:
- title
- type
- tags
- source_refs
- ai_assisted

Rules:
- Type must be one of: concept, source, person, project.
- Tags should be short and useful.
- Do not fabricate source references. If a source reference is unknown, say "needs-manual-entry".
- Set ai_assisted to true.

Return only a YAML snippet.

Text:
[PASTE NOTE OR SOURCE TEXT HERE]
```
