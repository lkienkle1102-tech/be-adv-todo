import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.features.tasks.models import Task


async def list_tasks(session: AsyncSession, owner_id: uuid.UUID) -> list[Task]:
    result = await session.execute(
        select(Task)
        .where(Task.owner_id == owner_id)
        .order_by(Task.is_done, Task.due_at.asc().nulls_last(), Task.title)
    )
    return list(result.scalars().all())


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
