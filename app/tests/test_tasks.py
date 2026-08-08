import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

from pydantic import ValidationError

from app.features.tasks.models import Task
from app.features.tasks.schemas import TaskCreate, TaskUpdate
from app.features.tasks.service import (
    create_task,
    delete_task,
    get_owned_task,
    list_tasks,
    update_task_schedule,
    update_task_status,
)


class TaskSchemaTests(unittest.TestCase):
    def test_title_is_trimmed(self) -> None:
        self.assertEqual(TaskCreate(title="  Plan the week  ").title, "Plan the week")

    def test_blank_title_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            TaskCreate(title="   ")

    def test_schedule_requires_timezone(self) -> None:
        with self.assertRaises(ValidationError):
            TaskCreate(title="Plan", due_at=datetime(2026, 8, 9, 9, 0))

        due_at = datetime.now(timezone.utc) + timedelta(days=1)
        self.assertEqual(TaskCreate(title="Plan", due_at=due_at).due_at, due_at)
        self.assertIsNone(TaskUpdate(due_at=None).due_at)

    def test_schedule_rejects_past_time(self) -> None:
        due_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        with self.assertRaises(ValidationError):
            TaskCreate(title="Too late", due_at=due_at)
        with self.assertRaises(ValidationError):
            TaskUpdate(due_at=due_at)


class TaskServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_lists_only_query_result_tasks(self) -> None:
        owner_id = uuid.uuid4()
        expected = [Task(owner_id=owner_id, title="First")]
        scalars = Mock()
        scalars.all.return_value = expected
        result = Mock()
        result.scalars.return_value = scalars
        session = AsyncMock()
        session.execute.return_value = result

        tasks = await list_tasks(session, owner_id)

        self.assertEqual(tasks, expected)
        session.execute.assert_awaited_once()

    async def test_creates_and_refreshes_task(self) -> None:
        session = AsyncMock()
        session.add = Mock()
        owner_id = uuid.uuid4()

        task = await create_task(session, owner_id, "Ship it")

        self.assertEqual(task.owner_id, owner_id)
        self.assertEqual(task.title, "Ship it")
        session.add.assert_called_once_with(task)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(task)

    async def test_finds_owned_task_from_query_result(self) -> None:
        owner_id = uuid.uuid4()
        expected = Task(owner_id=owner_id, title="Private")
        result = Mock()
        result.scalar_one_or_none.return_value = expected
        session = AsyncMock()
        session.execute.return_value = result

        task = await get_owned_task(session, owner_id, expected.id)

        self.assertIs(task, expected)
        session.execute.assert_awaited_once()

    async def test_updates_status_and_deletes_task(self) -> None:
        session = AsyncMock()
        session.add = Mock()
        task = Task(owner_id=uuid.uuid4(), title="Finish")

        updated = await update_task_status(session, task, True)

        self.assertTrue(updated.is_done)
        session.add.assert_called_once_with(task)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(task)

        session.reset_mock()
        due_at = datetime.now(timezone.utc) + timedelta(days=1)
        scheduled = await update_task_schedule(session, task, due_at)
        self.assertEqual(scheduled.due_at, due_at)
        session.add.assert_called_once_with(task)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(task)

        session.reset_mock()
        await delete_task(session, task)
        session.delete.assert_awaited_once_with(task)
        session.commit.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
