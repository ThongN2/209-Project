import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'backend', 'data')

rag_model = SentenceTransformer('all-MiniLM-L6-v2')
index_path = os.path.join(DATA_DIR, 'faiss_index')

if os.path.exists(index_path):
    rag_index = faiss.read_index(index_path)
    chunk_files = [os.path.join(DATA_DIR, 'rag_chunks', f) for f in os.listdir(os.path.join(DATA_DIR, 'rag_chunks')) if f.endswith('.txt')]
    rag_chunks = []
    for file in chunk_files:
        with open(file, 'r', encoding='utf-8') as f:
            rag_chunks += f.read().split('\n\n')
else:
    rag_index = None
    rag_chunks = []

def retrieve_extra_explanation(query: str, top_k: int = 3):
    if not rag_index:
        return []
    query_vec = rag_model.encode([query])
    D, I = rag_index.search(np.array(query_vec, dtype=np.float32), k=top_k)
    return [rag_chunks[i] for i in I[0] if i < len(rag_chunks)]
