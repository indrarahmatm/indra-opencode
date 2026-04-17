import os
import json
import numpy as np
import faiss
import ollama

from ingest import load_index, embed_texts

LLM_MODEL = "gemma4"
TOP_K = 5


def retrieve(query_embedding: list[float], store_dir: str, top_k: int = TOP_K) -> dict:
    index, docs = load_index(store_dir)

    if index is None or not docs:
        return {"documents": [], "metadatas": [], "distances": []}

    query = np.array([query_embedding], dtype=np.float32)
    norm = np.linalg.norm(query)
    if norm > 0:
        query = query / norm

    k = min(top_k, index.ntotal)
    distances, indices = index.search(query, k)

    documents = []
    metadatas = []
    dists = []

    for i, idx in enumerate(indices[0]):
        if idx == -1:
            continue
        doc = docs[idx]
        documents.append(doc["text"])
        metadatas.append({
            "filename": doc.get("filename", "unknown"),
            "filepath": doc.get("filepath", ""),
            "chunk_index": doc.get("chunk_index", 0),
        })
        dists.append(float(distances[0][i]))

    return {
        "documents": documents,
        "metadatas": metadatas,
        "distances": dists,
    }


def build_prompt(query: str, contexts: list[str], sources: list[str]) -> str:
    context_block = "\n\n---\n\n".join(
        f"[Source: {s}]\n{c}" for c, s in zip(contexts, sources)
    )
    prompt = f"""You are a helpful assistant. Answer the user's question based ONLY on the provided context. If the context doesn't contain enough information to answer, say so clearly.

Context:
{context_block}

---

Question: {query}

Answer:"""
    return prompt


def generate_answer(prompt: str, model: str = LLM_MODEL) -> str:
    resp = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 8192},
    )
    return resp["message"]["content"]


def ask_question(question: str, store_dir: str, top_k: int = TOP_K) -> dict:
    embeddings = embed_texts([question])
    query_embedding = embeddings[0]

    results = retrieve(query_embedding, store_dir, top_k)

    if not results["documents"]:
        return {
            "answer": "Tidak ditemukan dokumen yang relevan dengan pertanyaan kamu.",
            "sources": [],
        }

    documents = results["documents"]
    metadatas = results["metadatas"]
    distances = results["distances"]

    sources = [m.get("filename", "unknown") for m in metadatas]

    prompt = build_prompt(question, documents, sources)
    answer = generate_answer(prompt)

    return {
        "answer": answer,
        "sources": [
            {
                "filename": m.get("filename", "unknown"),
                "filepath": m.get("filepath", ""),
                "distance": round(d, 4),
                "chunk_index": m.get("chunk_index", 0),
            }
            for m, d in zip(metadatas, distances)
        ],
    }
