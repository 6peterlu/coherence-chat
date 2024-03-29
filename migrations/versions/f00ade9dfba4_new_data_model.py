"""new data model

Revision ID: f00ade9dfba4
Revises: 412d769b5eef
Create Date: 2021-04-25 18:00:12.480616

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f00ade9dfba4'
down_revision = '412d769b5eef'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('phone_number', sa.String(length=10), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('manual_takeover', sa.Boolean(), nullable=False),
    sa.Column('paused', sa.Boolean(), nullable=False),
    sa.Column('timezone', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('dose_window',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start_hour', sa.Integer(), nullable=False),
    sa.Column('end_hour', sa.Integer(), nullable=False),
    sa.Column('start_minute', sa.Integer(), nullable=False),
    sa.Column('end_minute', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='dose_window_user_fkey_custom', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('medication_name', sa.String(), nullable=False),
    sa.Column('instructions', sa.String(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='medication_user_fkey_custom', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('dose_medication_linker',
    sa.Column('dose_window_id', sa.Integer(), nullable=True),
    sa.Column('medication_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['dose_window_id'], ['dose_window.id'], name='dose_medication_linker_dose_window_fkey_custom', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['medication_id'], ['medication.id'], name='dose_medication_linker_medication_fkey_custom', ondelete='CASCADE')
    )
    op.create_table('event_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('dose_window_id', sa.Integer(), nullable=True),
    sa.Column('medication_id', sa.Integer(), nullable=True),
    sa.Column('event_time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['dose_window_id'], ['dose_window.id'], ),
    sa.ForeignKeyConstraint(['medication_id'], ['medication.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='event_user_fkey_custom', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('event_log')
    op.drop_table('dose_medication_linker')
    op.drop_table('medication')
    op.drop_table('dose_window')
    op.drop_table('user')
    # ### end Alembic commands ###
