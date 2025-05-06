import os
from rag_loader import retrieve_extra_explanation

def test_query(query: str):
    print(f"\n🔍 Query: {query}")
    results = retrieve_extra_explanation(query)
    print(f"✅ Retrieved {len(results)} result(s).\n")

    for i, chunk in enumerate(results):
        print(f"--- Chunk {i+1} ---\n{chunk}\n")

def show_indexed_chunks():
    chunks_dir = os.path.join(os.path.dirname(__file__), "data", "rag_chunks")
    if not os.path.exists(chunks_dir):
        print("⚠️ No rag_chunks directory found.")
        return

    print("\n📂 Preview of indexed chunks:")
    for file in os.listdir(chunks_dir):
        if file.endswith(".txt"):
            print(f"\n📄 {file}")
            with open(os.path.join(chunks_dir, file), 'r', encoding='utf-8') as f:
                chunks = f.read().split('\n\n')
                for i, chunk in enumerate(chunks[:3]):
                    print(f"--- Chunk {i+1} ---\n{chunk}\n")
            break  # Preview only the first file

if __name__ == "__main__":
    show_indexed_chunks()
    
    # Try different queries
    test_query("What is a buffer overflow?")
    test_query("Explain SQL injection")
    test_query("How does command injection work?")
