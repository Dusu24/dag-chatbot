# api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import sys, os, json
sys.path.insert(0, os.path.abspath("."))

from retrieval.engine import search_chunks
from orchestration.llm_client import (
    format_book_title,
    expand_query,
    build_prompt,
    build_mode_prompt,
)
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Dag Heward-Mills Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class HistoryMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    history: Optional[list[HistoryMessage]] = []
    mode: Optional[str] = "chat"  # chat | devotion | sermon | study


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest):
    question = request.question
    mode = request.mode or "chat"
    history = [
        {"role": m.role, "content": m.content}
        for m in request.history
    ] if request.history else []

    # Expand query for better retrieval
    expanded = expand_query(question)

    # Search for relevant chunks
    chunks = search_chunks(question, top_k=6, expanded_query=expanded)

    # Format sources
    sources = [
        {
            "book": format_book_title(c["book_title"]),
            "chapter": c["chapter_title"],
            "excerpt": c["text"][:150] + "...",
        }
        for c in chunks
    ]

    # Build prompt based on mode
    if mode == "chat":
        messages = build_prompt(question, chunks, history)
    else:
        messages = build_mode_prompt(question, chunks, history, mode)

    def stream():
        # First send the sources as a JSON line
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

        # Then stream the answer token by token
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.4,
            max_tokens=1200,
            stream=True,
        )

        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                yield f"data: {json.dumps({'type': 'token', 'token': delta.content})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
