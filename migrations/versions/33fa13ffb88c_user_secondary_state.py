"""user secondary state

Revision ID: 33fa13ffb88c
Revises: 2febfdcd85e8
Create Date: 2021-05-19 15:48:35.087618

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '33fa13ffb88c'
down_revision = '2febfdcd85e8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    user_secondary_state = postgresql.ENUM('payment_verification_pending', name='usersecondarystate')
    user_secondary_state.create(op.get_bind())
    op.add_column('user', sa.Column('secondary_state', user_secondary_state))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'secondary_state')
    user_secondary_state = postgresql.ENUM('payment_verification_pending', name='usersecondarystate')
    user_secondary_state.drop(op.get_bind())
    # ### end Alembic commands ###