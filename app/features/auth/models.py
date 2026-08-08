import uuid

from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import CheckConstraint, Column, Unicode
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(
            "char_length(username) BETWEEN 3 AND 50",
            name="ck_user_username_length",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_type=GUID, primary_key=True)
    username: str = Field(sa_column=Column(Unicode(50), nullable=False))
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    is_superuser: bool = Field(default=False, nullable=False)
    is_verified: bool = Field(default=False, nullable=False)
