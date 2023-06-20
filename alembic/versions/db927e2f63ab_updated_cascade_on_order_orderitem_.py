"""updated cascade on order-orderitem relationship

Revision ID: db927e2f63ab
Revises: 5b30e44af13c
Create Date: 2023-06-14 16:35:14.058641

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "db927e2f63ab"
down_revision = "5b30e44af13c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("order_items_order_id_fkey", "order_items", type_="foreignkey")
    op.create_foreign_key(
        "order_items_order_id_fkey",
        "order_items",
        "orders",
        ["order_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("order_items_order_id_fkey", "order_items", type_="foreignkey")
    op.create_foreign_key(
        "order_items_order_id_fkey", "order_items", "orders", ["order_id"], ["id"]
    )
    # ### end Alembic commands ###