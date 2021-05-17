# TODO: fix this migration

"""add verification type

Revision ID: 2febfdcd85e8
Revises: 74e00c05b7d4
Create Date: 2021-05-17 16:29:31.595146

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

old_type = sa.Enum(*old_options, name='status')
new_type = sa.Enum(*new_options, name='status')
tmp_type = sa.Enum(*new_options, name='_status')


def upgrade():
    # Create a tempoary "_status" type, convert and drop the "old" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE testcaseresult ALTER COLUMN status TYPE _status'
               ' USING status::text::_status')
    old_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "new" status type
    new_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE testcaseresult ALTER COLUMN status TYPE status'
               ' USING status::text::status')
    tmp_type.drop(op.get_bind(), checkfirst=False)


def downgrade():
    # Convert 'output_limit_exceeded' status into 'timed_out'
    op.execute(tcr.update().where(tcr.c.status==u'output_limit_exceeded')
               .values(status='timed_out'))
    # Create a tempoary "_status" type, convert and drop the "new" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE testcaseresult ALTER COLUMN status TYPE _status'
               ' USING status::text::_status')
    new_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "old" status type
    old_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE testcaseresult ALTER COLUMN status TYPE status'
               ' USING status::text::status')
    tmp_type.drop(op.get_bind(), checkfirst=False)
