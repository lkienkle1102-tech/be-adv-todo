import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi_users import FastAPIUsers

from app.features.auth.backend import auth_backend
from app.features.auth.manager import UserManager, get_user_manager
from app.features.auth.models import User
from app.features.auth.schemas import PasswordChange, UserCreate, UserRead, UserUpdate
from app.features.auth.service import (
    CurrentPasswordIncorrectError,
    change_user_password,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)

router = APIRouter(prefix="/auth", tags=["auth"])

router.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/jwt")
router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))
router.include_router(fastapi_users.get_reset_password_router())
router.include_router(fastapi_users.get_verify_router(UserRead))
router.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users")


@router.post("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_current_user_password(
    payload: PasswordChange,
    user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
) -> Response:
    try:
        await change_user_password(
            user_manager,
            user,
            payload.current_password,
            payload.new_password,
        )
    except CurrentPasswordIncorrectError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CURRENT_PASSWORD_INCORRECT",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
