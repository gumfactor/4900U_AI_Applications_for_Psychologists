# Full Build Implementation

This is the instructor-facing reference implementation for the workshop. It extends the student-facing Markdown/YAML workflow into a working FastAPI application with a browse/query UI, bounded Gemini tasks, AI interaction logging, and note authoring built around multi-value entity attributes.

## Current Feature Set

- `Notes` is the default landing page.
- `Stats` summarizes note, source, and log counts.
- New notes can be created from the slideout editor.
- When Gemini is available, new-note metadata is inferred from the title and body before final save.
- Existing notes can be edited in-app.
- Tags, people, sources, projects, and topics link into connected exploration views.
- Note detail pages show related AI activity logs and provenance context.
- The AI Tasks page supports bounded source summary, metadata extraction, related-note suggestion, and question answering.

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
3. Open the resulting note and inspect its related AI activity block.
4. Edit the note in-app.
5. Click a tag, person, source, or project to move into the connected exploration view.
6. Use `AI Tasks` for bounded source summary or Q&A.
