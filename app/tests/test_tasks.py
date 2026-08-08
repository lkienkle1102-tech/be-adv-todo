import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

from pydantic import ValidationError

from app.features.tasks.errors import TaskErrorCode, TaskValidationError
from app.features.tasks.models import Task
from app.features.tasks.schemas import (
    SortDirection,
    TaskCreate,
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
    update_task_schedule,
    update_task_details,
    update_task_status,
)


class TaskSchemaTests(unittest.TestCase):
    def test_title_is_trimmed(self) -> None:
        self.assertEqual(TaskCreate(title="  Plan the week  ").title, "Plan the week")

    def test_blank_title_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            TaskCreate(title="   ")
        with self.assertRaises(ValidationError):
            TaskUpdate(title="   ")

    def test_update_title_is_trimmed(self) -> None:
        self.assertEqual(TaskUpdate(title="  Revised plan  ").title, "Revised plan")

    def test_schedule_requires_timezone(self) -> None:
        with self.assertRaises(ValidationError) as context:
            TaskCreate(title="Plan", due_at=datetime(2026, 8, 9, 9, 0))
        self.assertEqual(
            context.exception.errors()[0]["type"],
            TaskErrorCode.TASK_DUE_AT_TIMEZONE_REQUIRED.value,
        )

        due_at = datetime.now(timezone.utc) + timedelta(days=1)
        self.assertEqual(TaskCreate(title="Plan", due_at=due_at).due_at, due_at)
        self.assertIsNone(TaskUpdate(due_at=None).due_at)

    def test_schedule_rejects_past_time(self) -> None:
        due_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        with self.assertRaises(ValidationError) as create_context:
            TaskCreate(title="Too late", due_at=due_at)
        self.assertEqual(
            create_context.exception.errors()[0]["type"],
            TaskErrorCode.TASK_DUE_AT_IN_PAST.value,
        )
        with self.assertRaises(ValidationError) as update_context:
            TaskUpdate(due_at=due_at)
        self.assertEqual(
            update_context.exception.errors()[0]["type"],
            TaskErrorCode.TASK_DUE_AT_IN_PAST.value,
        )

    def test_filter_range_accepts_open_ended_and_validates_provided_values(self) -> None:
        start = datetime(2026, 8, 8, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 8, 8, 11, 0, tzinfo=timezone.utc)

        validate_due_range(None, None)
        validate_due_range(start, None)
        validate_due_range(None, end)
        validate_due_range(start, end)
        with self.assertRaises(TaskValidationError) as order_context:
            validate_due_range(end, start)
        self.assertEqual(
            order_context.exception.code,
            TaskErrorCode.TASK_DUE_RANGE_ORDER_INVALID,
        )
        with self.assertRaises(TaskValidationError) as timezone_context:
            validate_due_range(None, end.replace(tzinfo=None))
        self.assertEqual(
            timezone_context.exception.code,
            TaskErrorCode.TASK_DUE_RANGE_TIMEZONE_REQUIRED,
        )


class TaskServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_lists_only_query_result_tasks(self) -> None:
        owner_id = uuid.uuid4()
        expected = [Task(owner_id=owner_id, title="First")]
        scalars = Mock()
        scalars.all.return_value = expected
        count_result = Mock()
        count_result.scalar_one.return_value = 1
        task_result = Mock()
        task_result.scalars.return_value = scalars
        session = AsyncMock()
        session.execute.side_effect = [count_result, task_result]

        tasks, total = await list_tasks(session, owner_id)

        self.assertEqual(tasks, expected)
        self.assertEqual(total, 1)
        self.assertEqual(session.execute.await_count, 2)

    async def test_lists_with_search_status_range_sort_and_pagination(self) -> None:
        owner_id = uuid.uuid4()
        due_from = datetime(2026, 8, 1, tzinfo=timezone.utc)
        due_to = datetime(2026, 9, 1, tzinfo=timezone.utc)
        count_result = Mock()
        count_result.scalar_one.return_value = 0
        scalars = Mock()
        scalars.all.return_value = []
        task_result = Mock()
        task_result.scalars.return_value = scalars
        session = AsyncMock()
        session.execute.side_effect = [count_result, task_result]

        tasks, total = await list_tasks(
            session,
            owner_id,
            page=2,
            page_size=20,
            search="100%_ready",
            status_filter=TaskStatusFilter.upcoming,
            sort_by=TaskSortBy.title,
            sort_direction=SortDirection.desc,
            due_from=due_from,
            due_to=due_to,
        )

        self.assertEqual(tasks, [])
        self.assertEqual(total, 0)
        statements = [str(call.args[0]) for call in session.execute.await_args_list]
        self.assertTrue(all("lower(task.title) LIKE lower" in statement for statement in statements))
        self.assertIn("task.is_done IS false", statements[0])
        self.assertIn("task.due_at >", statements[0])
        self.assertIn("task.due_at >=", statements[0])
        self.assertIn("task.due_at <=", statements[0])
        self.assertIn("task.title DESC", statements[1])
        self.assertIn("LIMIT", statements[1])
        self.assertIn("OFFSET", statements[1])

    async def test_status_filters_cover_all_active_and_done(self) -> None:
        owner_id = uuid.uuid4()
        statements: dict[TaskStatusFilter, str] = {}

        for status_filter in (
            TaskStatusFilter.all,
            TaskStatusFilter.active,
            TaskStatusFilter.done,
        ):
            count_result = Mock()
            count_result.scalar_one.return_value = 0
            scalars = Mock()
            scalars.all.return_value = []
            task_result = Mock()
            task_result.scalars.return_value = scalars
            session = AsyncMock()
            session.execute.side_effect = [count_result, task_result]

            await list_tasks(session, owner_id, status_filter=status_filter)
            statements[status_filter] = str(session.execute.await_args_list[0].args[0])

        self.assertNotIn("task.is_done IS", statements[TaskStatusFilter.all])
        self.assertIn("task.is_done IS false", statements[TaskStatusFilter.active])
        self.assertIn("task.is_done IS true", statements[TaskStatusFilter.done])

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
        revised = await update_task_details(
            session,
            task,
            title="Revised",
            due_at=None,
            update_due_at=True,
        )
        self.assertEqual(revised.title, "Revised")
        self.assertIsNone(revised.due_at)
        session.add.assert_called_once_with(task)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(task)

        session.reset_mock()
        await delete_task(session, task)
        session.delete.assert_awaited_once_with(task)
        session.commit.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
