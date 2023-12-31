"""created address table

Revision ID: 83e443de94ec
Revises: 7ec329e50737
Create Date: 2023-06-12 16:32:01.877887

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "83e443de94ec"
down_revision = "7ec329e50737"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("street", sa.String(), nullable=False),
        sa.Column("street_number", sa.Integer(), nullable=False),
        sa.Column("postal_code", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("addresses")
    # ### end Alembic commands ###
