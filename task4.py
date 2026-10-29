
import os
import re

from dotenv import load_dotenv
from groq import APIError, Groq

load_dotenv()


# TASK 1: Basic intent detection
def detect_intent(message: str) -> str:
    text = message.lower()

    if re.search(r"\b(hello|hi|hey)\b", text):
        return "greeting"

    if re.search(r"\b(profile|name|age|email|pan)\b", text):
        return "profile_help"

    return "general_question"


# TASK 3: Send conversation history to Groq
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
                "You are a helpful conversational AI assistant. "
                "Answer the latest message directly and naturally. "
                "Use previous messages when relevant. "
                f"The detected intent is '{intent}'. "
                "Do not mention the intent label."
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
            "GROQ_API_KEY is missing. Check your .env file."
        )

    client = Groq(api_key=api_key)

    # TASK 2: Store a separate history for every session ID.
    conversations: dict[str, list[dict[str, str]]] = {}

    current_session = "session_1"
    conversations[current_session] = []

    print("Conversation Memory Chatbot")
    print("Commands:")
    print("  /session <id>  - Switch or create a session")
    print("  /sessions      - Show session IDs")
    print("  /quit          - Exit")

    while True:
        user_message = input(
            f"\n[{current_session}] You: "
        ).strip()

        if not user_message:
            continue

        if user_message.lower() == "/quit":
            break

        # Switch sessions without mixing their histories.
        if user_message.startswith("/session "):
            new_session = user_message[len("/session "):].strip()

            if not new_session:
                print("Please provide a session ID.")
                continue

            current_session = new_session

            if current_session not in conversations:
                conversations[current_session] = []
                print(f"Created new session: {current_session}")
            else:
                print(f"Switched to session: {current_session}")

            continue

        if user_message == "/sessions":
            print("Available sessions:", list(conversations.keys()))
            continue

        intent = detect_intent(user_message)

        # Retrieve history for the current session only.
        history = conversations[current_session]

        try:
            reply = generate_response(
                client,
                user_message,
                intent,
                history,
            )

        except APIError as error:
            print(f"Groq API request failed: {error}")
            continue

        print(f"Assistant: {reply}")

        # Save both messages after a successful API response.
        history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": reply},
        ])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
