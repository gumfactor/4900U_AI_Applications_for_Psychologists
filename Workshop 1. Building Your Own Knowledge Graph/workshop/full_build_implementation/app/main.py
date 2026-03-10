from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
import re
from urllib.parse import quote, unquote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.models import (
    AiTaskRequest,
    ActivityEntry,
    DashboardSummary,
    InferMetadataRequest,
    InferMetadataResponse,
    SaveDraftRequest,
    UpdateNoteRequest,
)
from app.services.ai_service import AiService
from app.services.attachment_service import AttachmentService
from app.services.gemini_client import GeminiClient
from app.services.note_history_service import NoteHistoryService
from app.services.note_repository import NoteRepository
from app.services.prompt_repository import PromptRepository
from app.services.markdown_utils import split_sections


def create_app(base_dir: Path | None = None, gemini_client: GeminiClient | None = None) -> FastAPI:
    settings = get_settings(base_dir)
    note_repository = NoteRepository(settings.notes_dir)
    prompt_repository = PromptRepository(settings.prompts_dir)
    attachment_service = AttachmentService(settings.attachments_dir)
    note_history_service = NoteHistoryService(settings.history_dir, settings.notes_dir)
    ai_service = AiService(
        note_repository=note_repository,
        prompt_repository=prompt_repository,
        gemini_client=gemini_client or (GeminiClient(settings.gemini_api_key) if settings.ai_enabled else None),
        default_model=settings.default_model,
        high_quality_model=settings.high_quality_model,
    )

    app = FastAPI(title="Instructor PKB Demo")
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
    app.mount("/attachments", StaticFiles(directory=settings.attachments_dir), name="attachments")
    templates = Jinja2Templates(directory=str(settings.templates_dir))

    @app.get("/", response_class=HTMLResponse)
    def root_notes_page(
        request: Request,
        q: str | None = None,
        topic: str | None = None,
        tag: str | None = None,
        person: str | None = None,
        source: str | None = None,
        project: str | None = None,
        created_since: str | None = None,
        view: str | None = None,
    ) -> HTMLResponse:
        return _render_notes_page(
            request=request,
            templates=templates,
            note_repository=note_repository,
            settings=settings,
            q=q,
            topic=topic,
            tag=tag,
            person=person,
            source=source,
            project=project,
            created_since=created_since,
            view=view,
        )

    @app.get("/notes", response_class=HTMLResponse)
    def notes_page(
        request: Request,
        q: str | None = None,
        topic: str | None = None,
        tag: str | None = None,
        person: str | None = None,
        source: str | None = None,
        project: str | None = None,
        created_since: str | None = None,
        view: str | None = None,
    ) -> HTMLResponse:
        return _render_notes_page(
            request=request,
            templates=templates,
            note_repository=note_repository,
            settings=settings,
            q=q,
            topic=topic,
            tag=tag,
            person=person,
            source=source,
            project=project,
            created_since=created_since,
            view=view,
        )

    @app.get("/notes/{slug}", response_class=HTMLResponse)
    def note_detail(request: Request, slug: str, return_to: str | None = None) -> HTMLResponse:
        try:
            note = note_repository.get_note(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        version_history = _build_version_history(note_history_service.ensure_history(note), slug)
        related_notes = _related_notes_for(note_repository.list_notes(), note)
        return templates.TemplateResponse(
            request,
            "note_detail.html",
            {
                "note": note,
                "attachment_links": _build_attachment_links(note.metadata.attachments, attachment_service),
                "version_history": version_history,
                "related_notes": related_notes,
                "return_to": _safe_return_to(return_to),
                "draft_state": _build_draft_state(note),
                "ai_enabled": settings.ai_enabled,
                "title": note.metadata.title,
                "build_explore_href": _build_explore_href,
            },
        )

    @app.get("/notes/{slug}/history/{version_slug}", response_class=HTMLResponse)
    def note_version_detail(request: Request, slug: str, version_slug: str, return_to: str | None = None) -> HTMLResponse:
        try:
            versions = note_history_service.ensure_history(note_repository.get_note(slug))
            version = note_history_service.get_version(slug, version_slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        version_index = next((index for index, candidate in enumerate(versions) if candidate.slug == version_slug), None)
        if version_index is None:
            raise HTTPException(status_code=404, detail=f"Version not found: {version_slug}")
        previous_version = versions[version_index - 1] if version_index > 0 else None
        next_version = versions[version_index + 1] if version_index + 1 < len(versions) else None
        return templates.TemplateResponse(
            request,
            "note_version_detail.html",
            {
                "note": version.note,
                "version": version,
                "change_summary": _summarize_version_change(previous_version, version),
                "previous_version": previous_version,
                "next_version": next_version,
                "return_to": _safe_return_to(return_to) if return_to else f"/notes/{slug}",
                "draft_state": _build_draft_state(version.note),
                "ai_enabled": settings.ai_enabled,
                "title": f"{version.title} history",
                "build_explore_href": _build_explore_href,
            },
        )

    @app.get("/notes/{slug}/edit", response_class=HTMLResponse)
    def edit_note_page(request: Request, slug: str, return_to: str | None = None) -> HTMLResponse:
        try:
            note = note_repository.get_note(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return templates.TemplateResponse(
            request,
            "edit_note.html",
            {
                "note": note,
                "return_to": _safe_return_to(return_to),
                "ai_enabled": settings.ai_enabled,
                "title": f"Edit {note.metadata.title}",
            },
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

    @app.get("/ai", response_class=HTMLResponse)
    def ai_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "ai.html",
            {
                "notes": note_repository.list_notes(),
                "default_model": settings.default_model,
                "high_quality_model": settings.high_quality_model,
                "ai_enabled": settings.ai_enabled,
                "title": "Multi Note Queries",
            },
        )

    @app.get("/api/dashboard")
    def dashboard_api() -> DashboardSummary:
        return _build_dashboard_summary(settings, note_repository)

    @app.get("/api/notes")
    def notes_api() -> list[dict]:
        return [note.model_dump() for note in note_repository.list_notes()]

    @app.get("/api/notes/{slug}")
    def note_api(slug: str) -> dict:
        try:
            return note_repository.get_note(slug).model_dump()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

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
        return InferMetadataResponse(
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
        structured_content = request_body.content
        if not split_sections(request_body.content):
            try:
                structured_note = ai_service.structure_note_body(
                    title=request_body.title,
                    content=request_body.content,
                )
                structured_content = str(structured_note["content"])
            except (RuntimeError, ValueError):
                pass
        inferred_metadata = None
        try:
            inferred_metadata = ai_service.infer_note_metadata(
                title=request_body.title,
                content=structured_content,
                source_refs=request_body.source_refs,
            )
        except (RuntimeError, ValueError):
            inferred_metadata = None
        if inferred_metadata:
            topics = _merge_metadata_lists(request_body.topics, inferred_metadata["topics"])
            people = _merge_metadata_lists(request_body.people, inferred_metadata["people"])
            sources = _merge_metadata_lists(request_body.sources, inferred_metadata["sources"])
            projects = _merge_metadata_lists(request_body.projects, inferred_metadata["projects"])
            tags = _merge_metadata_lists(request_body.tags, inferred_metadata["tags"])
            source_refs = _merge_metadata_lists(request_body.source_refs, inferred_metadata["source_refs"])
            attachments = request_body.attachments
        else:
            topics = request_body.topics
            people = request_body.people
            sources = request_body.sources
            projects = request_body.projects
            tags = request_body.tags
            source_refs = request_body.source_refs
            attachments = request_body.attachments
        attachments = _merge_metadata_lists(
            attachments,
            attachment_service.save_uploads(_note_slug_from_title(request_body.title), request_body.attachment_uploads),
        )
        note = note_repository.save_draft(
            title=request_body.title,
            topics=topics,
            people=people,
            sources=sources,
            projects=projects,
            source_refs=source_refs,
            attachments=attachments,
            tags=tags,
            content=structured_content,
        )
        note_history_service.record_version(note, action="created")
        return note.model_dump()

    @app.put("/api/notes/{slug}")
    def update_note(slug: str, request_body: UpdateNoteRequest) -> dict:
        try:
            existing_note = note_repository.get_note(slug)
            if not note_history_service.list_versions(slug):
                note_history_service.record_version(existing_note, action="imported")
            attachments = _merge_metadata_lists(
                request_body.attachments,
                attachment_service.save_uploads(slug, request_body.attachment_uploads),
            )
            note = note_repository.update_note(
                slug=slug,
                title=request_body.title,
                topics=request_body.topics,
                people=request_body.people,
                sources=request_body.sources,
                projects=request_body.projects,
                source_refs=request_body.source_refs,
                attachments=attachments,
                tags=request_body.tags,
                content=request_body.content,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if _notes_differ(existing_note, note):
            note_history_service.record_version(note, action="updated")
        return note.model_dump()

    @app.delete("/api/notes/{slug}")
    def delete_note(slug: str) -> dict:
        try:
            note = note_repository.delete_note(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        attachment_service.delete_note_attachments(slug)
        note_history_service.delete_history(slug)
        return {"slug": slug, "deleted": True}

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
) -> DashboardSummary:
    notes = note_repository.list_notes()
    return DashboardSummary(
        total_notes=len(notes),
        ai_enabled=settings.ai_enabled,
    )


def _render_notes_page(
    request: Request,
    templates: Jinja2Templates,
    note_repository: NoteRepository,
    settings: Settings,
    q: str | None = None,
    topic: str | None = None,
    tag: str | None = None,
    person: str | None = None,
    source: str | None = None,
    project: str | None = None,
    created_since: str | None = None,
    view: str | None = None,
) -> HTMLResponse:
    view_mode = view if view in {"grid", "row"} else "grid"
    current_path = request.url.path
    if request.url.query:
        current_path = f"{current_path}?{request.url.query}"
    notes = note_repository.list_notes()
    all_notes = notes
    if q:
        search = q.lower().strip()
        notes = [
            note
            for note in notes
            if search in note.metadata.title.lower()
            or search in note.summary.lower()
            or search in note.raw_body.lower()
        ]
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
    if created_since:
        notes = [note for note in notes if note.metadata.created >= created_since]
    return templates.TemplateResponse(
        request,
        "notes.html",
        {
            "notes": notes,
            "total_notes": len(all_notes),
            "visible_notes": len(notes),
            "filter_options": _build_filter_options(all_notes),
            "ai_enabled": settings.ai_enabled,
            "title": "Notes",
            "view_mode": view_mode,
            "build_explore_href": _build_explore_href,
            "build_note_preview": _build_note_preview,
            "active_filters": {
                "q": q or "",
                "topic": topic or "",
                "tag": tag or "",
                "person": person or "",
                "source": source or "",
                "project": project or "",
                "created_since": created_since or "",
                "view": view_mode,
            },
            "return_to": current_path,
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


def _note_slug_from_title(title: str) -> str:
    return f"note-{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or 'untitled-note'}"


def _build_attachment_links(attachment_paths: list[str], attachment_service: AttachmentService) -> list[dict[str, str]]:
    return [
        {
            "label": attachment_service.display_name(path),
            "path": path,
            "href": attachment_service.build_link(path),
        }
        for path in attachment_paths
    ]


def _build_note_preview(text: str) -> str:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    preview = " ".join(sentences[:2]).strip()
    return preview or cleaned


def _build_filter_options(notes: list) -> dict[str, list[str]]:
    topics = _collect_sorted_values(notes, "topics")
    tags = _collect_sorted_values(notes, "tags")
    people = _collect_sorted_values(notes, "people")
    sources = _collect_sorted_values(notes, "sources")
    projects = _collect_sorted_values(notes, "projects")
    return {
        "topics": topics,
        "tags": tags,
        "people": people,
        "sources": sources,
        "projects": projects,
    }


def _collect_sorted_values(notes: list, attribute_name: str) -> list[str]:
    values: set[str] = set()
    for note in notes:
        for raw in getattr(note.metadata, attribute_name):
            cleaned = str(raw).strip()
            if cleaned:
                values.add(cleaned)
    return sorted(values, key=str.casefold)


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


def _build_version_history(versions: list, note_slug: str) -> list[ActivityEntry]:
    if not versions:
        return []
    entries: list[ActivityEntry] = []
    for index in range(len(versions) - 1, -1, -1):
        current = versions[index]
        previous = versions[index - 1] if index > 0 else None
        version_number = index + 1
        details = "; ".join(_summarize_version_change(previous, current))
        entries.append(
            ActivityEntry(
                timestamp=_format_activity_timestamp(current.timestamp),
                sort_timestamp=_normalize_activity_timestamp(current.timestamp),
                title=f"Version {version_number}",
                details=details,
                href=f"/notes/{note_slug}/history/{current.slug}",
            )
        )
    return entries


def _normalize_activity_timestamp(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat()


def _format_activity_timestamp(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    if parsed.tzinfo is None:
        return parsed.strftime("%b %d, %Y")
    return parsed.astimezone().strftime("%b %d, %Y, %I:%M %p")


def _summarize_version_change(previous_version, current_version) -> list[str]:
    if previous_version is None:
        return ["Initial version captured."]
    previous_note = previous_version.note
    current_note = current_version.note
    changes: list[str] = []
    if previous_note.metadata.title != current_note.metadata.title:
        changes.append(f"Retitled to {current_note.metadata.title}.")
    for label, attribute_name in (
        ("topics", "topics"),
        ("tags", "tags"),
        ("people", "people"),
        ("sources", "sources"),
        ("projects", "projects"),
        ("attachments", "attachments"),
    ):
        attribute_change = _summarize_list_change(
            getattr(previous_note.metadata, attribute_name),
            getattr(current_note.metadata, attribute_name),
            label,
        )
        if attribute_change:
            changes.append(attribute_change)
    if previous_note.summary.strip() != current_note.summary.strip():
        changes.append("Summary changed.")
    for label, attribute_name in (("key points", "key_points"), ("evidence", "evidence"), ("linked notes", "links")):
        if getattr(previous_note, attribute_name) != getattr(current_note, attribute_name):
            changes.append(f"{label.capitalize()} changed.")
    if previous_note.raw_body.strip() != current_note.raw_body.strip() and "Summary changed." not in changes:
        changes.append("Body content changed.")
    return changes[:3] or ["Minor content cleanup."]


def _summarize_list_change(previous_items: list[str], current_items: list[str], label: str) -> str:
    previous_set = set(previous_items)
    current_set = set(current_items)
    if previous_set == current_set:
        return ""
    added = sorted(current_set - previous_set)
    removed = sorted(previous_set - current_set)
    fragments: list[str] = []
    if added:
        fragments.append(f"added {', '.join(added[:2])}")
    if removed:
        fragments.append(f"removed {', '.join(removed[:2])}")
    if not fragments:
        return f"{label.capitalize()} reordered."
    return f"{label.capitalize()} {'; '.join(fragments)}."


def _notes_differ(previous_note, current_note) -> bool:
    if previous_note.raw_body != current_note.raw_body:
        return True
    return previous_note.metadata.model_dump() != current_note.metadata.model_dump()


def _safe_return_to(return_to: str | None) -> str:
    if not return_to:
        return "/notes"
    decoded = unquote(return_to).strip()
    if decoded.startswith("/notes") or decoded.startswith("/explore"):
        return decoded
    return "/notes"


def _related_notes_for(notes: list, current_note) -> list:
    scored_notes: list[tuple[int, object]] = []
    current_sets = {
        "topics": set(current_note.metadata.topics),
        "tags": set(current_note.metadata.tags),
        "people": set(current_note.metadata.people),
        "sources": set(current_note.metadata.sources),
        "projects": set(current_note.metadata.projects),
    }
    for note in notes:
        if note.slug == current_note.slug:
            continue
        score = 0
        for attribute_name, current_values in current_sets.items():
            if not current_values:
                continue
            score += len(current_values.intersection(getattr(note.metadata, attribute_name)))
        if score:
            scored_notes.append((score, note))
    scored_notes.sort(key=lambda item: (-item[0], item[1].metadata.title.casefold()))
    return [note for _, note in scored_notes[:5]]


def _build_draft_state(note) -> dict[str, object]:
    placeholder_key_points = {"Needs manual editing"}
    placeholder_evidence = {"Add supporting source"}
    visible_links = [
        link for link in note.links if link.title != "Add a linked note" and link.target != "./replace-linked-note.md"
    ]
    summary = note.summary.strip()
    return {
        "summary_is_placeholder": summary == "Draft content pending review.",
        "key_points": [item for item in note.key_points if item not in placeholder_key_points],
        "evidence": [item for item in note.evidence if item not in placeholder_evidence],
        "links": visible_links,
    }


app = create_app()
