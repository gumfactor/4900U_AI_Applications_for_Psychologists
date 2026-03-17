# Work Log

This file is the detailed historical record of work performed on this app.

Use it to capture implementation activity comprehensively, including planning, coding, testing, debugging, design changes, refactors, documentation updates, and decisions made during each work session.

## How To Use This File

- Add a new dated entry for each work session.
- Keep entries in reverse chronological order, with the newest session at the top.
- Record both completed work and meaningful in-progress work.
- Include enough detail that someone reviewing the project later can understand what changed, why it changed, and how it was verified.

## Suggested Entry Template

```md
## YYYY-MM-DD - Short Session Title

### Summary
Brief overview of what was worked on during the session.

### Work Completed
- Specific implementation change
- Specific bug fix or behavior update
- Documentation or planning output created

### Files Touched
- path/to/file.ext
- path/to/another-file.ext

### Decisions
- Important decision and rationale

### Testing / Verification
- Test command run
- Manual verification performed
- Known limitations or unresolved issues

### Follow-Up
- Next step
- Open question
```

---

## 2026-03-17 - Task Status Workflow

### Summary
Implemented persisted task statuses and quick status updates as the next independent workflow after due dates and reminder views.

### Work Completed
- Added `status` metadata with `open`, `in-progress`, and `done` values to the note model and persisted frontmatter.
- Extended note creation, note editing, and AI draft-save flows to capture task status.
- Added status badges and status filtering to the notes browser.
- Added a lightweight note status patch route and note detail quick-update controls.
- Updated route and repository tests to verify status persistence, filtering, and status history changes.
- Marked the feature complete in the roadmap and changelog.

### Files Touched
- `app/models.py`
- `app/main.py`
- `app/services/markdown_utils.py`
- `app/services/note_repository.py`
- `app/templates/base.html`
- `app/templates/edit_note.html`
- `app/templates/ai.html`
- `app/templates/notes.html`
- `app/templates/note_detail.html`
- `app/static/style.css`
- `tests/test_routes.py`
- `tests/test_note_repository.py`
- `todo.md`
- `WORKLOG.md`
- `CHANGELOG.md`

### Decisions
- Defaulted missing note status metadata to `open` so existing notes continue to load without migration work.
- Added a status-only patch endpoint to support quick updates without requiring full note edits.

### Testing / Verification
- Ran `PYTHONPATH=. pytest tests/test_routes.py tests/test_note_repository.py`.
- Verified all 30 targeted tests passed.

### Follow-Up
- Saved searches or smart collections would pair naturally with the new status filter.

## 2026-03-17 - Due Dates and Reminder Views

### Summary
Implemented due date support across note creation, editing, storage, and browsing, plus reminder-focused `Due Today`, `Upcoming`, and `Overdue` views on the notes page.

### Work Completed
- Added optional `due_date` metadata to notes and request models.
- Extended Markdown frontmatter parsing and note repository writes to preserve due dates.
- Added due date inputs to the new note panel, edit note page, and AI save-draft flow.
- Added reminder-focused due bucket views to the notes browser.
- Added due date badges to note cards and note detail pages.
- Added tests for metadata parsing, repository persistence, route persistence, and due view filtering.
- Updated the roadmap and README to reflect the shipped feature.

### Files Touched
- `app/models.py`
- `app/services/markdown_utils.py`
- `app/services/note_repository.py`
- `app/main.py`
- `app/templates/base.html`
- `app/templates/edit_note.html`
- `app/templates/ai.html`
- `app/templates/notes.html`
- `app/templates/note_detail.html`
- `app/static/style.css`
- `tests/test_markdown_utils.py`
- `tests/test_note_repository.py`
- `tests/test_routes.py`
- `README.md`
- `todo.md`
- `WORKLOG.md`
- `CHANGELOG.md`

### Decisions
- Stored due dates as optional ISO date strings in note frontmatter to stay consistent with the file-backed architecture.
- Scoped `Due Today`, `Upcoming`, and `Overdue` views to reminder-tagged notes so the views stay aligned with the reminder workflow.
- Kept due dates optional for all notes rather than restricting them only to todo notes.

### Testing / Verification
- Planned verification through `pytest` route, repository, and markdown utility tests.
- Follow-up verification needed after integrating all template and route changes together.

### Follow-Up
- Consider adding task status fields next so due dates and reminders can distinguish active work from completed work.

## 2026-03-17 - Project Logging Initialized

### Summary
Created dedicated historical record files for ongoing project tracking.

### Work Completed
- Added `WORKLOG.md` for detailed session-by-session implementation records.
- Added `CHANGELOG.md` for high-level user-facing and project-level change summaries.

### Files Touched
- `WORKLOG.md`
- `CHANGELOG.md`

### Decisions
- Split historical tracking into two layers:
- `WORKLOG.md` for comprehensive internal work detail.
- `CHANGELOG.md` for curated milestone and change summaries.

### Testing / Verification
- Verified both log files were created in the project root.

### Follow-Up
- Begin appending future sessions to this file as work continues.
