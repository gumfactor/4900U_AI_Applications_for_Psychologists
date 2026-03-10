# Workshop Build Plan: AI-Assisted Personal Knowledge Base in VS Code

## Summary
Build the workshop around a file-first personal knowledge base that is fully usable without AI and enhanced by Gemini when available. The mandatory path uses `VS Code`, `Markdown`, `YAML frontmatter`, and `Git/GitHub` to create a durable note system with consistent templates, links, provenance, and retrieval. AI is introduced as a structured assistive layer using `Gemini 2.5 Flash-Lite` for note drafting, metadata extraction, link suggestion, and limited Q&A. `Gemini 2.5 Flash` is positioned as an optional quality upgrade for synthesis-heavy tasks.

The workshop should be taught as a staged build, where each stage leaves students with a working system even if later stages are skipped. Mandatory stages should fit a single session; optional addons should be referenceable as independent extensions.

## Implementation Changes
### Mandatory core
- Create a starter repo with a single PKB root containing `notes/`, `templates/`, `sources/`, and `prompts/`.
- Store each knowledge item as one Markdown file with required YAML fields:
  - `id`
  - `title`
  - `type`
  - `status`
  - `tags`
  - `source_refs`
  - `created`
  - `updated`
  - `ai_assisted`
  - `human_reviewed`
- Limit the workshop ontology to 4 note types and 4-5 relationship styles.
  Default:
  - Types: `concept`, `source`, `person`, `project`
  - Relationships: `related_to`, `supports`, `contradicts`, `applies_to`, `mentions`
- Standardize note structure so every note has:
  - one-paragraph summary
  - key points
  - linked notes
  - evidence/source section
  - open questions
- Use wiki-style or relative Markdown links consistently so the note graph is inspectable without extra software.
- Keep filenames human-readable and stable: `YYYYMMDD-short-title.md` for time-based captures or `type-short-title.md` for canonical notes.

### Mandatory AI layer
- Use `Gemini 2.5 Flash-Lite` as the default model for all live workshop AI tasks.
- Make AI workflows prompt-first rather than code-first. Students should be able to complete the workshop with copy/paste prompts inside VS Code or a browser-based coding environment.
- Provide 4 fixed prompt templates:
  - source-to-note summary
  - metadata extraction
  - related-note/link suggestion
  - answer a question from a supplied set of notes
- Require bounded AI inputs. Students should pass one source or a small note bundle at a time, not the whole repo.
- Require explicit human review before an AI draft becomes a final note.
- Mark all AI-generated content in frontmatter or a provenance section so students can distinguish draft output from reviewed knowledge.

### Mandatory engineering process
- Initialize the PKB in Git from the start and teach a minimal commit workflow:
  - initial scaffold
  - first notes/templates
  - AI-assisted enrichment
  - review/cleanup
- Use short, meaningful commit messages tied to workshop milestones, not arbitrary save-point commits.
- Add a lightweight `.gitignore` for secrets, transient exports, and local caches.
- Keep API keys out of notes and source files. Use environment variables or per-user local config excluded from Git.
- Keep evidence of AI assistance in note metadata and revision history rather than a separate log workflow.

### Optional addons
- `Addon A: Better synthesis`
  Use `Gemini 2.5 Flash` for cross-note synthesis, comparison, literature-style summaries, and higher-quality Q&A.
- `Addon B: Prompt-to-script automation`
  Convert one prompt workflow into a small optional script for batch summarization or metadata generation.
- `Addon C: Structured export`
  Export notes and links to `JSON` or `CSV` so the PKB can be inspected as nodes and edges.
- `Addon D: Lightweight query tooling`
  Add a simple repo-level query workflow over note metadata, tags, and links before introducing more advanced AI retrieval.
- `Addon E: Retrieval augmentation`
  Add embeddings/vector search only as an advanced extension; do not make it part of the single-session baseline.

## Public Interfaces / Types
- Define one canonical note contract for the workshop: Markdown body plus YAML frontmatter fields listed above.
- Define one status lifecycle for notes:
  - `captured`
  - `ai-drafted`
  - `reviewed`
  - `final`
- Define one provenance contract for AI usage:
  - model used
  - prompt type
  - source/input files
  - reviewer
  - review date
- Define one prompt library contract in `prompts/` so prompts are reusable and versioned with the repo rather than living in chat history.
- Define one repository rule: Markdown notes are the source of truth; AI outputs are drafts unless marked reviewed.

## Test Plan
- Students can create at least 5-8 notes in the mandatory format without tool ambiguity.
- Every note validates manually against the required metadata contract.
- Students can navigate between related notes using links alone.
- Students can retrieve information in three ways:
  - VS Code text search
  - metadata/tag filtering by convention
  - AI answer over a selected note subset
- AI tasks stay within free-tier-friendly usage:
  - single-source summaries
  - small-bundle Q&A
  - no mandatory whole-repo querying
- Git workflow works end-to-end:
  - repo initialized or cloned
  - at least 3 meaningful commits created
  - no secrets committed
- Provenance is visible:
  - at least one note shows AI assistance
  - at least one note shows human review after AI drafting

## Assumptions
- The plan is optimized for a single workshop session, so advanced automation is intentionally deferred.
- Students may be using local VS Code or cloud-based coding environments, so the workflow cannot depend on local model inference.
- `Gemini 2.5 Flash-Lite` is the default due to free-tier practicality; `Gemini 2.5 Flash` is optional for higher-quality synthesis, not baseline use.
- The workshop should succeed even if some students do not complete live API setup; the core PKB remains fully functional without AI.
- Python/Node scripting is out of scope for the mandatory path and should appear only as an addon or instructor demonstration.
