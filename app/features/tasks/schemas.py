import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from app.features.tasks.errors import TaskErrorCode, TaskValidationError


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
            raise PydanticCustomError(
                TaskErrorCode.TASK_DUE_AT_TIMEZONE_REQUIRED.value,
                "due_at must include a timezone",
            )
        if value is not None and value.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            raise PydanticCustomError(
                TaskErrorCode.TASK_DUE_AT_IN_PAST.value,
                "due_at must be in the future",
            )
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


class TaskStatusFilter(str, Enum):
    all = "all"
    active = "active"
    done = "done"
    upcoming = "upcoming"


class TaskSortBy(str, Enum):
    title = "title"
    due_at = "due_at"
    status = "status"


class SortDirection(str, Enum):
    asc = "asc"
    desc = "desc"


class TaskPage(BaseModel):
    items: list[TaskRead]
    total: int
    page: int
    page_size: int
    total_pages: int


def validate_due_range(due_from: datetime | None, due_to: datetime | None) -> None:
    if (due_from is None) != (due_to is None):
        raise TaskValidationError(TaskErrorCode.TASK_DUE_RANGE_REQUIRED)
    if due_from is None or due_to is None:
        return
    if (
        due_from.tzinfo is None
        or due_from.utcoffset() is None
        or due_to.tzinfo is None
        or due_to.utcoffset() is None
    ):
        raise TaskValidationError(TaskErrorCode.TASK_DUE_RANGE_TIMEZONE_REQUIRED)
    if due_from >= due_to:
        raise TaskValidationError(TaskErrorCode.TASK_DUE_RANGE_ORDER_INVALID)
