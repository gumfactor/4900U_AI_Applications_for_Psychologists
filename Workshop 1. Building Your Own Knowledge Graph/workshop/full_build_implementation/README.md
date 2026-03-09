# Full Build Implementation

This is the instructor-facing reference implementation for the workshop. It extends the student-facing Markdown/YAML workflow into a working FastAPI application with a browse/query UI, bounded Gemini tasks, AI interaction logging, and note draft saving.

## Quick Start

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env` and add `GEMINI_API_KEY` if you want AI features. The app loads `.env` automatically at startup.
4. Run the app with:

```powershell
uvicorn app.main:app --reload
```

If no Gemini key is configured, the app runs in browse-only mode and disables AI actions in the UI.
