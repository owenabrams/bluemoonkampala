"""CHANGES with Waypoints MAP

Revision ID: fdab8e3623f3
Revises: 3ed3f9bc4954
Create Date: 2019-02-25 18:07:45.273274

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fdab8e3623f3'
down_revision = '3ed3f9bc4954'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('waypoint', sa.Column('color', sa.String(length=128), nullable=True))
    op.add_column('waypoint', sa.Column('picture', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('waypoint', 'picture')
    op.drop_column('waypoint', 'color')
    # ### end Alembic commands ###
