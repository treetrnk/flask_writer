"""Longer sidebar

Revision ID: 63811d946c28
Revises: e4d818a01040
Create Date: 2019-08-23 12:54:02.032155

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63811d946c28'
down_revision = 'e4d818a01040'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('page', 'sidebar', existing_type=sa.String(length=1000), type_=sa.Text(length=5000), existing_nullable=True)
    op.alter_column('page_version', 'sidebar', existing_type=sa.String(length=1000), type_=sa.Text(length=5000), existing_nullable=True)

        
def downgrade():
    op.alter_column('page', 'sidebar', existing_type=sa.Text(length=5000), type_=sa.String(length=1000), existing_nullable=True)
    op.alter_column('page_version', 'sidebar', existing_type=sa.Text(length=5000), type_=sa.String(length=1000), existing_nullable=True)
