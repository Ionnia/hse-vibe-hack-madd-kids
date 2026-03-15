"""topic enrichment fields

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE topics ADD COLUMN IF NOT EXISTS enriched_at TIMESTAMPTZ NULL"
    )
    op.execute(
        "ALTER TABLE topics ADD COLUMN IF NOT EXISTS enrichment_sources JSONB NULL"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE topics DROP COLUMN IF EXISTS enrichment_sources")
    op.execute("ALTER TABLE topics DROP COLUMN IF EXISTS enriched_at")
