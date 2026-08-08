import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    due_at: datetime | None = None

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("due_at")
    @classmethod
    def require_due_at_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("due_at must include a timezone")
        if value is not None and value.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError("due_at must be in the future")
        return value


class TaskUpdate(BaseModel):
    is_done: bool | None = None
    due_at: datetime | None = None

    @field_validator("due_at")
    @classmethod
    def require_due_at_timezone(cls, value: datetime | None) -> datetime | None:
        return TaskCreate.require_due_at_timezone(value)


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    is_done: bool
    due_at: datetime | None
