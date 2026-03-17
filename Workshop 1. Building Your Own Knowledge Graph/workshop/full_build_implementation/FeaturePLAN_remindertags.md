# Auto-Tag Todo Notes With `reminder`

## Summary
Ensure every newly created todo note automatically includes the `reminder` tag.

A note is considered a todo note when its title begins with the prefix `TODO:`. This rule should be enforced server-side in the shared create-note path so it applies consistently to both the slideout "New Note" form and the AI "Save Draft Note" flow.

## Implementation Changes
- Update the note creation flow in `app/main.py` inside `POST /api/notes/save-draft`.
- Before the note is saved, normalize the final tag list and append `reminder` when:
  - the request title, after trimming leading/trailing whitespace, starts with `TODO:`
  - matching is case-insensitive, so `todo:` and `ToDo:` also count
- Apply the rule after any AI tag inference/merge logic so the final saved payload always contains `reminder` for todo notes.
- Preserve existing user-entered and AI-inferred tags.
- De-duplicate tags case-insensitively so `reminder` is not added twice if the user already supplied it.
- Do not change update behavior in `PUT /api/notes/{slug}`. This plan only affects note creation, matching the stated requirement.
- No API schema changes are needed. `SaveDraftRequest` and `UpdateNoteRequest` stay as-is.

## Test Plan
- Add a route test proving `POST /api/notes/save-draft` adds `reminder` when title is `TODO: Finish slides`.
- Add a route test proving the rule also works when the title uses different casing, such as `todo: finish slides`.
- Add a route test proving `reminder` is not duplicated if already present in the submitted tags.
- Add a route test proving non-todo titles do not get `reminder`.
- Add a route test proving other tags remain intact when `reminder` is injected.

## Assumptions
- "Create a todo note" means creating a new note whose title starts with `TODO:`.
- The automatic tag value is exactly `reminder`.
- Enforcement belongs in the server create route, not only in the UI, so all creation entry points behave the same way.
- Existing notes and note edits are out of scope for this change.
