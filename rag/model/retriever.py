import os
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

file_path = "seerat.txt"  

if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ File '{file_path}' not found. Please check the path.")

with open(file_path, "r", encoding="utf-8") as f:
    raw_text = f.read()

cleaned_text = re.sub(r"\s*\n\s*", "\n", raw_text).strip()

structured_data = []
current_section = {"title": "", "content": ""}

heading_pattern = re.compile(r"^\s*[A-Z][A-Z0-9 .,()'’-]{4,}\s*$")

lines = cleaned_text.split("\n")

for line in lines:
    line = line.strip()
    if heading_pattern.fullmatch(line):  
        if current_section["title"] and current_section["content"].strip():
            structured_data.append(current_section)
        current_section = {"title": line, "content": ""} 
    else:
        current_section["content"] += line + " "

if current_section["title"] and current_section["content"].strip():
    structured_data.append(current_section)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)

docs = []
for sec in structured_data:
    content = sec["content"].strip()
    if content:  
        chunks = text_splitter.split_text(content)
        for chunk in chunks:
            if len(chunk.strip()) > 50:
                docs.append(Document(page_content=chunk, metadata={"heading": sec["title"]}))

embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base")

FAISS_INDEX_PATH = "faiss_index"

if os.path.exists(FAISS_INDEX_PATH):
    db = FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)
    print("✅ FAISS index loaded from disk.")
else:
    db = FAISS.from_documents(docs, embedding=embedding_model)
    db.save_local(FAISS_INDEX_PATH)  
    print("✅ FAISS index created and saved.")

def query_faiss(query, num_results=3):
    """Retrieve top-k results from FAISS and extract relevant sentences."""
    retrieved_results = db.similarity_search_with_score(query, k=num_results)

    if not retrieved_results:
        return "Unknown", "No relevant results found."

    best_match, score = retrieved_results[0]

    if score > 0.1:  
        full_text = best_match.page_content

        sentences = re.split(r'(?<=[.!?])\s+', full_text.strip())

        start_index = next((i for i, s in enumerate(sentences) if any(word in s.lower() for word in query.lower().split())), 0)
        final_output = " ".join(sentences[start_index:])

        return best_match.metadata["heading"], final_output

    return "Unknown", "No relevant results found."


if __name__ == "__main__":
    heading, result = query_faiss("How did the Quraysh torture Muslims?")
    print(f"\n🔹 **Title:** {heading}\n📖 **Content:** {result}")
