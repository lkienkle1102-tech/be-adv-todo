import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.features.auth.models import User
from app.features.auth.router import current_active_user
from app.features.tasks.errors import TaskErrorCode, TaskValidationError
from app.features.tasks.schemas import (
    SortDirection,
    TaskCreate,
    TaskPage,
    TaskRead,
    TaskSortBy,
    TaskStatusFilter,
    TaskUpdate,
    validate_due_range,
)
from app.features.tasks.service import (
    create_task,
    delete_task,
    get_owned_task,
    list_tasks,
    update_task_details,
    update_task_status,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskPage)
async def read_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    task_status: TaskStatusFilter = Query(default=TaskStatusFilter.all, alias="status"),
    sort_by: TaskSortBy = Query(default=TaskSortBy.due_at),
    sort_direction: SortDirection = Query(default=SortDirection.asc),
    due_from: datetime | None = Query(default=None),
    due_to: datetime | None = Query(default=None),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        validate_due_range(due_from, due_to)
    except TaskValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error.code,
        ) from error

    tasks, total = await list_tasks(
        session,
        user.id,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=task_status,
        sort_by=sort_by,
        sort_direction=sort_direction,
        due_from=due_from,
        due_to=due_to,
    )
    return TaskPage(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def add_task(
    payload: TaskCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    return await create_task(session, user.id, payload.title, payload.due_at)


@router.get("/{task_id}", response_model=TaskRead)
async def read_task(
    task_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    task = await get_owned_task(session, user.id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=TaskErrorCode.TASK_NOT_FOUND,
        )
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def set_task_status(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    task = await get_owned_task(session, user.id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=TaskErrorCode.TASK_NOT_FOUND,
        )
    if payload.is_done is not None:
        task = await update_task_status(session, task, payload.is_done)
    if payload.title is not None or "due_at" in payload.model_fields_set:
        task = await update_task_details(
            session,
            task,
            title=payload.title,
            due_at=payload.due_at,
            update_due_at="due_at" in payload.model_fields_set,
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_task(
    task_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_session),
):
    task = await get_owned_task(session, user.id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=TaskErrorCode.TASK_NOT_FOUND,
        )
    await delete_task(session, task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
