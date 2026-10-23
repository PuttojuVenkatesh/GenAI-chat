import os
import sys
from dotenv import load_dotenv
from groq import APIError, Groq

load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise SystemExit("GROQ_API_KEY is not configured. Add it to the project .env file.")

client = Groq(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": "Explain generative AI in one sentence and give a real-world example.",
            }
        ],
    )
except APIError as error:
    raise SystemExit(f"Groq API request failed: {error}") from error

print(response.choices[0].message.content or "(The model returned an empty response.)")