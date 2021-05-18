"""add verification type

Revision ID: 2febfdcd85e8
Revises: 74e00c05b7d4
Create Date: 2021-05-17 16:29:31.595146

src: https://stackoverflow.com/a/14845740
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2febfdcd85e8'
down_revision = '74e00c05b7d4'
branch_labels = None
depends_on = None


old_options = ('intro', 'dose_windows_requested', 'dose_window_times_requested', 'timezone_requested', 'payment_method_requested', 'paused', 'active', 'subscription_expired')
new_options = sorted(old_options + ('payment_verification_pending',))

old_type = postgresql.ENUM(*old_options, name='userstate')
new_type = postgresql.ENUM(*new_options, name='userstate')
tmp_type = postgresql.ENUM(*new_options, name='_userstate')


def upgrade():
    # Create a tempoary "_state" type, convert and drop the "old" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE public.user ALTER COLUMN state TYPE _userstate'
               ' USING state::text::_userstate')
    old_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "new" state type
    new_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE public.user ALTER COLUMN state TYPE userstate'
               ' USING state::text::userstate')
    tmp_type.drop(op.get_bind(), checkfirst=False)


def downgrade():
    # Create a tempoary "_state" type, convert and drop the "new" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE public.user ALTER COLUMN state TYPE _userstate'
               ' USING state::text::_userstate')
    new_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "old" state type
    old_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE public.user ALTER COLUMN state TYPE userstate'
               ' USING state::text::userstate')
    tmp_type.drop(op.get_bind(), checkfirst=False)
