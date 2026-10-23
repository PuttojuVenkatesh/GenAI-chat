
import os
import re
import sys

import instructor
from dotenv import load_dotenv
from groq import APIError, Groq
from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator

load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

class UserProfile(BaseModel):
    name: str = Field(min_length=2)
    age: int = Field(ge=18, le=100)
    email: EmailStr
    pan: str

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, value: str) -> str:
        if not re.fullmatch(r"^[A-Z]{5}[0-9]{4}[A-Z]$", value):
            raise ValueError("Invalid PAN format")
        return value


def main() -> int:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY is not configured. Add it to the project .env file.", file=sys.stderr)
        return 1

    client = instructor.from_groq(
        Groq(api_key=api_key),
        mode=instructor.Mode.JSON,
    )

    try:
        profile = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            response_model=UserProfile,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Create a fictional user profile with name Venkatesh, age 23, "
                        "email venkatesh@example.com, and PAN ABCDE1234F. "
                        "Return values matching the required schema."
                    ),
                }
            ],
        )
    except APIError as error:
        print(f"Groq API request failed: {error}", file=sys.stderr)
        return 1
    except ValidationError as error:
        print(f"The generated profile did not match the schema:\n{error}", file=sys.stderr)
        return 1

    print("Structured User Profile:")
    print(profile.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
