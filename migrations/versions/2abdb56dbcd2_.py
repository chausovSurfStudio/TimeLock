"""empty message

Revision ID: 2abdb56dbcd2
Revises: b844412491a0
Create Date: 2016-03-19 19:26:54.328908

"""

# revision identifiers, used by Alembic.
revision = '2abdb56dbcd2'
down_revision = 'b844412491a0'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('checkins',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('time', sa.DateTime(), nullable=True),
    sa.Column('trustLevel', sa.Boolean(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('checkins')
    ### end Alembic commands ###