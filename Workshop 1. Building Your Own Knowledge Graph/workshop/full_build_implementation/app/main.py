from __future__ import annotations

from collections import Counter
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.models import (
    AiTaskRequest,
    DashboardSummary,
    InferMetadataRequest,
    InferMetadataResponse,
    SaveDraftRequest,
    UpdateNoteRequest,
    UpdateNoteStatusRequest,
)
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
    def root_notes_page(
        request: Request,
        note_kind: str | None = None,
        topic: str | None = None,
        tag: str | None = None,
        person: str | None = None,
        source: str | None = None,
        project: str | None = None,
        view: str | None = None,
    ) -> HTMLResponse:
        return _render_notes_page(
            request=request,
            templates=templates,
            note_repository=note_repository,
            settings=settings,
            note_kind=note_kind,
            topic=topic,
            tag=tag,
            person=person,
            source=source,
            project=project,
            view=view,
        )

    @app.get("/stats", response_class=HTMLResponse)
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
                "title": "Stats",
            },
        )

    @app.get("/notes", response_class=HTMLResponse)
    def notes_page(
        request: Request,
        note_kind: str | None = None,
        topic: str | None = None,
        tag: str | None = None,
        person: str | None = None,
        source: str | None = None,
        project: str | None = None,
        view: str | None = None,
    ) -> HTMLResponse:
        return _render_notes_page(
            request=request,
            templates=templates,
            note_repository=note_repository,
            settings=settings,
            note_kind=note_kind,
            topic=topic,
            tag=tag,
            person=person,
            source=source,
            project=project,
            view=view,
        )

    @app.get("/notes/{slug}", response_class=HTMLResponse)
    def note_detail(request: Request, slug: str) -> HTMLResponse:
        try:
            note = note_repository.get_note(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        related_logs = _logs_for_note(log_service.list_logs(), note.path)
        return templates.TemplateResponse(
            request,
            "note_detail.html",
            {
                "note": note,
                "related_logs": related_logs,
                "ai_enabled": settings.ai_enabled,
                "title": note.metadata.title,
                "build_explore_href": _build_explore_href,
            },
        )

    @app.get("/notes/{slug}/edit", response_class=HTMLResponse)
    def edit_note_page(request: Request, slug: str) -> HTMLResponse:
        try:
            note = note_repository.get_note(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return templates.TemplateResponse(
            request,
            "edit_note.html",
            {
                "note": note,
                "ai_enabled": settings.ai_enabled,
                "title": f"Edit {note.metadata.title}",
            },
        )

    @app.get("/sources", response_class=HTMLResponse)
    def sources_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "sources.html", {"sources": source_repository.list_sources(), "ai_enabled": settings.ai_enabled, "title": "Sources"}
        )

    @app.get("/explore", response_class=HTMLResponse)
    def explore_page(request: Request, kind: str, value: str) -> HTMLResponse:
        if kind not in {"topic", "tag", "person", "source", "project"}:
            raise HTTPException(status_code=404, detail=f"Unsupported exploration kind: {kind}")
        notes = _notes_for_entity(note_repository.list_notes(), kind, value)
        related_counts = _build_related_counts(notes, kind, value)
        return templates.TemplateResponse(
            request,
            "explore.html",
            {
                "kind": kind,
                "value": value,
                "notes": notes,
                "related_counts": related_counts,
                "ai_enabled": settings.ai_enabled,
                "title": f"Explore {value}",
                "build_explore_href": _build_explore_href,
            },
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

    @app.post("/api/notes/infer-metadata")
    def infer_metadata(request_body: InferMetadataRequest) -> InferMetadataResponse:
        try:
            inferred_metadata = ai_service.infer_note_metadata(
                title=request_body.title,
                content=request_body.content,
                source_refs=request_body.source_refs,
            )
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"Could not infer metadata: {exc}") from exc
        if inferred_metadata.get("model"):
            log_service.write_log(
                task="metadata_extraction",
                prompt_slug=str(inferred_metadata["prompt_slug"]),
                model=str(inferred_metadata["model"]),
                input_files=list(inferred_metadata["input_paths"]),
                output_target="ui-preview",
                review_outcome="pending-review",
                notes="Metadata preview generated during note creation.",
            )
        return InferMetadataResponse(
            note_kind=inferred_metadata["note_kind"],
            topics=list(inferred_metadata["topics"]),
            people=list(inferred_metadata["people"]),
            sources=list(inferred_metadata["sources"]),
            projects=list(inferred_metadata["projects"]),
            tags=list(inferred_metadata["tags"]),
            source_refs=list(inferred_metadata["source_refs"]),
            ai_enabled=bool(inferred_metadata.get("model")),
            model=inferred_metadata.get("model"),
            prompt_slug=inferred_metadata.get("prompt_slug"),
        )

    @app.post("/api/notes/save-draft")
    def save_draft(request_body: SaveDraftRequest) -> dict:
        inferred_metadata = None
        if request_body.metadata_reviewed:
            note_kind = request_body.note_kind
            topics = request_body.topics
            people = request_body.people
            sources = request_body.sources
            projects = request_body.projects
            tags = request_body.tags
            source_refs = request_body.source_refs
            used_ai_metadata = settings.ai_enabled
        else:
            try:
                inferred_metadata = ai_service.infer_note_metadata(
                    title=request_body.title,
                    content=request_body.content,
                    source_refs=request_body.source_refs,
                )
            except (RuntimeError, ValueError):
                inferred_metadata = None
            if inferred_metadata:
                note_kind = request_body.note_kind or inferred_metadata["note_kind"]
                topics = _merge_metadata_lists(request_body.topics, inferred_metadata["topics"])
                people = _merge_metadata_lists(request_body.people, inferred_metadata["people"])
                sources = _merge_metadata_lists(request_body.sources, inferred_metadata["sources"])
                projects = _merge_metadata_lists(request_body.projects, inferred_metadata["projects"])
                tags = _merge_metadata_lists(request_body.tags, inferred_metadata["tags"])
                source_refs = _merge_metadata_lists(request_body.source_refs, inferred_metadata["source_refs"])
                used_ai_metadata = bool(inferred_metadata.get("model"))
            else:
                note_kind = request_body.note_kind
                topics = request_body.topics
                people = request_body.people
                sources = request_body.sources
                projects = request_body.projects
                tags = request_body.tags
                source_refs = request_body.source_refs
                used_ai_metadata = False
        note = note_repository.save_draft(
            title=request_body.title,
            note_kind=note_kind,
            topics=topics,
            people=people,
            sources=sources,
            projects=projects,
            source_refs=source_refs,
            tags=tags,
            content=request_body.content,
            ai_assisted=request_body.ai_assisted or used_ai_metadata,
        )
        if inferred_metadata and used_ai_metadata and not request_body.metadata_reviewed:
            log_service.write_log(
                task="metadata_extraction",
                prompt_slug=str(inferred_metadata["prompt_slug"]),
                model=str(inferred_metadata["model"]),
                input_files=list(inferred_metadata["input_paths"]),
                output_target=note.path,
                review_outcome="pending-review",
                notes="Metadata inferred during note creation.",
            )
        log_service.write_log(
            task="save_draft",
            prompt_slug="manual-or-ui",
            model="n/a",
            input_files=source_refs,
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

    @app.put("/api/notes/{slug}")
    def update_note(slug: str, request_body: UpdateNoteRequest) -> dict:
        try:
            note = note_repository.update_note(
                slug=slug,
                title=request_body.title,
                note_kind=request_body.note_kind,
                topics=request_body.topics,
                people=request_body.people,
                sources=request_body.sources,
                projects=request_body.projects,
                source_refs=request_body.source_refs,
                tags=request_body.tags,
                content=request_body.content,
                status=request_body.status,
                ai_assisted=request_body.ai_assisted,
                human_reviewed=request_body.human_reviewed,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        log_service.write_log(
            task="update_note",
            prompt_slug="manual-edit",
            model="n/a",
            input_files=note.metadata.source_refs,
            output_target=note.path,
            review_outcome="updated",
            notes="Existing note edited in UI.",
        )
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
        note_kind_counts=dict(Counter(note.metadata.note_kind for note in notes if note.metadata.note_kind)),
        note_status_counts=dict(Counter(note.metadata.status for note in notes)),
        ai_enabled=settings.ai_enabled,
    )


def _render_notes_page(
    request: Request,
    templates: Jinja2Templates,
    note_repository: NoteRepository,
    settings: Settings,
    note_kind: str | None = None,
    topic: str | None = None,
    tag: str | None = None,
    person: str | None = None,
    source: str | None = None,
    project: str | None = None,
    view: str | None = None,
) -> HTMLResponse:
    view_mode = view if view in {"grid", "row"} else "grid"
    notes = note_repository.list_notes()
    if note_kind:
        notes = [note for note in notes if note.metadata.note_kind == note_kind]
    if topic:
        notes = [note for note in notes if topic in note.metadata.topics]
    if tag:
        notes = [note for note in notes if tag in note.metadata.tags]
    if person:
        notes = [note for note in notes if person in note.metadata.people]
    if source:
        notes = [note for note in notes if source in note.metadata.sources]
    if project:
        notes = [note for note in notes if project in note.metadata.projects]
    unique_notes = note_repository.list_notes()
    return templates.TemplateResponse(
        request,
        "notes.html",
        {
            "notes": notes,
            "all_notes": unique_notes,
            "ai_enabled": settings.ai_enabled,
            "title": "Notes",
            "view_mode": view_mode,
            "build_explore_href": _build_explore_href,
            "active_filters": {
                "note_kind": note_kind or "",
                "topic": topic or "",
                "tag": tag or "",
                "person": person or "",
                "source": source or "",
                "project": project or "",
                "view": view_mode,
            },
        },
    )


def _merge_metadata_lists(primary: list[str], secondary: object) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for candidate in [*primary, *(secondary if isinstance(secondary, list) else [])]:
        cleaned = str(candidate).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        merged.append(cleaned)
    return merged


def _notes_for_entity(notes: list, kind: str, value: str) -> list:
    attribute_map = {
        "topic": "topics",
        "tag": "tags",
        "person": "people",
        "source": "sources",
        "project": "projects",
    }
    attribute_name = attribute_map[kind]
    return [note for note in notes if value in getattr(note.metadata, attribute_name)]


def _build_related_counts(notes: list, active_kind: str, active_value: str) -> dict[str, list[tuple[str, int]]]:
    related: dict[str, list[tuple[str, int]]] = {}
    attribute_map = {
        "topic": "topics",
        "tag": "tags",
        "person": "people",
        "source": "sources",
        "project": "projects",
    }
    for kind, attribute_name in attribute_map.items():
        counter: Counter = Counter()
        for note in notes:
            values = getattr(note.metadata, attribute_name)
            for value in values:
                if kind == active_kind and value == active_value:
                    continue
                counter[value] += 1
        related[kind] = counter.most_common(8)
    return related


def _build_explore_href(kind: str, value: str) -> str:
    return f"/explore?kind={quote(kind)}&value={quote(value)}"


def _logs_for_note(logs: list, note_path: str) -> list:
    return [log for log in logs if log.output_target == note_path or note_path in log.input_files]


app = create_app()
