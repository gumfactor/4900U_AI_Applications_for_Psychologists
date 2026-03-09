from __future__ import annotations

from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.models import AiTaskRequest, DashboardSummary, SaveDraftRequest, UpdateNoteStatusRequest
from app.services.ai_service import AiService
from app.services.gemini_client import GeminiClient
from app.services.log_service import LogService
from app.services.note_repository import NoteRepository
from app.services.prompt_repository import PromptRepository
from app.services.source_repository import SourceRepository


def create_app(base_dir: Path | None = None, gemini_client: GeminiClient | None = None) -> FastAPI:
    settings = get_settings(base_dir)
    note_repository = NoteRepository(settings.notes_dir)
    source_repository = SourceRepository(settings.sources_dir)
    prompt_repository = PromptRepository(settings.prompts_dir)
    log_service = LogService(settings.logs_dir)
    ai_service = AiService(
        note_repository=note_repository,
        source_repository=source_repository,
        prompt_repository=prompt_repository,
        log_service=log_service,
        gemini_client=gemini_client or (GeminiClient(settings.gemini_api_key) if settings.ai_enabled else None),
        default_model=settings.default_model,
        high_quality_model=settings.high_quality_model,
    )

    app = FastAPI(title="Instructor PKB Demo")
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
    templates = Jinja2Templates(directory=str(settings.templates_dir))

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request) -> HTMLResponse:
        summary = _build_dashboard_summary(settings, note_repository, source_repository, log_service)
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "summary": summary,
                "recent_notes": note_repository.list_notes()[:5],
                "recent_logs": log_service.list_logs()[:5],
                "ai_enabled": settings.ai_enabled,
                "title": "Dashboard",
            },
        )

    @app.get("/notes", response_class=HTMLResponse)
    def notes_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "notes.html", {"notes": note_repository.list_notes(), "ai_enabled": settings.ai_enabled, "title": "Notes"}
        )

    @app.get("/notes/{slug}", response_class=HTMLResponse)
    def note_detail(request: Request, slug: str) -> HTMLResponse:
        try:
            note = note_repository.get_note(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return templates.TemplateResponse(
            request, "note_detail.html", {"note": note, "ai_enabled": settings.ai_enabled, "title": note.metadata.title}
        )

    @app.get("/sources", response_class=HTMLResponse)
    def sources_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "sources.html", {"sources": source_repository.list_sources(), "ai_enabled": settings.ai_enabled, "title": "Sources"}
        )

    @app.get("/sources/{slug}", response_class=HTMLResponse)
    def source_detail(request: Request, slug: str) -> HTMLResponse:
        try:
            source = source_repository.get_source(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return templates.TemplateResponse(
            request, "source_detail.html", {"source": source, "ai_enabled": settings.ai_enabled, "title": source.title}
        )

    @app.get("/logs", response_class=HTMLResponse)
    def logs_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "logs.html", {"logs": log_service.list_logs(), "ai_enabled": settings.ai_enabled, "title": "Logs"}
        )

    @app.get("/logs/{slug}", response_class=HTMLResponse)
    def log_detail(request: Request, slug: str) -> HTMLResponse:
        try:
            log_entry = log_service.get_log(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return templates.TemplateResponse(
            request, "log_detail.html", {"log_entry": log_entry, "ai_enabled": settings.ai_enabled, "title": "Log Detail"}
        )

    @app.get("/ai", response_class=HTMLResponse)
    def ai_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "ai.html",
            {
                "notes": note_repository.list_notes(),
                "sources": source_repository.list_sources(),
                "default_model": settings.default_model,
                "high_quality_model": settings.high_quality_model,
                "ai_enabled": settings.ai_enabled,
                "title": "AI Tasks",
            },
        )

    @app.get("/api/dashboard")
    def dashboard_api() -> DashboardSummary:
        return _build_dashboard_summary(settings, note_repository, source_repository, log_service)

    @app.get("/api/notes")
    def notes_api() -> list[dict]:
        return [note.model_dump() for note in note_repository.list_notes()]

    @app.get("/api/notes/{slug}")
    def note_api(slug: str) -> dict:
        try:
            return note_repository.get_note(slug).model_dump()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/sources")
    def sources_api() -> list[dict]:
        return [source.model_dump() for source in source_repository.list_sources()]

    @app.get("/api/logs")
    def logs_api() -> list[dict]:
        return [log_entry.model_dump() for log_entry in log_service.list_logs()]

    @app.post("/api/ai/run")
    def run_ai_task(task_request: AiTaskRequest) -> dict:
        try:
            return ai_service.run_task(task_request).model_dump()
        except (RuntimeError, ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/notes/save-draft")
    def save_draft(request_body: SaveDraftRequest) -> dict:
        note = note_repository.save_draft(
            title=request_body.title,
            note_type=request_body.note_type,
            source_refs=request_body.source_refs,
            tags=request_body.tags,
            content=request_body.content,
            ai_assisted=request_body.ai_assisted,
        )
        log_service.write_log(
            task="save_draft",
            prompt_slug="manual-or-ui",
            model="n/a",
            input_files=request_body.source_refs,
            output_target=note.path,
            review_outcome="pending-review",
            notes="Draft note saved from UI.",
        )
        return note.model_dump()

    @app.post("/api/notes/{slug}/status")
    def update_note_status(slug: str, request_body: UpdateNoteStatusRequest) -> dict:
        try:
            note = note_repository.update_status(slug, request_body.status, request_body.human_reviewed)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return note.model_dump()

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException) -> HTMLResponse | JSONResponse:
        accepts_json = "application/json" in request.headers.get("accept", "")
        if accepts_json or request.url.path.startswith("/api/"):
            return JSONResponse({"detail": exc.detail}, status_code=404)
        return templates.TemplateResponse(
            request, "error.html", {"message": exc.detail, "status_code": 404, "title": "Error"}, status_code=404
        )

    return app


def _build_dashboard_summary(
    settings: Settings,
    note_repository: NoteRepository,
    source_repository: SourceRepository,
    log_service: LogService,
) -> DashboardSummary:
    notes = note_repository.list_notes()
    sources = source_repository.list_sources()
    logs = log_service.list_logs()
    return DashboardSummary(
        total_notes=len(notes),
        total_sources=len(sources),
        total_logs=len(logs),
        note_type_counts=dict(Counter(note.metadata.type for note in notes)),
        note_status_counts=dict(Counter(note.metadata.status for note in notes)),
        ai_enabled=settings.ai_enabled,
    )


app = create_app()
