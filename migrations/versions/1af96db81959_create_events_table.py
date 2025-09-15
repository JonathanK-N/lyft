"""create events table

Revision ID: 1af96db81959
Revises: 185b08f8e9c1
Create Date: 2025-09-15 10:29:22.956631

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '1af96db81959'
down_revision = '185b08f8e9c1'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'event' not in inspector.get_table_names():
        op.create_table(
            'event',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('start_at', sa.DateTime(), nullable=False),
            sa.Column('location', sa.String(length=255), nullable=True),
            sa.Column('lat', sa.Float(), nullable=True),
            sa.Column('lon', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )


def downgrade():
    op.drop_table('event')
