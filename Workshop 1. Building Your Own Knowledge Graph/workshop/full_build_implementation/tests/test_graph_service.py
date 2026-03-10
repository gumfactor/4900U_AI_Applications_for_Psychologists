from app.models import Note, NoteLink, NoteMetadata
from app.services.graph_service import GraphService


def build_note(
    slug: str,
    title: str,
    *,
    topics: list[str] | None = None,
    tags: list[str] | None = None,
    people: list[str] | None = None,
    sources: list[str] | None = None,
    projects: list[str] | None = None,
    links: list[NoteLink] | None = None,
) -> Note:
    return Note(
        metadata=NoteMetadata(
            id=slug,
            title=title,
            topics=topics or [],
            people=people or [],
            sources=sources or [],
            projects=projects or [],
            tags=tags or [],
            source_refs=[],
            attachments=[],
            created="2026-03-08",
            updated="2026-03-08",
        ),
        slug=slug,
        path=f"data/notes/{slug}.md",
        raw_body="## Summary\n\nExample note.",
        summary="Example note.",
        links=links or [],
    )


def test_graph_service_builds_explicit_edges_from_linked_notes() -> None:
    service = GraphService()
    notes = [
        build_note(
            "concept-alpha",
            "Alpha",
            links=[NoteLink(relationship="supports", title="Beta", target="./concept-beta.md")],
        ),
        build_note("concept-beta", "Beta"),
    ]

    graph = service.build_graph(notes)

    assert len(graph.nodes) == 2
    explicit_edges = [edge.model_dump() for edge in graph.edges if edge.family == "explicit"]
    assert explicit_edges == [
        {
            "id": "explicit:concept-alpha:supports:concept-beta",
            "source": "concept-alpha",
            "target": "concept-beta",
            "family": "explicit",
            "label": "supports",
            "weight": 1,
            "shared_values": [],
        }
    ]


def test_graph_service_builds_metadata_edges_once_per_pair_and_type() -> None:
    service = GraphService()
    notes = [
        build_note(
            "concept-alpha",
            "Alpha",
            topics=["Memory", "Attention"],
            tags=["study"],
            projects=["Instructor Demo System"],
        ),
        build_note(
            "concept-beta",
            "Beta",
            topics=["Memory", "Attention"],
            tags=["study"],
            projects=["Instructor Demo System"],
        ),
    ]

    graph = service.build_graph(notes)

    metadata_edges = [edge for edge in graph.edges if edge.family == "metadata"]
    assert len(metadata_edges) == 3
    topic_edge = next(edge for edge in metadata_edges if edge.label == "shared_topic")
    assert topic_edge.weight == 2
    assert topic_edge.shared_values == ["Attention", "Memory"]
    assert graph.stats.metadata_edges_by_type == {
        "shared_project": 1,
        "shared_tag": 1,
        "shared_topic": 1,
    }


def test_graph_service_keeps_isolated_notes_and_skips_empty_metadata_edges() -> None:
    service = GraphService()
    notes = [
        build_note("concept-alpha", "Alpha"),
        build_note("note-lonely", "Lonely"),
    ]

    graph = service.build_graph(notes)

    assert sorted(node.slug for node in graph.nodes) == ["concept-alpha", "note-lonely"]
    assert graph.edges == []
    assert graph.stats.total_nodes == 2
    assert graph.stats.metadata_edges_by_type == {}
