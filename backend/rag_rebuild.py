import os
from rag import RagBuilder

def rebuild_faiss_if_needed():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    index_path = os.path.join(base, "faiss_index")
    chunk_folder = os.path.join(base, "rag_chunks")

    os.makedirs(base, exist_ok=True)

    pdfs = [f for f in os.listdir(base) if f.lower().endswith('.pdf')]
    chunks_exist = os.path.exists(chunk_folder) and len(os.listdir(chunk_folder)) >= len(pdfs)

    if not os.path.exists(index_path) or not chunks_exist:
        print("🛠️ Rebuilding FAISS index.")
        builder = RagBuilder(base_folder=base)
        for pdf_file in pdfs:
            pdf_path = os.path.join(base, pdf_file)
            builder.process_pdf(pdf_path)
        builder.build_faiss_index(index_path)
        print("✅ Rebuild complete.")
    else:
        print("✅ FAISS index is up-to-date.")

if __name__ == "__main__":
    rebuild_faiss_if_needed()
