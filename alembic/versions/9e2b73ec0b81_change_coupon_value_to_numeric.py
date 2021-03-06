"""change_coupon_value_to_numeric

Revision ID: 9e2b73ec0b81
Revises: 2bee96734b46
Create Date: 2021-12-21 03:49:31.611323

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e2b73ec0b81'
down_revision = '2bee96734b46'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('coupon', 'value',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(scale=2),
                    nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('coupon', 'value',
                    existing_type=sa.Numeric(scale=2),
                    type_=sa.Float(),
                    nullable=False)
    # ### end Alembic commands ###
