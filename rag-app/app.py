import os
import json
import streamlit as st
from pathlib import Path

from ingest import ingest_files, ingest_folder
from query import ask_question

STORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_store")
SUPPORTED_EXT = {".pdf", ".docx", ".xlsx", ".csv", ".txt"}


st.set_page_config(page_title="RAG - Local Document QA", page_icon="🔍", layout="wide")

st.title("RAG - Local Document QA")
st.caption("Tanya jawab dengan dokumen lokal menggunakan Ollama + FAISS")


if "messages" not in st.session_state:
    st.session_state.messages = []


def count_documents():
    docs_path = os.path.join(STORE_DIR, "docs.json")
    if os.path.exists(docs_path):
        with open(docs_path, "r") as f:
            return len(json.load(f))
    return 0


with st.sidebar:
    st.header("Data Management")

    doc_count = count_documents()
    st.metric("Indexed Chunks", doc_count)

    st.subheader("Upload Files")
    uploaded = st.file_uploader(
        "Upload dokumen",
        type=["pdf", "docx", "xlsx", "csv", "txt"],
        accept_multiple_files=True,
    )

    if uploaded:
        import tempfile
        tmp_files = []
        for f in uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(f.name).suffix) as tmp:
                tmp.write(f.getvalue())
                tmp_files.append(tmp.name)

        with st.spinner(f"Processing {len(tmp_files)} file(s)..."):
            result = ingest_files(tmp_files, STORE_DIR)
            st.success(f"Done: {result['processed']} processed, {result['chunks']} chunks")
            for tf in tmp_files:
                try:
                    os.unlink(tf)
                except Exception:
                    pass

    st.subheader("Index Folder")
    folder_path = st.text_input("Path folder dokumen", value="/home/indra/Documents")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Index Folder"):
            if os.path.isdir(folder_path):
                with st.spinner(f"Scanning {folder_path}..."):
                    result = ingest_folder(folder_path, STORE_DIR)
                    st.success(
                        f"Done: {result['processed']} processed, "
                        f"{result['skipped']} skipped, "
                        f"{result['errors']} errors, "
                        f"{result['chunks']} total chunks"
                    )
            else:
                st.error("Folder tidak ditemukan")
    with col2:
        if st.button("Reindex All"):
            if os.path.isdir(folder_path):
                with st.spinner("Reindexing..."):
                    result = ingest_folder(folder_path, STORE_DIR, replace=True)
                    st.success(
                        f"Done: {result['processed']} processed, "
                        f"{result['chunks']} total chunks"
                    )
            else:
                st.error("Folder tidak ditemukan")

    if st.button("Clear All Data"):
        for fname in ["index.faiss", "docs.json"]:
            fpath = os.path.join(STORE_DIR, fname)
            if os.path.exists(fpath):
                os.remove(fpath)
        st.success("All data cleared")

    st.divider()
    st.caption("Models: gemma4 (LLM) + nomic-embed-text (Embedding)")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg:
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.write(f"📄 **{s['filename']}** (distance: {s['distance']})")
                    if s["filepath"]:
                        st.caption(s["filepath"])


if prompt := st.chat_input("Tanya sesuatu tentang dokumen kamu..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if count_documents() == 0:
        with st.chat_message("assistant"):
            st.warning("Belum ada dokumen yang di-index. Upload file atau index folder di sidebar.")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Mencari jawaban..."):
                try:
                    result = ask_question(prompt, STORE_DIR)
                    st.markdown(result["answer"])
                    with st.expander("Sources"):
                        for s in result["sources"]:
                            st.write(f"📄 **{s['filename']}** (distance: {s['distance']})")
                            if s["filepath"]:
                                st.caption(s["filepath"])
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result["sources"],
                    })
                except Exception as e:
                    st.error(f"Error: {e}")
