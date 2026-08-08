import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.features.tasks.models import Task
from app.features.tasks.schemas import SortDirection, TaskSortBy, TaskStatusFilter


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
) -> tuple[list[Task], int]:
    conditions = [Task.owner_id == owner_id]
    if search:
        escaped_search = (
            search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        if escaped_search:
            conditions.append(Task.title.ilike(f"%{escaped_search}%", escape="\\"))
    if status_filter == TaskStatusFilter.active:
        conditions.append(Task.is_done.is_(False))
    elif status_filter == TaskStatusFilter.done:
        conditions.append(Task.is_done.is_(True))
    elif status_filter == TaskStatusFilter.upcoming:
        conditions.extend(
            [Task.is_done.is_(False), Task.due_at > datetime.now(timezone.utc)]
        )
    if due_from is not None:
        conditions.append(Task.due_at >= due_from)
    if due_to is not None:
        conditions.append(Task.due_at <= due_to)

    count_result = await session.execute(
        select(func.count()).select_from(Task).where(*conditions)
    )
    total = count_result.scalar_one()

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
    return list(result.scalars().all()), total


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


async def delete_task(session: AsyncSession, task: Task) -> None:
    await session.delete(task)
    await session.commit()
