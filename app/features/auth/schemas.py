import uuid
import unicodedata
from typing import Annotated, Any

from fastapi_users import schemas
from pydantic import BaseModel, BeforeValidator, Field, StringConstraints


def normalize_username(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    normalized = unicodedata.normalize("NFC", value).strip()
    if any(unicodedata.category(character) in {"Cc", "Cs"} for character in normalized):
        raise ValueError("username contains control characters")
    return normalized


Username = Annotated[
    str,
    BeforeValidator(normalize_username),
    StringConstraints(min_length=3, max_length=50),
]


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: Username


class UserCreate(schemas.BaseUserCreate):
    username: Username


class UserUpdate(schemas.BaseUserUpdate):
    username: Username | None = None
    password: None = None


class PasswordUpdate(schemas.BaseUserUpdate):
    pass


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)
