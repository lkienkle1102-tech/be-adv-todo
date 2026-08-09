import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from pydantic import ValidationError

from app.features.auth.schemas import PasswordChange, UserUpdate
from app.features.auth.service import (
    CurrentPasswordIncorrectError,
    change_user_password,
)


class PasswordChangeSchemaTests(unittest.TestCase):
    def test_profile_update_rejects_direct_password_change(self) -> None:
        with self.assertRaises(ValidationError):
            UserUpdate(password="bypass-password-check")

    def test_requires_current_password(self) -> None:
        with self.assertRaises(ValidationError):
            PasswordChange(current_password="", new_password="new-password")

    def test_requires_new_password_with_eight_characters(self) -> None:
        with self.assertRaises(ValidationError):
            PasswordChange(current_password="old-password", new_password="short")


class ChangeUserPasswordTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_incorrect_current_password(self) -> None:
        manager = SimpleNamespace(
            password_helper=SimpleNamespace(
                verify_and_update=Mock(return_value=(False, None))
            ),
            update=AsyncMock(),
        )
        user = SimpleNamespace(hashed_password="stored-hash")

        with self.assertRaises(CurrentPasswordIncorrectError):
            await change_user_password(manager, user, "wrong-password", "new-password")

        manager.password_helper.verify_and_update.assert_called_once_with(
            "wrong-password", "stored-hash"
        )
        manager.update.assert_not_awaited()

    async def test_updates_password_only_after_current_password_matches(self) -> None:
        updated_user = object()
        manager = SimpleNamespace(
            password_helper=SimpleNamespace(
                verify_and_update=Mock(return_value=(True, None))
            ),
            update=AsyncMock(return_value=updated_user),
        )
        user = SimpleNamespace(hashed_password="stored-hash")

        result = await change_user_password(
            manager, user, "correct-password", "new-password"
        )

        self.assertIs(result, updated_user)
        manager.password_helper.verify_and_update.assert_called_once_with(
            "correct-password", "stored-hash"
        )
        manager.update.assert_awaited_once()
        update_payload, updated_target = manager.update.await_args.args
        self.assertEqual(update_payload.password, "new-password")
        self.assertIs(updated_target, user)
        self.assertTrue(manager.update.await_args.kwargs["safe"])


if __name__ == "__main__":
    unittest.main()
