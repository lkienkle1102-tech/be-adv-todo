import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field
from pydantic_core import PydanticCustomError

from app.features.tasks.errors import TaskErrorCode, TaskValidationError


def normalize_task_title(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def validate_task_due_at(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise PydanticCustomError(
            TaskErrorCode.TASK_DUE_AT_TIMEZONE_REQUIRED.value,
            "due_at must include a timezone",
        )
    if value.astimezone(timezone.utc) <= datetime.now(timezone.utc):
        raise PydanticCustomError(
            TaskErrorCode.TASK_DUE_AT_IN_PAST.value,
            "due_at must be in the future",
        )
    return value


TaskTitle = Annotated[
    str,
    BeforeValidator(normalize_task_title),
    Field(min_length=1, max_length=200),
]
TaskDueAt = Annotated[datetime, AfterValidator(validate_task_due_at)]


class TaskCreate(BaseModel):
    title: TaskTitle
    due_at: TaskDueAt | None = None


class TaskUpdate(BaseModel):
    title: TaskTitle | None = None
    is_done: bool | None = None
    due_at: TaskDueAt | None = None


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


class TaskSummary(BaseModel):
    total: int
    completed: int
    incomplete: int


class TaskStatusCounts(BaseModel):
    all: int
    active: int
    done: int
    upcoming: int


class TaskPage(BaseModel):
    items: list[TaskRead]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: TaskSummary
    status_counts: TaskStatusCounts


def validate_due_range(due_from: datetime | None, due_to: datetime | None) -> None:
    values = (value for value in (due_from, due_to) if value is not None)
    if any(value.tzinfo is None or value.utcoffset() is None for value in values):
        raise TaskValidationError(TaskErrorCode.TASK_DUE_RANGE_TIMEZONE_REQUIRED)
    if due_from is not None and due_to is not None and due_from >= due_to:
        raise TaskValidationError(TaskErrorCode.TASK_DUE_RANGE_ORDER_INVALID)
