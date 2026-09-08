"""Streamlit UI for upload, grounded facts, evidence, relationships, and review."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from src.config import settings
from src.database import Database
from src.pipeline import FactKnowledgePipeline

st.set_page_config(page_title="Fact Knowledge Layer", page_icon="🔎", layout="wide")
db = Database(settings.database_file(ROOT))
pipeline = FactKnowledgePipeline(db, settings)

st.title("🔎 Fact Knowledge Layer")
st.caption("Grounded facts from PDFs - compared with context, not just string matching.")
page = st.sidebar.radio("Navigate", ["Upload / Process", "Facts", "Evidence", "Relationships", "Review / Failures"])

if page == "Upload / Process":
    uploads = st.file_uploader("Choose one or more PDFs", type=["pdf"], accept_multiple_files=True)
    if uploads and st.button("Process PDFs", type="primary"):
        upload_dir = Path(os.getenv("FACT_LAYER_UPLOAD_DIR", Path(tempfile.gettempdir()) / "fact-layer-uploads")); upload_dir.mkdir(parents=True, exist_ok=True)
        for uploaded in uploads:
            safe_path = upload_dir / Path(uploaded.name).name
            safe_path.write_bytes(uploaded.getvalue())
            with st.status(f"Processing {uploaded.name}", expanded=True) as status:
                try:
                    result = pipeline.process_pdf(safe_path)
                    status.update(label=f"{uploaded.name}: {result['status']} ({result['facts']} facts)", state="complete")
                except Exception as error:
                    status.update(label=f"{uploaded.name}: failed", state="error")
                    st.exception(error)
    docs = db.documents()
    st.subheader("Documents")
    st.dataframe(pd.DataFrame(docs), use_container_width=True, hide_index=True) if docs else st.info("No documents processed yet.")

elif page == "Facts":
    facts = db.facts(); query = st.text_input("Search subject, predicate, value, or document")
    rows = [{"ID": f.fact_id, "Subject": f.subject, "Predicate": f.predicate, "Value": f.value, "Normalized": f.normalized_value, "Time": f.time, "Scope": f.scope, "Confidence": f.confidence, "Document": f.source_document, "Page": f.source_page, "Needs review": f.needs_review} for f in facts]
    if query: rows = [row for row in rows if query.casefold() in " ".join(map(str, row.values())).casefold()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Evidence":
    facts = db.facts()
    if not facts: st.info("Process a PDF first.")
    else:
        selected = st.selectbox("Select fact", facts, format_func=lambda f: f"{f.subject} - {f.predicate}: {f.value} ({f.source_document}, p. {f.source_page})")
        st.json(selected.model_dump(mode="json"), expanded=False)
        st.subheader(f"Source: {selected.source_document}, page {selected.source_page}")
        st.success(selected.evidence)
        st.caption(f"Extraction confidence: {selected.confidence:.0%}" + (" - Needs review" if selected.needs_review else ""))

elif page == "Relationships":
    rows = db.relationships()
    icons = {"CORROBORATED": "✅", "CONTRADICTION": "❌", "CONTEXTUALIZED": "⚠️", "UNCERTAIN": "❓", "UNRELATED": "↔️"}
    if not rows: st.info("No cross-document candidate relationships found yet.")
    for row in rows:
        with st.expander(f"{icons.get(row['relationship'], '')} {row['relationship']} - {row['a_subject']} / {row['a_predicate']}"):
            st.write(f"**Why:** {row['reason']}")
            left, right = st.columns(2)
            left.markdown(f"**A - {row['a_document']}, p. {row['a_page']}**\n\n{row['a_evidence']}")
            right.markdown(f"**B - {row['b_document']}, p. {row['b_page']}**\n\n{row['b_evidence']}")

else:
    review = [f for f in db.facts() if f.needs_review]
    st.subheader("Facts needing human review")
    if review:
        st.dataframe(pd.DataFrame([{"Subject": f.subject, "Predicate": f.predicate, "Value": f.value, "Confidence": f.confidence, "Notes": f.extraction_notes, "Document": f.source_document, "Page": f.source_page, "Evidence": f.evidence} for f in review]), use_container_width=True, hide_index=True)
    else: st.success("No low-confidence facts are currently flagged.")

