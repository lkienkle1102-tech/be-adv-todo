from app.features.auth.manager import UserManager
from app.features.auth.models import User
from app.features.auth.schemas import PasswordUpdate


class CurrentPasswordIncorrectError(Exception):
    pass


async def change_user_password(
    user_manager: UserManager,
    user: User,
    current_password: str,
    new_password: str,
) -> User:
    verified, _ = user_manager.password_helper.verify_and_update(
        current_password,
        user.hashed_password,
    )
    if not verified:
        raise CurrentPasswordIncorrectError

    return await user_manager.update(
        PasswordUpdate(password=new_password),
        user,
        safe=True,
    )
