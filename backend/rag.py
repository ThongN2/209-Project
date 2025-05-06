import os
import faiss
import re
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import numpy as np

class RagBuilder:
    def __init__(self, base_folder: str):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.base_folder = base_folder
        self.chunk_folder = os.path.join(base_folder, 'rag_chunks')
        os.makedirs(self.chunk_folder, exist_ok=True)
        self.chunks = []

    def clean_text(self, text: str) -> str:
        text = re.sub(r'COMPUTER ENGINEERING CMPE 209 Dr\.Park\d* Running Footer.*', '', text)
        text = re.sub(r'Page \d+.*', '', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()

    def split_into_chunks(self, text: str, max_length: int = 500) -> list:
        paragraphs = text.split('\n')
        chunks = []
        current_chunk = ''
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current_chunk) + len(para) <= max_length:
                current_chunk += ' ' + para
            else:
                chunks.append(current_chunk.strip())
                current_chunk = para
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    def process_pdf(self, pdf_path: str):
        reader = PdfReader(pdf_path)
        full_text = ''
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + '\n'
        clean = self.clean_text(full_text)
        chunks = self.split_into_chunks(clean)
        self.chunks.extend(chunks)

        base_name = os.path.basename(pdf_path).replace('.pdf', '_chunks.txt')
        save_path = os.path.join(self.chunk_folder, base_name)
        with open(save_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(chunk + '\n\n')
        print(f"✅ Processed and saved chunks: {save_path}")

    def build_faiss_index(self, index_save_path: str):
        embeddings = self.model.encode(self.chunks)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(np.array(embeddings, dtype=np.float32))
        faiss.write_index(index, index_save_path)
        print(f"✅ Saved FAISS index: {index_save_path}")

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(__file__), "data")
    builder = RagBuilder(base_folder=base)

    builder.process_pdf(os.path.join(base, 'Malware.pdf'))
    builder.process_pdf(os.path.join(base, 'BufferOverFlow.pdf'))

    builder.build_faiss_index(os.path.join(base, "faiss_index"))
