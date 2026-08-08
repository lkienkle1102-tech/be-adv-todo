"""add username to user

Revision ID: 9a2f6c4d81e3
Revises: 75802166d43d
Create Date: 2026-08-08 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a2f6c4d81e3"
down_revision: Union[str, Sequence[str], None] = "75802166d43d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add username and backfill existing users with real international names."""
    op.add_column("user", sa.Column("username", sa.Unicode(50), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE "user"
            SET username = names.values[
                1 + mod(
                    mod(hashtextextended(id::text, 0), array_length(names.values, 1))
                    + array_length(names.values, 1),
                    array_length(names.values, 1)
                )
            ]
            FROM (
                SELECT ARRAY[
                    'Nguyễn Minh Anh',
                    'María García',
                    'José da Silva',
                    'Zoë van Dijk',
                    'Łukasz Kowalski',
                    'Søren Andersen',
                    'Chloé Dubois',
                    'İpek Yılmaz',
                    'Александра Иванова',
                    '李小龍',
                    '山田 太郎',
                    '김민준',
                    'أحمد محمود',
                    'अनन्या शर्मा',
                    'Thandiwe Ndlovu',
                    'Anaïs O''Connor'
                ]::varchar[] AS values
            ) AS names
            """
        )
    )
    op.alter_column(
        "user",
        "username",
        existing_type=sa.Unicode(50),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_user_username_length",
        "user",
        "char_length(username) BETWEEN 3 AND 50",
    )


def downgrade() -> None:
    """Remove username from users."""
    op.drop_constraint("ck_user_username_length", "user", type_="check")
    op.drop_column("user", "username")
