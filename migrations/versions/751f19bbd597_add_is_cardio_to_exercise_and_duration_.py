"""Add is_cardio to Exercise and duration to WorkoutExercise

Revision ID: 751f19bbd597
Revises: 2e2408b740bd
Create Date: 2025-05-21 18:29:20.689200

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '751f19bbd597'
down_revision = '2e2408b740bd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('exercises', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_cardio', sa.Boolean(), nullable=True))

    with op.batch_alter_table('workout_exercises', schema=None) as batch_op:
        batch_op.add_column(sa.Column('duration', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('workout_exercises', schema=None) as batch_op:
        batch_op.drop_column('duration')

    with op.batch_alter_table('exercises', schema=None) as batch_op:
        batch_op.drop_column('is_cardio')

    # ### end Alembic commands ###
