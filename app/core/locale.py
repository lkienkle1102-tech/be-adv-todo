from fastapi import Header

SUPPORTED_LOCALES = ("en", "vi")
DEFAULT_LOCALE = "vi"


def get_locale(accept_language: str | None = Header(default=None)) -> str:
    if accept_language:
        code = accept_language.split(",")[0].split("-")[0].strip().lower()
        if code in SUPPORTED_LOCALES:
            return code
    return DEFAULT_LOCALE
