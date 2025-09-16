"""ride_request add pickup and assigned_driver_id

Revision ID: 7c1ab2d4e2a3
Revises: 1af96db81959
Create Date: 2025-09-16 02:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '7c1ab2d4e2a3'
down_revision = '1af96db81959'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c['name'] for c in insp.get_columns('ride_request')}
    if 'pickup_lat' not in cols:
        op.execute("ALTER TABLE ride_request ADD COLUMN pickup_lat FLOAT")
    if 'pickup_lon' not in cols:
        op.execute("ALTER TABLE ride_request ADD COLUMN pickup_lon FLOAT")
    if 'assigned_driver_id' not in cols:
        op.execute("ALTER TABLE ride_request ADD COLUMN assigned_driver_id INTEGER")


def downgrade():
    # SQLite can't drop columns easily; no-op
    pass

