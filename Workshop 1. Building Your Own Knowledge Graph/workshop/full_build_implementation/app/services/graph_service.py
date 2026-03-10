from __future__ import annotations

from collections import Counter
import re

from app.models import GraphEdge, GraphNode, GraphResponse, GraphStats, Note, NoteType


class GraphService:
    _METADATA_FIELDS = {
        "topic": "topics",
        "tag": "tags",
        "person": "people",
        "source": "sources",
        "project": "projects",
    }

    def build_graph(self, notes: list[Note]) -> GraphResponse:
        notes_by_slug = {note.slug: note for note in notes}
        nodes = [self._build_node(note) for note in sorted(notes, key=lambda item: item.metadata.title.casefold())]
        edges: list[GraphEdge] = []
        edges.extend(self._build_explicit_edges(notes, notes_by_slug))
        metadata_edges = self._build_metadata_edges(notes)
        edges.extend(metadata_edges)
        return GraphResponse(
            nodes=nodes,
            edges=sorted(edges, key=lambda edge: edge.id),
            stats=GraphStats(
                total_nodes=len(nodes),
                explicit_edges=sum(1 for edge in edges if edge.family == "explicit"),
                metadata_edges_by_type=dict(Counter(edge.label for edge in metadata_edges)),
            ),
        )

    def _build_node(self, note: Note) -> GraphNode:
        return GraphNode(
            id=note.slug,
            slug=note.slug,
            title=note.metadata.title,
            note_type=self._infer_note_type(note.slug),
            path=note.path,
            summary_preview=self._build_note_preview(note.summary or note.raw_body),
            topics=list(note.metadata.topics),
            tags=list(note.metadata.tags),
            people=list(note.metadata.people),
            sources=list(note.metadata.sources),
            projects=list(note.metadata.projects),
        )

    def _build_explicit_edges(self, notes: list[Note], notes_by_slug: dict[str, Note]) -> list[GraphEdge]:
        edges: list[GraphEdge] = []
        for note in notes:
            for link in note.links:
                target_slug = self._slug_from_target(link.target)
                if not target_slug or target_slug not in notes_by_slug:
                    continue
                edges.append(
                    GraphEdge(
                        id=f"explicit:{note.slug}:{link.relationship}:{target_slug}",
                        source=note.slug,
                        target=target_slug,
                        family="explicit",
                        label=link.relationship,
                        weight=1,
                    )
                )
        return edges

    def _build_metadata_edges(self, notes: list[Note]) -> list[GraphEdge]:
        edges: list[GraphEdge] = []
        sorted_notes = sorted(notes, key=lambda item: item.slug)
        for index, source_note in enumerate(sorted_notes):
            for target_note in sorted_notes[index + 1 :]:
                for field_slug, attribute_name in self._METADATA_FIELDS.items():
                    shared_values = sorted(
                        set(getattr(source_note.metadata, attribute_name)).intersection(
                            getattr(target_note.metadata, attribute_name)
                        ),
                        key=str.casefold,
                    )
                    if not shared_values:
                        continue
                    label = f"shared_{field_slug}"
                    edges.append(
                        GraphEdge(
                            id=f"metadata:{source_note.slug}:{label}:{target_note.slug}",
                            source=source_note.slug,
                            target=target_note.slug,
                            family="metadata",
                            label=label,
                            weight=len(shared_values),
                            shared_values=shared_values,
                        )
                    )
        return edges

    def _infer_note_type(self, slug: str) -> NoteType:
        prefix = slug.split("-", 1)[0]
        if prefix in {"concept", "source", "person", "project"}:
            return prefix
        return "note"

    def _build_note_preview(self, text: str) -> str:
        cleaned = " ".join((text or "").split())
        if not cleaned:
            return ""
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        preview = " ".join(sentences[:2]).strip()
        return preview or cleaned

    def _slug_from_target(self, target: str) -> str:
        cleaned = (target or "").strip()
        if not cleaned:
            return ""
        cleaned = cleaned.replace("\\", "/")
        if cleaned.endswith(".md"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.rsplit("/", 1)[-1]
        if cleaned.startswith("./"):
            cleaned = cleaned[2:]
        return cleaned.strip()
