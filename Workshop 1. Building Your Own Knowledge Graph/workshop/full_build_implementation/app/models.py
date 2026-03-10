from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RelationshipType = Literal["related_to", "supports", "contradicts", "applies_to", "mentions"]
AiTaskType = Literal["source_summary", "metadata_extraction", "related_note_suggestion", "question_answering"]


class NoteMetadata(BaseModel):
    id: str
    title: str
    topics: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    created: str
    updated: str


class NoteLink(BaseModel):
    relationship: RelationshipType
    title: str
    target: str


class Note(BaseModel):
    metadata: NoteMetadata
    slug: str
    path: str
    raw_body: str
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    linked_notes_markdown: str = ""
    links: list[NoteLink] = Field(default_factory=list)


class SourceDocument(BaseModel):
    slug: str
    title: str
    path: str
    content: str


class PromptTemplate(BaseModel):
    slug: str
    title: str
    path: str
    content: str


class AiTaskRequest(BaseModel):
    task: AiTaskType
    model: str | None = None
    source_slug: str | None = None
    note_slugs: list[str] = Field(default_factory=list)
    question: str | None = None
    prompt_slug: str | None = None


class AiTaskResult(BaseModel):
    task: AiTaskType
    model: str
    prompt_slug: str
    prompt_text: str
    output_text: str
    input_paths: list[str] = Field(default_factory=list)
    log_path: str | None = None


class AiLogEntry(BaseModel):
    slug: str
    timestamp: str
    task: str
    prompt_slug: str
    model: str
    input_files: list[str] = Field(default_factory=list)
    output_target: str
    review_outcome: str
    notes: str = ""
    raw_content: str = ""


class SaveDraftRequest(BaseModel):
    title: str
    topics: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    content: str


class InferMetadataRequest(BaseModel):
    title: str
    content: str
    source_refs: list[str] = Field(default_factory=list)


class InferMetadataResponse(BaseModel):
    topics: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    ai_enabled: bool
    model: str | None = None
    prompt_slug: str | None = None


class UpdateNoteRequest(BaseModel):
    title: str
    topics: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    content: str


class DashboardSummary(BaseModel):
    total_notes: int
    total_sources: int
    total_logs: int
    ai_enabled: bool
