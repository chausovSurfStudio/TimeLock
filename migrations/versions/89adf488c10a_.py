"""empty message

Revision ID: 89adf488c10a
Revises: c89ab165c241
Create Date: 2016-04-23 00:14:43.077044

"""

# revision identifiers, used by Alembic.
revision = '89adf488c10a'
down_revision = 'c89ab165c241'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notes_timestamp'), 'notes', ['timestamp'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_notes_timestamp'), table_name='notes')
    op.drop_table('notes')
    ### end Alembic commands ###