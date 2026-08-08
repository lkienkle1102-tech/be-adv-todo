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


if __name__ == "__main__":
    unittest.main()
