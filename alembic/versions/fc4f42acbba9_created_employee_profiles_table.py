"""created employee_profiles table

Revision ID: fc4f42acbba9
Revises: bb5652422430
Create Date: 2023-06-15 11:34:17.506171

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fc4f42acbba9"
down_revision = "bb5652422430"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "employee_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("salary", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("available_holidays", sa.Integer(), nullable=False),
        sa.Column("hire_date", sa.Date(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("employee_profiles")
    # ### end Alembic commands ###
