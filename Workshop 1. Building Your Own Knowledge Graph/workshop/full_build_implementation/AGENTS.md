# AGENTS.md

This file defines working instructions for agents and contributors operating in this project.

It is intended to keep implementation work consistent, safe, and well documented over time.

## Project Context

This project is an instructor-facing reference implementation for a personal knowledge base workshop. It extends a Markdown and YAML based note workflow into a working web application with note creation, metadata management, graph exploration, AI-assisted note workflows, and lightweight knowledge management features.

## Tech Stack

- Backend: Python
- Web framework: FastAPI
- Templates: Jinja2
- Frontend: server-rendered HTML, vanilla JavaScript, CSS
- Data format: Markdown files with YAML frontmatter
- Testing: `pytest`
- AI integration: Gemini client support when configured
- Runtime pattern: local file-backed app, not database-backed

## Dos

- Do make targeted, minimal changes that fit the existing structure of the app.
- Do prefer server-side enforcement for shared business rules when behavior must be consistent across multiple UI entry points.
- Do add or update tests when changing behavior.
- Do preserve the Markdown-plus-frontmatter architecture unless a change explicitly requires otherwise.
- Do keep user-facing copy clear and simple.
- Do update documentation when product behavior, workflows, setup, or feature scope changes.
- Do keep `WORKLOG.md`, `CHANGELOG.md`, and `todo.md` current as part of normal delivery.
- Do record meaningful implementation decisions so future contributors can understand why something was done.

## Don'ts

- Don't hardcode secrets, API keys, tokens, or credentials in source files, docs, tests, or example payloads.
- Don't commit `.env` files or secret-bearing local config.
- Don't introduce unnecessary frameworks or dependencies when the current stack already supports the feature.
- Don't bypass existing patterns for note storage, metadata merging, or route structure without a strong reason.
- Don't silently change product behavior without updating tests and project documentation.
- Don't treat `CHANGELOG.md` as a scratchpad; keep it outcome-focused and readable.
- Don't treat `WORKLOG.md` as a one-line summary; it should capture enough detail for historical reconstruction.

## Secrets Handling

- Store secrets in environment variables only.
- Use local `.env` files only when they are already part of the project workflow, and never commit them.
- Treat API keys, access tokens, credentials, signed URLs, and private endpoints as secrets unless clearly public.
- When documenting setup, refer to secret names such as `GEMINI_API_KEY` without including real values.
- If a screenshot, log, or output contains secret material, redact it before saving or sharing.
- If test fixtures ever require secret-like values, use obvious placeholders such as `test-api-key` rather than realistic credentials.

## Documentation Rules

Documentation updates are part of the definition of done for this project.

### Required on Every Commit

For every commit that changes product behavior, implementation scope, roadmap status, or project documentation:

- Update `WORKLOG.md`
- Update `CHANGELOG.md`
- Update `todo.md` when feature status, progress, priority, or roadmap shape has changed

These updates should be made before creating the commit so the repository history stays aligned with the shipped work.

### WORKLOG.md Guidance

Use `WORKLOG.md` for comprehensive internal history.

Add an entry when:
- code is added, removed, or refactored
- tests are added or changed
- a product decision is made
- a bug is investigated or fixed
- a feature plan is implemented
- setup or workflow documentation changes in a meaningful way

Each entry should include:
- date
- short session title
- summary of the work
- files touched
- key decisions
- testing or verification performed
- follow-up items or unresolved issues

### CHANGELOG.md Guidance

Use `CHANGELOG.md` for concise notable changes.

Add or update an entry when:
- a feature is added
- a behavior changes
- a bug is fixed
- a new documentation artifact or workflow is introduced

Keep it focused on:
- what changed
- why it matters to the project or user

Avoid:
- raw debugging notes
- internal-only implementation minutiae
- duplicated low-level detail already covered in `WORKLOG.md`

### todo.md Guidance

Use `todo.md` to track roadmap progress and current status.

Update it when:
- a feature starts
- a feature advances materially
- percent complete changes
- a feature is blocked
- a feature is completed
- roadmap priorities or ordering change
- new approved roadmap items are added

The table should stay current enough that someone can quickly see:
- what is planned
- what is in progress
- what is done
- what is blocked

## Implementation Preferences

- Favor helper functions for reusable business rules.
- Keep route handlers readable and avoid burying core behavior in long inline logic.
- Prefer extending current utilities over creating duplicate logic paths.
- Keep naming explicit and behavior-driven.
- When changing note creation behavior, consider all creation entry points, not just one screen.

## Testing Expectations

- Add or update tests for any user-visible or data-shaping behavior change.
- Prefer route-level tests for API workflow changes and repository-level tests for storage behavior.
- If a full test suite cannot be run, record what was run and what remains unverified in `WORKLOG.md`.

## File Placement

Place new product planning or tracking artifacts in the `full_build_implementation` project area unless there is a strong reason to store them elsewhere.

## Agent Operating Rule

Before committing work:
- verify code changes
- update `WORKLOG.md`
- update `CHANGELOG.md`
- update `todo.md` if roadmap or status changed
- then commit the complete set together
