"""empty message

Revision ID: 5bcc28a34df9
Revises: 615b5cf65da9
Create Date: 2016-04-14 17:05:41.506824

"""

# revision identifiers, used by Alembic.
revision = '5bcc28a34df9'
down_revision = '615b5cf65da9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('timeCaches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('week', sa.Integer(), nullable=True),
    sa.Column('time', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('timeCaches')
    ### end Alembic commands ###