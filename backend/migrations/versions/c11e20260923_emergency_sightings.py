"""Add Week 10 tracked emergency sighting history."""
from alembic import op
import sqlalchemy as sa
revision = 'c11e20260923'
down_revision = 'c10e20260919'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('emergency_sightings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('run_id', sa.String(32), nullable=False),
        sa.Column('track_id', sa.Integer(), nullable=False),
        sa.Column('frame_id', sa.Integer(), nullable=False),
        sa.Column('lane_id', sa.Integer(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('bbox_json', sa.Text(), nullable=False),
        sa.UniqueConstraint('event_id','frame_id',name='uq_emergency_sighting_frame'))
    op.create_index('ix_emergency_sightings_event_id','emergency_sightings',['event_id'])
    op.create_index('ix_emergency_sightings_run_id','emergency_sightings',['run_id'])


def downgrade():
    op.drop_table('emergency_sightings')
