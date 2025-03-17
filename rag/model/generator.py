import os
import re
import google.generativeai as genai  
from model.retriever import query_faiss  

from dotenv import load_dotenv

load_dotenv()  
api_key = os.getenv("api_key")

if not api_key:
    raise ValueError("❌ Gemini API key not found. Set it as an environment variable.")

genai.configure(api_key=api_key)
def refine_with_gemini(query, retrieved_text):
    """Enhance FAISS output using Google Gemini"""
    model = genai.GenerativeModel("gemini-1.5-pro")  

    truncated_text = retrieved_text[:3000]  

    prompt = f"""You are an AI historian named IlmBot, specializing in the life and teachings of Prophet Muhammad (PBUH).
Based on the query and retrieved content, provide a well-structured and engaging response.

- Do not introduce yourself unless explicitly asked.
- If the retrieved content does not fully match the query, prioritize answering the query accurately without mentioning retrieval mistakes.
- Ensure the response is concise, informative, and maintains historical accuracy.

**Query:** {query}
**Context:** {truncated_text}

Craft your response with clarity and relevance.
"""

    response = model.generate_content(prompt)
    
    if response and hasattr(response, "text") and response.text:
        return response.text.strip()
    
    return "I'm unable to generate an answer at the moment."

def query_chatbot(query):
    score, heading, retrieved_text = query_faiss(query)  

    if retrieved_text != "No relevant results found.":
        refined_answer = refine_with_gemini(query, retrieved_text) 
        return score, retrieved_text, refined_answer
    else:
        return score, "No relevant information found.", "No enhanced answer available."

if __name__ == "__main__":
    query = "What was the first revelation received by Prophet Muhammad?"
    score, retrieved, answer = query_chatbot(query)
    
    print(f"\n🔹 **FAISS Score:** {score}")
    print(f"📖 **Retrieved Text:** {retrieved}")
    print(f"🤖 **IlmBot's Answer:** {answer}")
