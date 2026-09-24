"""Week 10 observations; adds tables only, does not drop existing project data."""
from alembic import op
import sqlalchemy as sa

revision = 'c10e20260919'
down_revision = 'b4f4c72ee83c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('plate_observations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(160), nullable=False),
        sa.Column('frame_key', sa.String(64), nullable=False),
        sa.Column('plate', sa.String(20), nullable=False),
        sa.Column('raw_text', sa.String(100), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('method', sa.String(40), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('reviewed_by', sa.String(100)),
        sa.Column('bbox_json', sa.Text(), nullable=False),
        sa.UniqueConstraint('source', 'frame_key', 'raw_text', name='uq_plate_frame_evidence'))
    op.create_table('emergency_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(160), nullable=False),
        sa.Column('frame_key', sa.String(64), nullable=False),
        sa.Column('vehicle_type', sa.String(30), nullable=False),
        sa.Column('evidence', sa.String(500), nullable=False),
        sa.Column('confidence', sa.Float()),
        sa.Column('method', sa.String(40), nullable=False),
        sa.Column('status', sa.String(24), nullable=False),
        sa.Column('lane_id', sa.Integer()),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.UniqueConstraint('source', 'frame_key', 'vehicle_type', name='uq_emergency_frame_kind'))
    op.create_table('emergency_audit',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actor', sa.String(100), nullable=False),
        sa.Column('from_status', sa.String(24), nullable=False),
        sa.Column('to_status', sa.String(24), nullable=False),
        sa.Column('note', sa.String(500), nullable=False))
    for name, columns in {'plate_observations':['observed_at','source','frame_key','plate'],
                           'emergency_events':['created_at','source','frame_key','status'],
                           'emergency_audit':['event_id']}.items():
        for column in columns:
            op.create_index(f'ix_{name}_{column}', name, [column])


def downgrade():
    for name in ['emergency_audit', 'emergency_events', 'plate_observations']:
        op.drop_table(name)
