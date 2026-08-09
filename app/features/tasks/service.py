import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import and_, func, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.features.tasks.models import Task
from app.features.tasks.schemas import SortDirection, TaskSortBy, TaskStatusFilter


@dataclass(frozen=True)
class TaskCounts:
    total: int
    completed: int
    incomplete: int
    filtered_all: int
    filtered_active: int
    filtered_done: int
    filtered_upcoming: int


async def list_tasks(
    session: AsyncSession,
    owner_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    status_filter: TaskStatusFilter = TaskStatusFilter.all,
    sort_by: TaskSortBy = TaskSortBy.due_at,
    sort_direction: SortDirection = SortDirection.asc,
    due_from: datetime | None = None,
    due_to: datetime | None = None,
) -> tuple[list[Task], TaskCounts]:
    filter_conditions = []
    if search:
        escaped_search = (
            search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        if escaped_search:
            filter_conditions.append(Task.title.ilike(f"%{escaped_search}%", escape="\\"))
    if due_from is not None:
        filter_conditions.append(Task.due_at >= due_from)
    if due_to is not None:
        filter_conditions.append(Task.due_at <= due_to)

    now = datetime.now(timezone.utc)
    status_conditions = {
        TaskStatusFilter.all: true(),
        TaskStatusFilter.active: Task.is_done.is_(False),
        TaskStatusFilter.done: Task.is_done.is_(True),
        TaskStatusFilter.upcoming: and_(Task.is_done.is_(False), Task.due_at > now),
    }
    filtered_scope = and_(*filter_conditions) if filter_conditions else true()
    count_result = await session.execute(
        select(
            func.count().label("total"),
            func.count().filter(Task.is_done.is_(True)).label("completed"),
            func.count().filter(Task.is_done.is_(False)).label("incomplete"),
            func.count().filter(filtered_scope).label("filtered_all"),
            func.count()
            .filter(and_(filtered_scope, status_conditions[TaskStatusFilter.active]))
            .label("filtered_active"),
            func.count()
            .filter(and_(filtered_scope, status_conditions[TaskStatusFilter.done]))
            .label("filtered_done"),
            func.count()
            .filter(and_(filtered_scope, status_conditions[TaskStatusFilter.upcoming]))
            .label("filtered_upcoming"),
        )
        .select_from(Task)
        .where(Task.owner_id == owner_id)
    )
    count_row = count_result.one()
    counts = TaskCounts(
        total=count_row.total,
        completed=count_row.completed,
        incomplete=count_row.incomplete,
        filtered_all=count_row.filtered_all,
        filtered_active=count_row.filtered_active,
        filtered_done=count_row.filtered_done,
        filtered_upcoming=count_row.filtered_upcoming,
    )

    conditions = [Task.owner_id == owner_id, *filter_conditions]
    if status_filter == TaskStatusFilter.active:
        conditions.append(Task.is_done.is_(False))
    elif status_filter == TaskStatusFilter.done:
        conditions.append(Task.is_done.is_(True))
    elif status_filter == TaskStatusFilter.upcoming:
        conditions.append(status_conditions[TaskStatusFilter.upcoming])

    sort_column = {
        TaskSortBy.title: Task.title,
        TaskSortBy.due_at: Task.due_at,
        TaskSortBy.status: Task.is_done,
    }[sort_by]
    ordering = sort_column.asc() if sort_direction == SortDirection.asc else sort_column.desc()
    if sort_by == TaskSortBy.due_at:
        ordering = ordering.nulls_last()

    result = await session.execute(
        select(Task)
        .where(*conditions)
        .order_by(ordering, Task.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), counts


async def create_task(
    session: AsyncSession,
    owner_id: uuid.UUID,
    title: str,
    due_at: datetime | None = None,
) -> Task:
    task = Task(owner_id=owner_id, title=title, due_at=due_at)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def get_owned_task(
    session: AsyncSession, owner_id: uuid.UUID, task_id: uuid.UUID
) -> Task | None:
    result = await session.execute(
        select(Task).where(Task.id == task_id, Task.owner_id == owner_id)
    )
    return result.scalar_one_or_none()


async def update_task_status(
    session: AsyncSession, task: Task, is_done: bool
) -> Task:
    task.is_done = is_done
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def update_task_schedule(
    session: AsyncSession, task: Task, due_at: datetime | None
) -> Task:
    task.due_at = due_at
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def update_task_details(
    session: AsyncSession,
    task: Task,
    *,
    title: str | None,
    due_at: datetime | None,
    update_due_at: bool,
) -> Task:
    if title is not None:
        task.title = title
    if update_due_at:
        task.due_at = due_at
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, task: Task) -> None:
    await session.delete(task)
    await session.commit()
