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
    422: "VALIDATION_ERROR",
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
        "CURRENT_PASSWORD_INCORRECT": "The current password is incorrect.",
        "ACCESS_TOKEN_ALREADY_EXPIRED": "Your session has expired. Please log in again.",
        "ACCESS_TOKEN_DECODE_ERROR": "Your session is invalid. Please log in again.",
        "TASK_NOT_FOUND": "The task was not found.",
        "TASK_TITLE_REQUIRED": "Enter a task name.",
        "TASK_TITLE_TOO_LONG": "Keep the task name to 200 characters or fewer.",
        "TASK_TITLE_INVALID": "The task name is invalid.",
        "TASK_DUE_AT_INVALID": "Enter a valid due date and time.",
        "TASK_DUE_AT_TIMEZONE_REQUIRED": "The due time must include a timezone.",
        "TASK_DUE_AT_IN_PAST": "Choose a due time in the future.",
        "TASK_DUE_RANGE_TIMEZONE_REQUIRED": "Both range values must include a timezone.",
        "TASK_DUE_RANGE_ORDER_INVALID": "The range start must be earlier than the range end.",
        "TASK_DUE_RANGE_INVALID": "Enter a valid due-time range.",
        "TASK_ID_INVALID": "The task ID is invalid.",
        "TASK_PAGE_INVALID": "The page must be 1 or greater.",
        "TASK_PAGE_SIZE_INVALID": "The page size must be between 1 and 100.",
        "TASK_SEARCH_TOO_LONG": "Search text must be 200 characters or fewer.",
        "TASK_STATUS_FILTER_INVALID": "The task status filter is invalid.",
        "TASK_SORT_FIELD_INVALID": "The task sort field is invalid.",
        "TASK_SORT_DIRECTION_INVALID": "The task sort direction is invalid.",
        "TASK_COMPLETION_STATUS_INVALID": "The task completion status is invalid.",
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
        "CURRENT_PASSWORD_INCORRECT": "Mật khẩu hiện tại không chính xác.",
        "ACCESS_TOKEN_ALREADY_EXPIRED": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
        "ACCESS_TOKEN_DECODE_ERROR": "Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.",
        "TASK_NOT_FOUND": "Không tìm thấy công việc.",
        "TASK_TITLE_REQUIRED": "Vui lòng nhập tên công việc.",
        "TASK_TITLE_TOO_LONG": "Tên công việc không được vượt quá 200 ký tự.",
        "TASK_TITLE_INVALID": "Tên công việc không hợp lệ.",
        "TASK_DUE_AT_INVALID": "Vui lòng nhập ngày và giờ đến hạn hợp lệ.",
        "TASK_DUE_AT_TIMEZONE_REQUIRED": "Thời điểm đến hạn phải kèm múi giờ.",
        "TASK_DUE_AT_IN_PAST": "Vui lòng chọn thời điểm đến hạn trong tương lai.",
        "TASK_DUE_RANGE_TIMEZONE_REQUIRED": "Hai thời điểm trong khoảng phải kèm múi giờ.",
        "TASK_DUE_RANGE_ORDER_INVALID": "Thời điểm bắt đầu phải trước thời điểm kết thúc.",
        "TASK_DUE_RANGE_INVALID": "Khoảng thời gian đến hạn không hợp lệ.",
        "TASK_ID_INVALID": "Mã công việc không hợp lệ.",
        "TASK_PAGE_INVALID": "Số trang phải lớn hơn hoặc bằng 1.",
        "TASK_PAGE_SIZE_INVALID": "Số công việc mỗi trang phải từ 1 đến 100.",
        "TASK_SEARCH_TOO_LONG": "Nội dung tìm kiếm không được vượt quá 200 ký tự.",
        "TASK_STATUS_FILTER_INVALID": "Bộ lọc trạng thái công việc không hợp lệ.",
        "TASK_SORT_FIELD_INVALID": "Tiêu chí sắp xếp công việc không hợp lệ.",
        "TASK_SORT_DIRECTION_INVALID": "Thứ tự sắp xếp công việc không hợp lệ.",
        "TASK_COMPLETION_STATUS_INVALID": "Trạng thái hoàn thành công việc không hợp lệ.",
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
        field = error.get("loc", ())[-1:]
        error_type = error.get("type")
        if isinstance(error_type, str) and error_type in ERROR_MESSAGES["en"]:
            code = error_type
            break
        if field == ("username",):
            code = {
                "missing": "USERNAME_REQUIRED",
                "string_too_short": "USERNAME_TOO_SHORT",
                "string_too_long": "USERNAME_TOO_LONG",
            }.get(error_type, "USERNAME_INVALID")
            break
        if not request.url.path.startswith("/tasks"):
            continue

        code = {
            "title": {
                "missing": "TASK_TITLE_REQUIRED",
                "string_too_short": "TASK_TITLE_REQUIRED",
                "string_too_long": "TASK_TITLE_TOO_LONG",
            }.get(error_type, "TASK_TITLE_INVALID"),
            "due_at": "TASK_DUE_AT_INVALID",
            "task_id": "TASK_ID_INVALID",
            "page": "TASK_PAGE_INVALID",
            "page_size": "TASK_PAGE_SIZE_INVALID",
            "search": "TASK_SEARCH_TOO_LONG",
            "status": "TASK_STATUS_FILTER_INVALID",
            "sort_by": "TASK_SORT_FIELD_INVALID",
            "sort_direction": "TASK_SORT_DIRECTION_INVALID",
            "due_from": "TASK_DUE_RANGE_INVALID",
            "due_to": "TASK_DUE_RANGE_INVALID",
            "is_done": "TASK_COMPLETION_STATUS_INVALID",
        }.get(field[0] if field else None, "VALIDATION_ERROR")
        break

    return JSONResponse(
        status_code=422,
        content={"code": code, "message": get_error_message(code, locale)},
    )
