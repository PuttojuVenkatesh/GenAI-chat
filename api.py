import os
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from groq import APIError, Groq

from task4 import detect_intent, generate_response

app = FastAPI()
sessions: dict[UUID, list[dict[str, str]]] = {}
MAX_STORED_MESSAGES = 40

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    session_id: UUID
    message: str = Field(min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    session_id: UUID
    intent: str
    reply: str


class SessionResponse(BaseModel):
    session_id: UUID


@app.post("/sessions", response_model=SessionResponse)
def create_session() -> SessionResponse:
    session_id = uuid4()
    sessions[session_id] = []
    return SessionResponse(session_id=session_id)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    history = sessions.get(request.session_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Chat session not found. Start a new chat.")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured in the project .env file.",
        )

    intent = detect_intent(request.message)

    try:
        reply = generate_response(
            Groq(api_key=api_key),
            request.message,
            intent,
            history.copy(),
        )
    except APIError as error:
        raise HTTPException(
            status_code=502,
            detail="The Groq API request failed.",
        ) from error

    history.extend(
        [
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": reply},
        ]
    )
    del history[:-MAX_STORED_MESSAGES]

    return ChatResponse(session_id=request.session_id, intent=intent, reply=reply)
