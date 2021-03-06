"""Product and Link

Revision ID: dab2ae085b83
Revises: 4d9d4e0e52db
Create Date: 2019-12-19 11:26:12.899246

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dab2ae085b83'
down_revision = '4d9d4e0e52db'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('product',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('price', sa.String(length=10), nullable=False),
    sa.Column('description', sa.String(length=1000), nullable=True),
    sa.Column('image', sa.String(length=500), nullable=True),
    sa.Column('sort', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('link',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(length=100), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=False),
    sa.Column('sort', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('link')
    op.drop_table('product')
    # ### end Alembic commands ###
