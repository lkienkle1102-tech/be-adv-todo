"""add task due_at

Revision ID: c1d2e3f4a5b6
Revises: 9a2f6c4d81e3
Create Date: 2026-08-08 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "9a2f6c4d81e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add an optional timezone-aware schedule to tasks."""
    op.add_column(
        "task",
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_task_owner_due_at", "task", ["owner_id", "due_at"])


def downgrade() -> None:
    """Remove task scheduling."""
    op.drop_index("ix_task_owner_due_at", table_name="task")
    op.drop_column("task", "due_at")
