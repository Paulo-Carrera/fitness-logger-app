"""fix exercise and workout relationship

Revision ID: 6979bfc3fabe
Revises: 31bc46aa8026
Create Date: 2025-05-19 16:09:01.803081

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6979bfc3fabe'
down_revision = '31bc46aa8026'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('workout_exercises', schema=None) as batch_op:
        batch_op.drop_column('duration_minutes')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('workout_exercises', schema=None) as batch_op:
        batch_op.add_column(sa.Column('duration_minutes', sa.INTEGER(), autoincrement=False, nullable=True))

    # ### end Alembic commands ###
