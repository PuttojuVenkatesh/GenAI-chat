import os
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import APIError, Groq
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from task4 import detect_intent, generate_response

load_dotenv()

app = FastAPI()
mongo_client = MongoClient(
    os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017"),
    serverSelectionTimeoutMS=3000,
)
chats = mongo_client[os.getenv("MONGODB_DATABASE", "genai_chat")]["chats"]
MAX_STORED_MESSAGES = 40

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    session_id: UUID
    message: str = Field(min_length=1, max_length=8000)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatResponse(BaseModel):
    session_id: UUID
    intent: str
    reply: str


class SessionResponse(BaseModel):
    session_id: UUID


class SessionSummary(BaseModel):
    session_id: UUID
    title: str
    updated_at: str


class SessionDetail(SessionSummary):
    messages: list[ChatMessage]


def database_unavailable() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=(
            "MongoDB is unavailable. Start MongoDB or check MONGODB_URI "
            "in the project .env file."
        ),
    )


@app.post("/sessions", response_model=SessionResponse)
def create_session() -> SessionResponse:
    session_id = uuid4()
    now = datetime.now(timezone.utc).isoformat()
    try:
        chats.insert_one(
            {
                "_id": str(session_id),
                "title": "New chat",
                "messages": [],
                "created_at": now,
                "updated_at": now,
            }
        )
    except PyMongoError as error:
        raise database_unavailable() from error
    return SessionResponse(session_id=session_id)


@app.get("/sessions", response_model=list[SessionSummary])
def list_sessions() -> list[SessionSummary]:
    try:
        documents = chats.find(
            {"messages.0": {"$exists": True}},
            {"messages": 0},
        )
        sessions = list(documents)
    except PyMongoError as error:
        raise database_unavailable() from error

    sessions.sort(key=lambda session: session["updated_at"], reverse=True)
    return [
        SessionSummary(
            session_id=UUID(session["_id"]),
            title=session["title"],
            updated_at=session["updated_at"],
        )
        for session in sessions[:100]
    ]


@app.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: UUID) -> SessionDetail:
    try:
        session = chats.find_one({"_id": str(session_id)})
    except PyMongoError as error:
        raise database_unavailable() from error
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    return SessionDetail(
        session_id=session_id,
        title=session["title"],
        updated_at=session["updated_at"],
        messages=session["messages"],
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        session = chats.find_one({"_id": str(request.session_id)})
    except PyMongoError as error:
        raise database_unavailable() from error
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found. Start a new chat.")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured in the project .env file.",
        )

    stored_messages = session["messages"]
    history = [
        {"role": message["role"], "content": message["content"]}
        for message in stored_messages[-MAX_STORED_MESSAGES:]
    ]
    intent = detect_intent(request.message)

    try:
        reply = generate_response(
            Groq(api_key=api_key),
            request.message,
            intent,
            history,
        )
    except APIError as error:
        raise HTTPException(
            status_code=502,
            detail="The Groq API request failed.",
        ) from error

    now = datetime.now(timezone.utc).isoformat()
    title = session["title"]
    if not stored_messages:
        title = request.message[:57].rstrip()
        if len(request.message) > 57:
            title += "..."

    try:
        chats.update_one(
            {"_id": str(request.session_id)},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "content": request.message},
                            {"role": "assistant", "content": reply},
                        ]
                    }
                },
                "$set": {"title": title, "updated_at": now},
            },
        )
    except PyMongoError as error:
        raise database_unavailable() from error

    return ChatResponse(session_id=request.session_id, intent=intent, reply=reply)
