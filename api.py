import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from groq import APIError, Groq

from task4 import detect_intent, generate_response

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class ChatMessage(BaseModel):
    role: str = Field(pattern=r"^(user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=8)


class ChatResponse(BaseModel):
    intent: str
    reply: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured in the project .env file.",
        )

    intent = detect_intent(request.message)
    history = [item.model_dump() for item in request.history]

    try:
        reply = generate_response(
            Groq(api_key=api_key),
            request.message,
            intent,
            history,
        )
    except APIError as error:
        raise HTTPException(status_code=502, detail="The Groq API request failed.") from error

    return ChatResponse(intent=intent, reply=reply)
