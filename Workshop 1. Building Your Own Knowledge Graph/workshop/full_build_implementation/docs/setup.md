# Setup

## Local VS Code

1. Open `workshop/full_build_implementation` in VS Code.
2. Create and activate a virtual environment.
3. Install dependencies with `python -m pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and add `GEMINI_API_KEY` if you want live AI. The app reads `.env` automatically.
5. Start the server with `uvicorn app.main:app --reload`.
6. Open `http://127.0.0.1:8000`.
7. The default landing page is `Notes`; `Graph` and `Multi Note Queries` are available in the top nav, and the `Notes` banner shows the current note count.
8. The graph view loads a lightweight browser library from a CDN, so an internet connection is required for the interactive graph canvas.

## Cloud IDE

1. Open the same folder in the cloud workspace.
2. Install dependencies into the available Python environment.
3. Set environment variables through the platform UI instead of writing secrets to disk.
4. Launch the app with `uvicorn app.main:app --reload`.
5. Use the `Notes` page as the primary starting point for demos, then open `Graph` for the relationship view.
