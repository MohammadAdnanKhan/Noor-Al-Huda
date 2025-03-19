# import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model.retriever import query_faiss
from model.generator import refine_with_gemini
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

app = FastAPI(
    title="IlmBot API",
    version="1.0",
    description="Seerat Chatbot API powered by FAISS & Gemini"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address, default_limits=["10 per 15 minutes"])
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

logging.basicConfig(level=logging.INFO)

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def home():
    return {"message": "IlmBot API is running!"}

@app.post("/chat/")
@limiter.limit("10/15minutes")
async def chat_with_bot(request: Request, query_request: QueryRequest):
    try:
        logging.info(f"Received query: {query_request.query}")

        heading, retrieved_text = query_faiss(query_request.query)

        if retrieved_text and retrieved_text.lower() != "no relevant results found.":
            refined_answer = refine_with_gemini(query_request.query, retrieved_text)
            return {
                "heading": heading,
                "retrieved_text": retrieved_text,
                "enhanced_response": refined_answer
            }

        return {
            "heading": None,
            "retrieved_text": "No relevant information found.",
            "enhanced_response": "No enhanced answer available."
        }

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return HTTPException(
        status_code=429,
        detail="Rate limit exceeded. You can make 10 requests every 15 minutes."
    )

# Ensure the app runs on Render's provided port
if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    load_dotenv()


    # Check if the PORT variable is loaded
    # port = int(os.getenv("PORT", 8000))
    # if not port:
        # print("PORT environment variable not loaded!")
    # else:
        # print(f"Loaded PORT: {port}")

    port = int(os.getenv("PORT", 8000))  # Render provides a PORT variable
    print(f"Loaded PORT: {port}")
    uvicorn.run(app, host='0.0.0.0', port=port)
