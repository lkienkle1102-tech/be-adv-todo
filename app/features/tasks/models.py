import uuid

from fastapi_users_db_sqlalchemy.generics import GUID
from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    __tablename__ = "task"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_type=GUID, primary_key=True)
    title: str = Field(nullable=False)
    is_done: bool = Field(default=False, nullable=False)
    owner_id: uuid.UUID = Field(sa_type=GUID, foreign_key="user.id", nullable=False)
