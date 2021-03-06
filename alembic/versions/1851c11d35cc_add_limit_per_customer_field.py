"""add-limit-per-customer-field

Revision ID: 1851c11d35cc
Revises: 2bee96734b46
Create Date: 2021-12-17 11:11:19.744379

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1851c11d35cc'
down_revision = '9e2b73ec0b81'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('coupon', sa.Column('limit_per_customer', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('coupon', 'limit_per_customer')
    # ### end Alembic commands ###
