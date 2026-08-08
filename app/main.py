from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.errors import (
    localized_http_exception_handler,
    localized_validation_exception_handler,
)
from app.core.locale import get_locale
from app.features.auth.router import router as auth_router
from app.features.tasks.router import router as tasks_router

app = FastAPI(title="Advanced Todo API")

app.add_exception_handler(StarletteHTTPException, localized_http_exception_handler)
app.add_exception_handler(RequestValidationError, localized_validation_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(tasks_router)


@app.get("/health")
async def health(locale: str = Depends(get_locale)):
    return {"status": "ok", "locale": locale}
