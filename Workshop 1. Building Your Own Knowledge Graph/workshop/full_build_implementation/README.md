# Full Build Implementation

This is the instructor-facing reference implementation for the workshop. It extends the student-facing Markdown/YAML workflow into a working FastAPI application with a browse/query UI, bounded Gemini tasks, and note authoring built around multi-value entity attributes.

## Current Feature Set

- `Notes` is the default landing page.
- The `Notes` banner shows the current note count and filtered result count.
- `Graph` provides a workspace-level relationship view over authored note links, with optional metadata-derived edges.
- New notes can be created from the slideout editor.
- When Gemini is available, new-note metadata is inferred from the title and body before final save.
- Existing notes can be edited in-app.
- Notes can store optional due dates.
- The notes browser includes reminder-focused `Due Today`, `Upcoming`, and `Overdue` views.
- Tags, people, sources, projects, and topics link into connected exploration views.
- Note detail pages show related notes, metadata, and version history.
- The `Multi Note Queries` page supports question answering across one or more selected notes.

## Quick Start

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env` and add `GEMINI_API_KEY` if you want AI features. The app loads `.env` automatically at startup.
4. Run the app with:

```powershell
uvicorn app.main:app --reload
```

If no Gemini key is configured, the app runs in browse-only mode and disables AI actions in the UI.

## Recommended Demo Path

1. Start on `Notes` and open the new-note slideout.
2. Show AI-assisted attribute suggestion on save.
3. Open the resulting note and inspect the generated structure and metadata.
4. Edit the note in-app.
5. Open `Graph` to show explicit note links, then toggle metadata edges on.
6. Click a tag, person, source, or project to move into the connected exploration view.
7. Use `Multi Note Queries` for cross-note Q&A.
