import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import json

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'backend', 'data')

# Load embedding model
rag_model = SentenceTransformer('all-MiniLM-L6-v2')

# Load FAISS index and chunks
index_path = os.path.join(DATA_DIR, 'faiss_index')

if os.path.exists(index_path):
    rag_index = faiss.read_index(index_path)

    chunk_dir = os.path.join(DATA_DIR, 'rag_chunks')
    chunk_files = [os.path.join(chunk_dir, f) for f in os.listdir(chunk_dir) if f.endswith('.txt')]

    rag_chunks = []
    for file in chunk_files:
        with open(file, 'r', encoding='utf-8') as f:
            chunks = f.read().split('\n\n')
            rag_chunks += [c.strip() for c in chunks if len(c.strip()) > 50]
else:
    rag_index = None
    rag_chunks = []

# Retrieve top-k relevant chunks
def retrieve_extra_explanation(query: str, top_k: int = 3):
    if not rag_index:
        return []

    query = query.strip()
    query_vec = rag_model.encode([query])
    D, I = rag_index.search(np.array(query_vec, dtype=np.float32), k=top_k)
    return [rag_chunks[i] for i in I[0] if i < len(rag_chunks)]

# Summarize each chunk separately with OpenAI
def summarize_chunk_with_openai(chunk: str, query: str, key: str, model="gpt-3.5-turbo"):
    client = OpenAI(api_key=key)
    prompt = f"""You are a cybersecurity expert. Based on the context below, answer the question in no more than 2 simple sentences.

Context:
{chunk}

Question: {query}

Answer:"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ OpenAI error: {e}"

# Full public interface
def get_simplified_answers(query: str, top_k: int = 3):
    try:
        with open("openai_config.json", "r") as f:
            key = json.load(f)["api_key"]
    except Exception as e:
        return [f"🔒 OpenAI API key error: {e}"]

    chunks = retrieve_extra_explanation(query, top_k=top_k)
    if not chunks:
        return ["⚠️ No relevant information found."]

    summaries = []
    for chunk in chunks:
        summary = summarize_chunk_with_openai(chunk, query, key)
        summaries.append(summary)

    return summaries

# Manual test
if __name__ == "__main__":
    query = "What is buffer overflow?"
    results = get_simplified_answers(query)
    print("\n🔍 Simplified Results:")
    for i, res in enumerate(results, 1):
        print(f"\nResult {i}:\n{res}")
