"""Subscriber sub length

Revision ID: 662fb0a49767
Revises: 157a61ff25e8
Create Date: 2021-06-10 01:01:04.473594

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '662fb0a49767'
down_revision = '157a61ff25e8'
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
    op.alter_column('subscriber', 'subscription',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=100),
               type_=sa.String(length=1000),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('subscriber', 'subscription',
               existing_type=sa.String(length=1000),
               type_=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=100),
               existing_nullable=False)
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
