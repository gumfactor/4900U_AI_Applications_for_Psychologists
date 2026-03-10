from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RelationshipType = Literal["related_to", "supports", "contradicts", "applies_to", "mentions"]
AiTaskType = Literal["question_answering"]
GraphEdgeFamily = Literal["explicit", "metadata"]
NoteType = Literal["concept", "source", "person", "project", "note"]


class NoteMetadata(BaseModel):
    id: str
    title: str
    topics: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)
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


class AttachmentUpload(BaseModel):
    name: str
    content_base64: str


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


class ActivityEntry(BaseModel):
    timestamp: str
    sort_timestamp: str
    title: str
    details: str = ""
    href: str | None = None


class NoteVersion(BaseModel):
    slug: str
    note_slug: str
    timestamp: str
    action: str
    title: str
    path: str
    raw_markdown: str
    note: Note


class SaveDraftRequest(BaseModel):
    title: str
    topics: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)
    attachment_uploads: list[AttachmentUpload] = Field(default_factory=list)
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
    attachments: list[str] = Field(default_factory=list)
    attachment_uploads: list[AttachmentUpload] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    content: str


class DashboardSummary(BaseModel):
    total_notes: int
    ai_enabled: bool


class GraphNode(BaseModel):
    id: str
    slug: str
    title: str
    note_type: NoteType
    path: str
    summary_preview: str = ""
    topics: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    family: GraphEdgeFamily
    label: str
    weight: int = 1
    shared_values: list[str] = Field(default_factory=list)


class GraphStats(BaseModel):
    total_nodes: int
    explicit_edges: int
    metadata_edges_by_type: dict[str, int] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    stats: GraphStats
