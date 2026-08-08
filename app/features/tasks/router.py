import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.features.auth.models import User
from app.features.auth.router import current_active_user
from app.features.tasks.schemas import TaskCreate, TaskRead, TaskUpdate
from app.features.tasks.service import (
    create_task,
    delete_task,
    get_owned_task,
    list_tasks,
    update_task_schedule,
    update_task_status,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def read_tasks(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    return await list_tasks(session, user.id)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def add_task(
    payload: TaskCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    return await create_task(session, user.id, payload.title, payload.due_at)


@router.patch("/{task_id}", response_model=TaskRead)
async def set_task_status(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    task = await get_owned_task(session, user.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if payload.is_done is not None:
        task = await update_task_status(session, task, payload.is_done)
    if "due_at" in payload.model_fields_set:
        task = await update_task_schedule(session, task, payload.due_at)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_task(
    task_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    task = await get_owned_task(session, user.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await delete_task(session, task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
