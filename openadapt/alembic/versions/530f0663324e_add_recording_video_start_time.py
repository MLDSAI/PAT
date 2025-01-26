"""add Recording.video_start_time

Revision ID: 530f0663324e
Revises: 8713b142f5de
Create Date: 2024-02-16 10:31:05.020772

"""
import sqlalchemy as sa

from alembic import op
from openadapt.decorators import ForceFloat

# revision identifiers, used by Alembic.
revision = "530f0663324e"
down_revision = "8713b142f5de"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("recording", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "video_start_time",
                ForceFloat(precision=10, scale=2, asdecimal=False),
                nullable=True,
            )
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("recording", schema=None) as batch_op:
        batch_op.drop_column("video_start_time")

    # ### end Alembic commands ###
