from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.analysis import research_opportunities
from src.graph_store import GraphStore
from src.schema import ENTITY_TYPES

st.set_page_config(page_title="Halophyte Research Graph", page_icon="🌿", layout="wide")


@st.cache_resource
def get_store() -> GraphStore:
    return GraphStore()


store = get_store()

st.title("Halophyte Research Knowledge Graph")
st.caption("Phase 4 · Literature evidence, graph exploration and research-gap discovery")

with st.sidebar:
    st.header("Graph controls")
    if st.button("Load demonstration graph", use_container_width=True):
        store.seed_demo()
        st.cache_data.clear()
        st.success("Demonstration graph loaded.")
    page = st.radio("View", ["Overview", "Evidence explorer", "Graph map", "Research opportunities", "Review queue"])
    st.divider()
    st.caption("Evidence rule: every literature edge needs a source paper, exact supporting text and a review status.")

counts = store.dashboard_counts()
if counts["nodes"] == 0:
    st.info("Start by loading the demonstration graph in the left panel, or build a corpus with the command-line workflow.")

if page == "Overview":
    cols = st.columns(4)
    for col, (label, value) in zip(cols, [("Provenance records", counts["papers"]), ("Entities", counts["nodes"]), ("Relationships", counts["edges"]), ("Pending review", counts["pending"])]):
        col.metric(label, value)
    st.subheader("How this strengthens the full Halophyte project")
    st.markdown("""
    - **Phase 1 — Dictionary:** validated species, mechanism and GR50 records can be imported as the project-data backbone.
    - **Phase 2 — Prediction:** model outputs stay clearly labelled as predictions; graph evidence explains which mechanisms, genes and papers are related to the selected species.
    - **Phase 3 — Dashboard:** this interface adds literature exploration, citation inspection and defensible research-gap analysis.
    - **Phase 4 — Knowledge Graph:** the new evidence layer links the project to real scientific literature and makes its scope wider and more research-oriented.
    """)
    st.subheader("Data-quality safeguard")
    st.warning("Demo seed items are intentionally marked as demonstration/review records. Only approved or manually reviewed evidence should be used in results tables or to support a scientific claim.")

elif page == "Evidence explorer":
    left, right = st.columns([1, 2])
    with left:
        query = st.text_input("Find an entity")
        node_type = st.selectbox("Entity type", ["All", *sorted(ENTITY_TYPES)])
        matches = store.search(query, node_type)
        labels = {row["id"]: f"{row['display_name']} · {row['node_type']}" for row in matches}
        selected = st.selectbox("Entity", options=list(labels), format_func=labels.get) if labels else None
    with right:
        if selected:
            node, edges = store.node_details(selected)
            st.subheader(node["display_name"])
            st.caption(node["node_type"])
            if not edges:
                st.info("No evidence relationships recorded yet.")
            for edge in edges:
                direction = "→" if edge["source_id"] == selected else "←"
                other = edge["target_name"] if edge["source_id"] == selected else edge["source_name"]
                st.markdown(f"**{direction} {edge['relation_type']} {other}**  ")
                st.caption(f"Status: {edge['review_status']} · confidence: {edge['confidence']:.2f}")
                st.write(f'“{edge["evidence_quote"]}”')
                if edge["paper_url"]:
                    st.link_button(f"Open {edge['paper_external_id']}", edge["paper_url"])
                st.divider()

elif page == "Graph map":
    edges = store.graph_edges()
    if edges:
        lines = ["digraph {", "rankdir=LR;", 'node [shape=box, style="rounded,filled", fillcolor="#edf7ed", color="#609966"];']
        seen = set()
        for edge in edges:
            for label, kind in ((edge["source_name"], edge["source_type"]), (edge["target_name"], edge["target_type"])):
                key = (label, kind)
                if key not in seen:
                    seen.add(key)
                    lines.append(f'"{label}" [tooltip="{kind}"];')
            lines.append(f'"{edge["source_name"]}" -> "{edge["target_name"]}" [label="{edge["relation_type"]}"];')
        lines.append("}")
        st.graphviz_chart("\n".join(lines), use_container_width=True)
        st.caption("The graph map is a navigator. Open an entity in Evidence explorer to inspect the supporting paper and text.")
    else:
        st.info("No graph relationships available.")

elif page == "Research opportunities":
    results = research_opportunities(store)
    st.subheader("Ranked evidence-coverage leads")
    st.caption("Scores rank visible graph gaps only. They do not establish novelty, causal biology or suitability for agricultural use.")
    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
    else:
        st.info("Add approved/demonstration/dataset relationships to generate transparent coverage leads.")

elif page == "Review queue":
    queued = [edge for edge in store.graph_edges() if edge["review_status"] in {"pending", "needs_source_review"}]
    st.subheader("Manual review queue")
    if not queued:
        st.success("There are no pending LLM-extracted relationships.")
    for edge in queued:
        st.markdown(f"**{edge['source_name']} — {edge['relation_type']} → {edge['target_name']}**")
        st.caption(f'Confidence {edge["confidence"]:.2f} · {edge["paper_external_id"] or "No paper"}')
        st.write(f'“{edge["evidence_quote"]}”')
        a, b = st.columns(2)
        if a.button("Approve", key=f"approve-{edge['id']}"):
            store.set_review_status(edge["id"], "approved")
            st.rerun()
        if b.button("Reject", key=f"reject-{edge['id']}"):
            store.set_review_status(edge["id"], "rejected")
            st.rerun()
        st.divider()
