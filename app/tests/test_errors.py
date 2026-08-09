import json
import unittest
from enum import Enum

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import (
    extract_error_code,
    get_error_message,
    localized_http_exception_handler,
    localized_validation_exception_handler,
)
from app.features.tasks.errors import TaskErrorCode


class ExampleErrorCode(str, Enum):
    LOGIN_BAD_CREDENTIALS = "LOGIN_BAD_CREDENTIALS"


class ErrorMappingTests(unittest.TestCase):
    def test_maps_fastapi_users_enum_code(self) -> None:
        code = extract_error_code(ExampleErrorCode.LOGIN_BAD_CREDENTIALS, 400)

        self.assertEqual(code, "LOGIN_BAD_CREDENTIALS")

    def test_maps_nested_error_code(self) -> None:
        code = extract_error_code({"code": "REGISTER_INVALID_PASSWORD"}, 400)

        self.assertEqual(code, "REGISTER_INVALID_PASSWORD")

    def test_falls_back_to_http_status_code(self) -> None:
        code = extract_error_code("Not authenticated", 401)

        self.assertEqual(code, "UNAUTHORIZED")

    def test_returns_message_in_requested_locale(self) -> None:
        self.assertEqual(
            get_error_message("LOGIN_BAD_CREDENTIALS", "en"),
            "The email or password is incorrect.",
        )
        self.assertEqual(
            get_error_message("LOGIN_BAD_CREDENTIALS", "vi"),
            "Email hoặc mật khẩu không chính xác.",
        )

    def test_returns_task_message_in_requested_locale(self) -> None:
        self.assertEqual(
            get_error_message("TASK_NOT_FOUND", "en"),
            "The task was not found.",
        )
        self.assertEqual(
            get_error_message("TASK_NOT_FOUND", "vi"),
            "Không tìm thấy công việc.",
        )

    def test_returns_current_password_error_in_requested_locale(self) -> None:
        self.assertEqual(
            get_error_message("CURRENT_PASSWORD_INCORRECT", "en"),
            "The current password is incorrect.",
        )
        self.assertEqual(
            get_error_message("CURRENT_PASSWORD_INCORRECT", "vi"),
            "Mật khẩu hiện tại không chính xác.",
        )

    def test_unknown_code_uses_localized_generic_message(self) -> None:
        self.assertEqual(
            get_error_message("UNKNOWN", "en"),
            "Something went wrong. Please try again.",
        )


class ErrorResponseTests(unittest.IsolatedAsyncioTestCase):
    async def test_response_contains_localized_code_and_message(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/auth/jwt/login",
                "headers": [(b"accept-language", b"en-US,en;q=0.9")],
            }
        )
        exception = StarletteHTTPException(
            status_code=400,
            detail=ExampleErrorCode.LOGIN_BAD_CREDENTIALS,
        )

        response = await localized_http_exception_handler(request, exception)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.body),
            {
                "code": "LOGIN_BAD_CREDENTIALS",
                "message": "The email or password is incorrect.",
            },
        )

    async def test_username_validation_response_uses_specific_localized_code(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/auth/register",
                "headers": [(b"accept-language", b"vi")],
            }
        )
        exception = RequestValidationError(
            [
                {
                    "type": "string_too_short",
                    "loc": ("body", "username"),
                    "msg": "String should have at least 3 characters",
                    "input": "李小",
                    "ctx": {"min_length": 3},
                }
            ]
        )

        response = await localized_validation_exception_handler(request, exception)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            json.loads(response.body),
            {
                "code": "USERNAME_TOO_SHORT",
                "message": "Tên người dùng phải có ít nhất 3 ký tự.",
            },
        )

    async def test_task_http_error_uses_specific_localized_code(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "DELETE",
                "path": "/tasks/00000000-0000-0000-0000-000000000000",
                "headers": [(b"accept-language", b"vi")],
            }
        )
        exception = StarletteHTTPException(
            status_code=404,
            detail=TaskErrorCode.TASK_NOT_FOUND,
        )

        response = await localized_http_exception_handler(request, exception)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            json.loads(response.body),
            {
                "code": "TASK_NOT_FOUND",
                "message": "Không tìm thấy công việc.",
            },
        )

    async def test_task_title_validation_uses_specific_localized_code(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/tasks",
                "headers": [(b"accept-language", b"vi")],
            }
        )
        exception = RequestValidationError(
            [
                {
                    "type": "string_too_short",
                    "loc": ("body", "title"),
                    "msg": "String should have at least 1 character",
                    "input": "",
                    "ctx": {"min_length": 1},
                }
            ]
        )

        response = await localized_validation_exception_handler(request, exception)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            json.loads(response.body),
            {
                "code": "TASK_TITLE_REQUIRED",
                "message": "Vui lòng nhập tên công việc.",
            },
        )

    async def test_task_custom_validation_code_is_preserved(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/tasks",
                "headers": [(b"accept-language", b"en")],
            }
        )
        exception = RequestValidationError(
            [
                {
                    "type": "TASK_DUE_AT_IN_PAST",
                    "loc": ("body", "due_at"),
                    "msg": "due_at must be in the future",
                    "input": "2020-01-01T00:00:00Z",
                }
            ]
        )

        response = await localized_validation_exception_handler(request, exception)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            json.loads(response.body),
            {
                "code": "TASK_DUE_AT_IN_PAST",
                "message": "Choose a due time in the future.",
            },
        )


if __name__ == "__main__":
    unittest.main()
