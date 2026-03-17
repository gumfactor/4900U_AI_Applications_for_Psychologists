# Changelog

All notable changes to this project should be recorded in this file.

This file is intended to be a readable historical summary of product, engineering, and documentation changes over time. It should stay concise compared with `WORKLOG.md`, while still preserving the important milestones and outcomes.

## How To Use This File

- Add the newest changes at the top.
- Group related work into a single dated section when possible.
- Focus on outcomes and visible project changes rather than minute implementation detail.
- Reference major features, fixes, documentation updates, and structural changes.

## Suggested Entry Template

```md
## YYYY-MM-DD

### Added
- New feature or file

### Changed
- Behavior update or improvement

### Fixed
- Bug fix or regression repair

### Documented
- Documentation, planning, or tracking update
```

---

## 2026-03-17

### Added
- Persisted task statuses for notes with `open`, `in-progress`, and `done` values.
- Status badges and status filtering in the notes browser.
- Quick task status updates from the note detail page.

### Changed
- Note create, edit, and AI draft-save flows now capture task status alongside other note metadata.

### Documented
- Marked `Task Status Workflow` complete in `todo.md`.

## 2026-03-17

### Added
- Optional due dates for notes across create, edit, and AI draft-save flows.
- Reminder-focused notes browser views for `Due Today`, `Upcoming`, and `Overdue`.

### Changed
- Note cards and note detail pages now surface due date status directly in the UI.
- The roadmap now marks `Due Dates and Reminder Views` as completed.

### Documented
- Updated the project README and historical tracking files to reflect the new due date workflow.

## 2026-03-17

### Added
- `WORKLOG.md` to maintain a detailed session-by-session historical work record.
- `CHANGELOG.md` to maintain a summarized project history of notable changes.

### Documented
- Established a two-file logging system to support comprehensive long-term project recordkeeping.
