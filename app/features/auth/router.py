import uuid

from fastapi import APIRouter
from fastapi_users import FastAPIUsers

from app.features.auth.backend import auth_backend
from app.features.auth.manager import get_user_manager
from app.features.auth.models import User
from app.features.auth.schemas import UserCreate, UserRead, UserUpdate

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)

router = APIRouter(prefix="/auth", tags=["auth"])

router.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/jwt")
router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))
router.include_router(fastapi_users.get_reset_password_router())
router.include_router(fastapi_users.get_verify_router(UserRead))
router.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users")
