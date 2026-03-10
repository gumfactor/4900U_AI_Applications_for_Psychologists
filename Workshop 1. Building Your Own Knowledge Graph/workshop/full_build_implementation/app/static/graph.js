(function () {
    const canvas = document.getElementById("graph-canvas");
    if (!canvas) {
        return;
    }

    const searchInput = document.getElementById("graph-search");
    const summary = document.getElementById("graph-summary");
    const libraryWarning = document.getElementById("graph-library-warning");
    const emptyDetail = document.getElementById("graph-detail-empty");
    const nodeDetail = document.getElementById("graph-node-detail");
    const edgeDetail = document.getElementById("graph-edge-detail");
    const nodeTypeInputs = Array.from(document.querySelectorAll('input[name="note-type"]'));
    const explicitEdgeInputs = Array.from(document.querySelectorAll('input[name="explicit-edge"]'));
    const metadataEdgeInputs = Array.from(document.querySelectorAll('input[name="metadata-edge"]'));

    const state = {
        graph: null,
        network: null,
        allNodes: [],
        allEdges: []
    };

    function escapeHtml(value) {
        return String(value || "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function colorForType(noteType) {
        switch (noteType) {
            case "concept":
                return "#2f6b50";
            case "source":
                return "#70503a";
            case "person":
                return "#355c94";
            case "project":
                return "#91463f";
            default:
                return "#5b6475";
        }
    }

    function labelForEdge(edge) {
        if (edge.family === "metadata") {
            return `${edge.label} (${edge.weight})`;
        }
        return edge.label;
    }

    function graphNode(node) {
        return {
            id: node.id,
            label: node.title,
            value: 14 + node.tags.length + node.topics.length,
            color: {
                background: colorForType(node.note_type),
                border: "#1f2430",
                highlight: { background: colorForType(node.note_type), border: "#1f2430" }
            },
            font: { color: "#fff", face: "Georgia" },
            shape: "dot",
            note_type: node.note_type,
            slug: node.slug,
            title: `${node.title} (${node.note_type})`
        };
    }

    function graphEdge(edge) {
        const isMetadata = edge.family === "metadata";
        return {
            id: edge.id,
            from: edge.source,
            to: edge.target,
            label: labelForEdge(edge),
            arrows: isMetadata ? "" : "to",
            width: isMetadata ? Math.min(6, 1 + edge.weight) : 2,
            color: isMetadata ? { color: "#9e8f74", opacity: 0.55 } : { color: "#0b6e4f", opacity: 0.95 },
            dashes: isMetadata,
            smooth: { enabled: true, type: "dynamic" }
        };
    }

    function selectedValues(inputs) {
        return new Set(inputs.filter((input) => input.checked).map((input) => input.value));
    }

    function renderNodeDetail(node) {
        nodeDetail.innerHTML = `
            <h4>${escapeHtml(node.title)}</h4>
            <p class="muted-text">${escapeHtml(node.note_type)} note</p>
            <p>${escapeHtml(node.summary_preview || "No summary available.")}</p>
            <p><a href="/notes/${encodeURIComponent(node.slug)}">Open note</a></p>
            <div class="attribute-chip-group">
                ${node.topics.map((value) => `<span class="attribute-chip topic">${escapeHtml(value)}</span>`).join("")}
                ${node.tags.map((value) => `<span class="attribute-chip tag">${escapeHtml(value)}</span>`).join("")}
                ${node.people.map((value) => `<span class="attribute-chip person">${escapeHtml(value)}</span>`).join("")}
                ${node.sources.map((value) => `<span class="attribute-chip source">${escapeHtml(value)}</span>`).join("")}
                ${node.projects.map((value) => `<span class="attribute-chip project">${escapeHtml(value)}</span>`).join("")}
            </div>
        `;
    }

    function renderEdgeDetail(edge) {
        const sharedValues = edge.shared_values && edge.shared_values.length
            ? `<p><strong>Shared values:</strong> ${escapeHtml(edge.shared_values.join(", "))}</p>`
            : "";
        edgeDetail.innerHTML = `
            <h4>${escapeHtml(edge.label)}</h4>
            <p class="muted-text">${escapeHtml(edge.family)} edge</p>
            <p><strong>Source:</strong> <a href="/notes/${encodeURIComponent(edge.source)}">${escapeHtml(edge.source)}</a></p>
            <p><strong>Target:</strong> <a href="/notes/${encodeURIComponent(edge.target)}">${escapeHtml(edge.target)}</a></p>
            <p><strong>Weight:</strong> ${edge.weight}</p>
            ${sharedValues}
        `;
    }

    function setSelection(type, payload) {
        emptyDetail.classList.toggle("hidden", Boolean(payload));
        nodeDetail.classList.toggle("hidden", type !== "node");
        edgeDetail.classList.toggle("hidden", type !== "edge");
        if (type === "node" && payload) {
            renderNodeDetail(payload);
        }
        if (type === "edge" && payload) {
            renderEdgeDetail(payload);
        }
    }

    function applyFilters() {
        if (!state.graph || !state.network) {
            return;
        }

        const allowedNodeTypes = selectedValues(nodeTypeInputs);
        const allowedExplicitLabels = selectedValues(explicitEdgeInputs);
        const allowedMetadataLabels = selectedValues(metadataEdgeInputs);
        const query = String(searchInput?.value || "").trim().toLowerCase();

        const typeFilteredNodes = state.graph.nodes.filter((node) => allowedNodeTypes.has(node.note_type));
        const typeFilteredNodeIds = new Set(typeFilteredNodes.map((node) => node.id));

        let visibleEdges = state.graph.edges.filter((edge) => {
            if (!typeFilteredNodeIds.has(edge.source) || !typeFilteredNodeIds.has(edge.target)) {
                return false;
            }
            if (edge.family === "explicit") {
                return allowedExplicitLabels.has(edge.label);
            }
            return allowedMetadataLabels.has(edge.label);
        });

        let visibleNodeIds = new Set(typeFilteredNodes.map((node) => node.id));
        if (query) {
            const matchedIds = new Set(
                typeFilteredNodes
                    .filter((node) => node.title.toLowerCase().includes(query) || node.slug.toLowerCase().includes(query))
                    .map((node) => node.id)
            );
            visibleEdges = visibleEdges.filter((edge) => matchedIds.has(edge.source) || matchedIds.has(edge.target));
            visibleNodeIds = new Set();
            visibleEdges.forEach((edge) => {
                visibleNodeIds.add(edge.source);
                visibleNodeIds.add(edge.target);
            });
            matchedIds.forEach((id) => visibleNodeIds.add(id));
        }

        const visibleNodes = typeFilteredNodes.filter((node) => visibleNodeIds.has(node.id));
        state.network.setData({
            nodes: visibleNodes.map(graphNode),
            edges: visibleEdges.map(graphEdge)
        });
        summary.textContent = `${visibleNodes.length} nodes, ${visibleEdges.length} edges visible`;

        if (query && visibleNodes.length === 1) {
            state.network.focus(visibleNodes[0].id, { scale: 1.15, animation: true });
        } else if (visibleNodes.length > 0) {
            state.network.fit({ animation: true });
        }
        setSelection(null, null);
    }

    async function init() {
        if (!window.vis || !window.vis.Network) {
            libraryWarning.classList.remove("hidden");
            summary.textContent = "Graph library unavailable";
            return;
        }

        const response = await fetch(canvas.dataset.graphEndpoint || "/api/graph");
        if (!response.ok) {
            summary.textContent = "Could not load graph data";
            return;
        }

        state.graph = await response.json();
        state.network = new window.vis.Network(
            canvas,
            {
                nodes: [],
                edges: []
            },
            {
                autoResize: true,
                physics: {
                    barnesHut: {
                        gravitationalConstant: -3000,
                        springLength: 165,
                        springConstant: 0.035
                    },
                    stabilization: { iterations: 150 }
                },
                interaction: {
                    hover: true,
                    navigationButtons: true
                },
                nodes: {
                    borderWidth: 2
                },
                edges: {
                    font: {
                        face: "Consolas",
                        size: 11,
                        align: "middle"
                    }
                }
            }
        );

        state.allNodes = state.graph.nodes;
        state.allEdges = state.graph.edges;

        state.network.on("click", function (params) {
            if (params.nodes.length) {
                const selectedNode = state.graph.nodes.find((node) => node.id === params.nodes[0]);
                setSelection("node", selectedNode);
                return;
            }
            if (params.edges.length) {
                const selectedEdge = state.graph.edges.find((edge) => edge.id === params.edges[0]);
                setSelection("edge", selectedEdge);
                return;
            }
            setSelection(null, null);
        });

        state.network.on("doubleClick", function (params) {
            if (!params.nodes.length) {
                return;
            }
            const selectedNode = state.graph.nodes.find((node) => node.id === params.nodes[0]);
            if (selectedNode) {
                window.location.href = `/notes/${encodeURIComponent(selectedNode.slug)}`;
            }
        });

        [searchInput, ...nodeTypeInputs, ...explicitEdgeInputs, ...metadataEdgeInputs].forEach((element) => {
            element?.addEventListener("input", applyFilters);
            element?.addEventListener("change", applyFilters);
        });

        applyFilters();
    }

    init().catch(function () {
        summary.textContent = "Could not initialize graph";
    });
})();
