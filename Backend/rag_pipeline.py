"""
rag_pipeline.py — Full RAG pipeline: document loading, chunking,
embedding, index building/loading, retrieval, and LLM generation.
This is the complete pipeline as an importable module for main.py.
"""

import os
import re
import requests
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv(override=True)
GROQ_API_KEY = os.getenv("GROQ_API_KEY").strip()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HAZARD_DIR = os.path.join(BASE_DIR, "..", "hazard")
FAISS_PATH = os.path.join(BASE_DIR, "faiss_hazard_index")

_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# -------------------------------------------------
# STEP 1-2: Load .txt files and split into paragraph chunks
# -------------------------------------------------
def load_and_chunk_by_paragraph(directory):
    chunks = []
    for filename in os.listdir(directory):
        if not filename.endswith(".txt"):
            continue
        zone_name = filename.replace(".txt", "").replace("_", " ").title()
        filepath = os.path.join(directory, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        body = content.split("=" * 60, 1)[-1].strip()
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        for para in paragraphs:
            chunks.append(Document(page_content=para, metadata={"zone": zone_name}))
    return chunks


# -------------------------------------------------
# STEP 3-4: Build embeddings + FAISS index from chunks
# -------------------------------------------------
def build_or_load_vectorstore():
    index_file = os.path.join(FAISS_PATH, "index.faiss")

    if os.path.exists(index_file):
        print("Loading existing FAISS index...")
        return FAISS.load_local(
            FAISS_PATH, _embeddings, allow_dangerous_deserialization=True
        )

    print("No existing index found — building a new one from hazard_docs...")
    chunks = load_and_chunk_by_paragraph(HAZARD_DIR)
    chunks = [
        c for c in chunks
        if "HAZARD BRIEFING" not in c.page_content and len(c.page_content.strip()) > 20
    ]
    print(f"Total clean chunks: {len(chunks)}")

    vs = FAISS.from_documents(chunks, _embeddings)
    os.makedirs(FAISS_PATH, exist_ok=True)
    vs.save_local(FAISS_PATH)
    print("FAISS index built and saved.")
    return vs


# Built/loaded ONCE when this module is imported by main.py
vectorstore = build_or_load_vectorstore()


# -------------------------------------------------
# STEP 5: Retriever — zone-filtered similarity search
# -------------------------------------------------
def retrieve_hazards(zone, query, k_search=50, k_return=3):
    results = vectorstore.similarity_search(query, k=k_search)
    zone_matches = [r for r in results if r.metadata["zone"] == zone][:k_return]
    return zone_matches


def call_llm(prompt):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def rewrite_with_context(query, history):
    history_text = "\n".join([f"{h['role']}: {h['content']}" for h in history[-4:]])
    prompt = f"""Given this conversation history, rewrite the latest
user message into a complete, standalone question that includes all
necessary context. Output ONLY the rewritten question.

History:
{history_text}

Latest message: {query}
"""
    return call_llm(prompt)


def get_hazard_briefing(zone, query, history=None):
    history = history or []

    standalone_query = rewrite_with_context(query, history) if history else query

    retrieved_chunks = retrieve_hazards(zone, standalone_query)
    context = "\n\n".join([c.page_content for c in retrieved_chunks])

    history_text = "\n".join([f"{h['role']}: {h['content']}" for h in history[-4:]])

    prompt = f"""You are a trip-safety assistant for Sundarban tourists.
Zone: {zone}

Recent conversation:
{history_text}

Answer ONLY using the facts below, which are specific to {zone}.
Do not invent any risk, statistic, or recommendation not explicitly
stated in the context.

The user may write in informal English mixed with local words (like WhatsApp chat).
Understand the meaning and answer in clear simple English.
If needed, you may include a few common local terms, but keep the answer easy to read.

If the context does not cover what the user asked, answer naturally
and briefly using whatever related information IS available, without
using phrases like "the information provided" or "the context does
not include." Just speak plainly, e.g. "I don't have winter-specific
weather details for {zone}, but..."

CONTEXT (specific to {zone}):
{context}

QUESTION: {standalone_query}

Answer in 2-4 sentences, warm and practical, naming {zone} explicitly.
"""
    answer = call_llm(prompt)

    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": answer})

    return answer, history