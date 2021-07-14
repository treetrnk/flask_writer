"""Record action

Revision ID: bb7aa6e122cb
Revises: 662fb0a49767
Create Date: 2021-07-13 06:33:27.166532

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'bb7aa6e122cb'
down_revision = '662fb0a49767'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('page', 'body',
               existing_type=mysql.LONGTEXT(collation='utf8mb4_unicode_ci'),
               type_=sa.Text(length=10000000),
               existing_nullable=True)
    op.alter_column('page', 'notes',
               existing_type=mysql.LONGTEXT(collation='utf8mb4_unicode_ci'),
               type_=sa.Text(length=5000000),
               existing_nullable=True)
    op.alter_column('page_version', 'body',
               existing_type=mysql.LONGTEXT(collation='utf8mb4_unicode_ci'),
               type_=sa.Text(length=10000000),
               existing_nullable=True)
    op.alter_column('page_version', 'notes',
               existing_type=mysql.LONGTEXT(collation='utf8mb4_unicode_ci'),
               type_=sa.Text(length=5000000),
               existing_nullable=True)
    op.add_column('record', sa.Column('action', sa.String(length=150), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('record', 'action')
    op.alter_column('page_version', 'notes',
               existing_type=sa.Text(length=5000000),
               type_=mysql.LONGTEXT(collation='utf8mb4_unicode_ci'),
               existing_nullable=True)
    op.alter_column('page_version', 'body',
               existing_type=sa.Text(length=10000000),
               type_=mysql.LONGTEXT(collation='utf8mb4_unicode_ci'),
               existing_nullable=True)
    op.alter_column('page', 'notes',
               existing_type=sa.Text(length=5000000),
               type_=mysql.LONGTEXT(collation='utf8mb4_unicode_ci'),
               existing_nullable=True)
    op.alter_column('page', 'body',
               existing_type=sa.Text(length=10000000),
               type_=mysql.LONGTEXT(collation='utf8mb4_unicode_ci'),
               existing_nullable=True)
    # ### end Alembic commands ###
