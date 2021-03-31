"""empty message

Revision ID: 73386dd87aed
Revises: f1ae6f3a1966
Create Date: 2021-03-30 10:39:47.062952

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '73386dd87aed'
down_revision = 'f1ae6f3a1966'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_apscheduler_jobs_next_run_time', table_name='apscheduler_jobs')
    op.drop_table('apscheduler_jobs')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('apscheduler_jobs',
    sa.Column('id', sa.VARCHAR(length=191), autoincrement=False, nullable=False),
    sa.Column('next_run_time', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('job_state', postgresql.BYTEA(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='apscheduler_jobs_pkey')
    )
    op.create_index('ix_apscheduler_jobs_next_run_time', 'apscheduler_jobs', ['next_run_time'], unique=False)
    # ### end Alembic commands ###
