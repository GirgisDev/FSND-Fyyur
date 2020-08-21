"""empty message

Revision ID: 1567002e069e
Revises: cb47f796b67c
Create Date: 2020-08-15 16:55:30.100461

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1567002e069e'
down_revision = 'cb47f796b67c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Venue', sa.Column('genres', sa.String(length=120), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'genres')
    # ### end Alembic commands ###
