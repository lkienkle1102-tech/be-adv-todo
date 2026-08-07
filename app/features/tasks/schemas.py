import uuid

from pydantic import BaseModel


class TaskRead(BaseModel):
    id: uuid.UUID
    title: str
    is_done: bool
