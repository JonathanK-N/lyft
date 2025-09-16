"""user add email + password_hash

Revision ID: 185b08f8e9c1
Revises: 
Create Date: 2025-09-15 10:06:47.082197

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '185b08f8e9c1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Use raw ALTER TABLE to avoid SQLite batch/circular issues.
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c['name'] for c in insp.get_columns('user')}
    if 'email' not in cols:
        op.execute("ALTER TABLE user ADD COLUMN email VARCHAR(120)")
    if 'password_hash' not in cols:
        op.execute("ALTER TABLE user ADD COLUMN password_hash VARCHAR(255)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_user_email ON user(email)")


def downgrade():
    # Best effort for SQLite: drop index if exists (can't drop columns)
    op.execute("DROP INDEX IF EXISTS uq_user_email")
