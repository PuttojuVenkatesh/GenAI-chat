import os
import re

from dotenv import load_dotenv
from groq import APIError, Groq

load_dotenv()


def detect_intent(message: str) -> str:
    text = message.lower()

    if re.search(r"\b(hello|hi|hey)\b", text):
        return "greeting"
    if re.search(r"\b(profile|name|age|email|pan)\b", text):
        return "profile_help"
    return "general_question"


def generate_response(
    client: Groq,
    message: str,
    intent: str,
    history: list[dict[str, str]],
) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful, conversational AI assistant. Answer the "
                "latest user message directly and naturally, using earlier "
                "messages when relevant. The detected intent is "
                f"'{intent}'; use it to understand the request, but do not "
                "mention the intent label. Keep simple answers concise. Use "
                "Markdown headings, lists, or fenced code blocks when they "
                "make a longer answer easier to read; avoid unnecessary "
                "formatting for short answers."
            ),
        },
        *history[-8:],
        {"role": "user", "content": message},
    ]

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
    )
    return response.choices[0].message.content or ""


def main() -> int:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise SystemExit(
            "GROQ_API_KEY is not configured. Add it to the project .env file."
        )

    client = Groq(api_key=api_key)
    history: list[dict[str, str]] = []

    print("Chat started. Type 'quit' to exit.")
    while True:
        user_message = input("You: ").strip()
        if user_message.lower() == "quit":
            break
        if not user_message:
            continue

        intent = detect_intent(user_message)
        try:
            reply = generate_response(client, user_message, intent, history)
        except APIError as error:
            print(f"Groq API request failed: {error}")
            continue

        print(f"Assistant: {reply}")
        history.extend(
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": reply},
            ]
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
