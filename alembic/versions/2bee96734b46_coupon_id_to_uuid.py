"""coupon_id_to_uuid

Revision ID: 2bee96734b46
Revises: 76ee3ff01655
Create Date: 2021-12-07 15:06:38.459640

"""
import sqlalchemy as sa

from alembic import op
from app.db.base import CustomID

# revision identifiers, used by Alembic.
revision = '2bee96734b46'
down_revision = '76ee3ff01655'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('coupon', 'coupon_id')
    op.add_column('coupon', sa.Column(
            "coupon_id",
            CustomID(),
            server_default=sa.text(
                "concat(CAST(EXTRACT(EPOCH FROM now()) AS BIGINT),text('-'),gen_random_uuid())"
            ),
            nullable=False,
        )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('coupon', 'coupon_id')
    op.add_column('coupon', sa.Column("coupon_id", sa.Integer(), autoincrement=True, nullable=False))
    # ### end Alembic commands ###
