"""add pending_announcements

Revision ID: 0a42fd064caa
Revises: f11590a9a9a7
Create Date: 2021-05-11 13:50:58.518043

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0a42fd064caa'
down_revision = 'f11590a9a9a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('pending_announcement', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'pending_announcement')
    # ### end Alembic commands ###
