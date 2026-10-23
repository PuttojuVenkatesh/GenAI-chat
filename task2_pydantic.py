
import re
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ValidationError,
    field_validator,
)


# Define the structure and rules for a user profile
class UserProfile(BaseModel):
    name: str = Field(min_length=2)
    age: int = Field(ge=18, le=100)
    email: EmailStr
    pan: str

    # Custom validation for Indian PAN format
    @field_validator("pan")
    @classmethod
    def validate_pan(cls, value: str) -> str:
        pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"

        if not re.fullmatch(pattern, value):
            raise ValueError("Invalid PAN format")

        return value


# Test 1: Valid input
print("TEST 1: VALID DATA")

try:
    user = UserProfile(
        name="Venkatesh",
        age=23,
        email="venkatesh@example.com",
        pan="ABCDE1234F",
    )

    print(user.model_dump_json(indent=2))

except ValidationError as error:
    print("Validation failed:")
    print(error)


# Test 2: Invalid input
print("\nTEST 2: INVALID DATA")

try:
    user = UserProfile(
        name="V",
        age=15,
        email="venkat@gmail.com",
        pan="123456",
    )

    print(user.model_dump_json(indent=2))

except ValidationError as error:
    print("Validation failed:")
    print(error)
