"""Week 10 priority and Week 11 forecasting persistence."""
from alembic import op
import sqlalchemy as sa
revision = 'w11_20260924'
down_revision = 'c11e20260923'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('forecast_streams',
        sa.Column('id', sa.String(length=32), nullable=False, primary_key=True),
        sa.Column('source', sa.String(length=500), nullable=False, primary_key=False),
        sa.Column('run_id', sa.String(length=64), nullable=False, primary_key=False),
        sa.Column('layout_id', sa.String(length=64), nullable=False, primary_key=False),
        sa.Column('data_kind', sa.String(length=24), nullable=False, primary_key=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
    )
    op.create_table('forecast_samples',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('stream_id', sa.String(length=32), nullable=False, primary_key=False),
        sa.Column('lane_id', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('minute', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('vehicle_count', sa.Float(), nullable=False, primary_key=False),
        sa.Column('average_speed', sa.Float(), nullable=False, primary_key=False),
        sa.Column('queue_length', sa.Float(), nullable=False, primary_key=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.UniqueConstraint('stream_id','lane_id','minute', name='uq_forecast_sample'),
    )
    op.create_index('ix_forecast_samples_stream_id','forecast_samples',['stream_id'],unique=False)
    op.create_table('forecast_models',
        sa.Column('id', sa.String(length=32), nullable=False, primary_key=True),
        sa.Column('stream_id', sa.String(length=32), nullable=False, primary_key=False),
        sa.Column('lane_id', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('horizon', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('trained_through', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('artifact_json', sa.Text(), nullable=False, primary_key=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
    )
    op.create_index('ix_forecast_models_stream_id','forecast_models',['stream_id'],unique=False)
    op.create_table('forecast_jobs',
        sa.Column('id', sa.String(length=32), nullable=False, primary_key=True),
        sa.Column('stream_id', sa.String(length=32), nullable=False, primary_key=False),
        sa.Column('lane_id', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('horizon', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('status', sa.String(length=20), nullable=False, primary_key=False),
        sa.Column('model_id', sa.String(length=32), nullable=True, primary_key=False),
        sa.Column('error', sa.String(length=500), nullable=True, primary_key=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
    )
    op.create_table('forecast_results',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('cache_key', sa.String(length=64), nullable=False, primary_key=False),
        sa.Column('stream_id', sa.String(length=32), nullable=False, primary_key=False),
        sa.Column('lane_id', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('model_id', sa.String(length=32), nullable=False, primary_key=False),
        sa.Column('payload_json', sa.Text(), nullable=False, primary_key=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.UniqueConstraint('cache_key', name=None),
    )
    op.create_index('ix_forecast_results_stream_id','forecast_results',['stream_id'],unique=False)
    op.create_table('emergency_plate_links',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('event_id', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('plate_id', sa.Integer(), nullable=False, primary_key=False),
        sa.UniqueConstraint('event_id','plate_id', name='uq_emergency_plate_link'),
    )
    op.create_index('ix_emergency_plate_links_event_id','emergency_plate_links',['event_id'],unique=False)
    op.create_index('ix_emergency_plate_links_plate_id','emergency_plate_links',['plate_id'],unique=False)
    op.create_table('emergency_priority',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('event_id', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('event_version', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('source', sa.String(length=500), nullable=False, primary_key=False),
        sa.Column('run_id', sa.String(length=32), nullable=False, primary_key=False),
        sa.Column('lane_id', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('green_seconds', sa.Integer(), nullable=False, primary_key=False),
        sa.Column('status', sa.String(length=20), nullable=False, primary_key=False),
        sa.Column('actor', sa.String(length=100), nullable=False, primary_key=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, primary_key=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True, primary_key=False),
    )
    op.create_index('ix_emergency_priority_event_id','emergency_priority',['event_id'],unique=False)


def downgrade():
    op.drop_table('emergency_priority')
    op.drop_table('emergency_plate_links')
    op.drop_table('forecast_results')
    op.drop_table('forecast_jobs')
    op.drop_table('forecast_models')
    op.drop_table('forecast_samples')
    op.drop_table('forecast_streams')
