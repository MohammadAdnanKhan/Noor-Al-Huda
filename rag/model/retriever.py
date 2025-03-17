import os
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# ✅ Load the TXT file
file_path = "seerat.txt"  # Make sure this file exists

if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ File '{file_path}' not found. Please check the path.")

with open(file_path, "r", encoding="utf-8") as f:
    raw_text = f.read()

# ✅ Normalize spaces & fix unwanted line breaks
cleaned_text = re.sub(r"\s*\n\s*", "\n", raw_text).strip()

# ✅ Process structured data
structured_data = []
current_section = {"title": "", "content": ""}

# ✅ Detect uppercase headings
heading_pattern = re.compile(r"^\s*[A-Z][A-Z0-9 .,()'’-]{4,}\s*$")

# ✅ Split text by newlines
lines = cleaned_text.split("\n")

for line in lines:
    line = line.strip()
    if heading_pattern.fullmatch(line):  # Detect uppercase headings
        if current_section["title"] and current_section["content"].strip():
            structured_data.append(current_section)
        current_section = {"title": line, "content": ""}  # Start new section
    else:
        current_section["content"] += line + " "

# ✅ Append last section
if current_section["title"] and current_section["content"].strip():
    structured_data.append(current_section)

# ✅ Chunking text
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)

docs = []
for sec in structured_data:
    content = sec["content"].strip()
    if content:  # Ensure section has actual content
        chunks = text_splitter.split_text(content)
        for chunk in chunks:
            if len(chunk.strip()) > 50:
                docs.append(Document(page_content=chunk, metadata={"heading": sec["title"]}))

# ✅ Load multilingual embedding model
embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base")

# ✅ Path to FAISS index
FAISS_INDEX_PATH = "faiss_index"

# ✅ Load or create FAISS
if os.path.exists(FAISS_INDEX_PATH):
    db = FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)
    print("✅ FAISS index loaded from disk.")
else:
    db = FAISS.from_documents(docs, embedding=embedding_model)
    db.save_local(FAISS_INDEX_PATH)  # Save FAISS to disk
    print("✅ FAISS index created and saved.")

# ✅ Query function
def query_faiss(query, num_results=3):
    """Retrieve top-k results from FAISS and extract relevant sentences."""
    retrieved_results = db.similarity_search_with_score(query, k=num_results)

    if not retrieved_results:
        return "Unknown", "No relevant results found."

    best_match, score = retrieved_results[0]

    if score > 0.1:  # Ensure relevance
        full_text = best_match.page_content

        # ✅ Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', full_text.strip())

        # ✅ Find first relevant sentence and include all following ones
        start_index = next((i for i, s in enumerate(sentences) if any(word in s.lower() for word in query.lower().split())), 0)
        final_output = " ".join(sentences[start_index:])

        return best_match.metadata["heading"], final_output

    return "Unknown", "No relevant results found."


# ✅ Test Query
if __name__ == "__main__":
    heading, result = query_faiss("How did the Quraysh torture Muslims?")
    print(f"\n🔹 **Title:** {heading}\n📖 **Content:** {result}")
