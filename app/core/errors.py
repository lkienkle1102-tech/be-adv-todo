from enum import Enum
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.locale import resolve_locale

DEFAULT_ERROR_CODE = "INTERNAL_SERVER_ERROR"

STATUS_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
}

ERROR_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "BAD_REQUEST": "The request could not be processed.",
        "UNAUTHORIZED": "Please log in to continue.",
        "FORBIDDEN": "You do not have permission to perform this action.",
        "NOT_FOUND": "The requested resource was not found.",
        "METHOD_NOT_ALLOWED": "This action is not supported.",
        "VALIDATION_ERROR": "Some submitted information is invalid.",
        "USERNAME_REQUIRED": "Enter your username.",
        "USERNAME_TOO_SHORT": "Use at least 3 characters for your username.",
        "USERNAME_TOO_LONG": "Use no more than 50 characters for your username.",
        "USERNAME_INVALID": "The username contains unsupported characters.",
        "INTERNAL_SERVER_ERROR": "Something went wrong. Please try again.",
        "LOGIN_BAD_CREDENTIALS": "The email or password is incorrect.",
        "LOGIN_USER_NOT_VERIFIED": "Verify your email before logging in.",
        "REGISTER_USER_ALREADY_EXISTS": "An account with this email already exists.",
        "REGISTER_INVALID_PASSWORD": "The password does not meet the security requirements.",
        "RESET_PASSWORD_BAD_TOKEN": "This password reset link is invalid or has expired.",
        "RESET_PASSWORD_INVALID_PASSWORD": "The new password does not meet the security requirements.",
        "VERIFY_USER_BAD_TOKEN": "This verification link is invalid or has expired.",
        "VERIFY_USER_ALREADY_VERIFIED": "This account has already been verified.",
        "UPDATE_USER_EMAIL_ALREADY_EXISTS": "An account with this email already exists.",
        "UPDATE_USER_INVALID_PASSWORD": "The password does not meet the security requirements.",
        "ACCESS_TOKEN_ALREADY_EXPIRED": "Your session has expired. Please log in again.",
        "ACCESS_TOKEN_DECODE_ERROR": "Your session is invalid. Please log in again.",
    },
    "vi": {
        "BAD_REQUEST": "Yêu cầu không thể được xử lý.",
        "UNAUTHORIZED": "Vui lòng đăng nhập để tiếp tục.",
        "FORBIDDEN": "Bạn không có quyền thực hiện thao tác này.",
        "NOT_FOUND": "Không tìm thấy tài nguyên được yêu cầu.",
        "METHOD_NOT_ALLOWED": "Thao tác này không được hỗ trợ.",
        "VALIDATION_ERROR": "Một số thông tin đã nhập không hợp lệ.",
        "USERNAME_REQUIRED": "Vui lòng nhập tên người dùng.",
        "USERNAME_TOO_SHORT": "Tên người dùng phải có ít nhất 3 ký tự.",
        "USERNAME_TOO_LONG": "Tên người dùng không được vượt quá 50 ký tự.",
        "USERNAME_INVALID": "Tên người dùng chứa ký tự không được hỗ trợ.",
        "INTERNAL_SERVER_ERROR": "Đã có lỗi xảy ra. Vui lòng thử lại.",
        "LOGIN_BAD_CREDENTIALS": "Email hoặc mật khẩu không chính xác.",
        "LOGIN_USER_NOT_VERIFIED": "Vui lòng xác minh email trước khi đăng nhập.",
        "REGISTER_USER_ALREADY_EXISTS": "Email này đã được dùng để đăng ký tài khoản.",
        "REGISTER_INVALID_PASSWORD": "Mật khẩu chưa đáp ứng yêu cầu bảo mật.",
        "RESET_PASSWORD_BAD_TOKEN": "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.",
        "RESET_PASSWORD_INVALID_PASSWORD": "Mật khẩu mới chưa đáp ứng yêu cầu bảo mật.",
        "VERIFY_USER_BAD_TOKEN": "Liên kết xác minh không hợp lệ hoặc đã hết hạn.",
        "VERIFY_USER_ALREADY_VERIFIED": "Tài khoản này đã được xác minh.",
        "UPDATE_USER_EMAIL_ALREADY_EXISTS": "Email này đã được dùng cho tài khoản khác.",
        "UPDATE_USER_INVALID_PASSWORD": "Mật khẩu chưa đáp ứng yêu cầu bảo mật.",
        "ACCESS_TOKEN_ALREADY_EXPIRED": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
        "ACCESS_TOKEN_DECODE_ERROR": "Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.",
    },
}


def get_error_message(code: str, locale: str) -> str:
    messages = ERROR_MESSAGES.get(locale, ERROR_MESSAGES["vi"])
    return messages.get(code, messages[DEFAULT_ERROR_CODE])


def extract_error_code(detail: Any, status_code: int) -> str:
    if isinstance(detail, dict):
        candidate = detail.get("code")
    elif isinstance(detail, Enum):
        candidate = detail.value
    else:
        candidate = detail

    if isinstance(candidate, str) and candidate in ERROR_MESSAGES["en"]:
        return candidate
    return STATUS_ERROR_CODES.get(status_code, DEFAULT_ERROR_CODE)


async def localized_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    locale = resolve_locale(request.headers.get("accept-language"))
    code = extract_error_code(exc.detail, exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "message": get_error_message(code, locale)},
        headers=exc.headers,
    )


async def localized_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    locale = resolve_locale(request.headers.get("accept-language"))
    code = "VALIDATION_ERROR"
    for error in exc.errors():
        if error.get("loc", ())[-1:] != ("username",):
            continue

        error_type = error.get("type")
        code = {
            "missing": "USERNAME_REQUIRED",
            "string_too_short": "USERNAME_TOO_SHORT",
            "string_too_long": "USERNAME_TOO_LONG",
        }.get(error_type, "USERNAME_INVALID")
        break

    return JSONResponse(
        status_code=422,
        content={"code": code, "message": get_error_message(code, locale)},
    )
