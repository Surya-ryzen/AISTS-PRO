"""Week 10 observations and operator-reviewed emergency workflow."""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.base import Base


def now():
    return datetime.now(timezone.utc)


class PlateObservation(Base):
    __tablename__ = 'plate_observations'
    __table_args__ = (UniqueConstraint('source', 'frame_key', 'raw_text', name='uq_plate_frame_evidence'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    source: Mapped[str] = mapped_column(String(160), index=True)
    frame_key: Mapped[str] = mapped_column(String(64), index=True)
    plate: Mapped[str] = mapped_column(String(20), index=True)
    raw_text: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(40), default='ocr_candidate')
    status: Mapped[str] = mapped_column(String(20), default='unverified')
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bbox_json: Mapped[str] = mapped_column(Text, default='[]')


class EmergencyEvent(Base):
    __tablename__ = 'emergency_events'
    __table_args__ = (UniqueConstraint('source', 'frame_key', 'vehicle_type', name='uq_emergency_frame_kind'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    source: Mapped[str] = mapped_column(String(160), index=True)
    frame_key: Mapped[str] = mapped_column(String(64), index=True)
    vehicle_type: Mapped[str] = mapped_column(String(30))
    evidence: Mapped[str] = mapped_column(String(500))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    method: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(24), default='pending', index=True)
    lane_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class EmergencyAudit(Base):
    __tablename__ = 'emergency_audit'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    actor: Mapped[str] = mapped_column(String(100))
    from_status: Mapped[str] = mapped_column(String(24))
    to_status: Mapped[str] = mapped_column(String(24))
    note: Mapped[str] = mapped_column(String(500))


class EmergencySighting(Base):
    __tablename__ = 'emergency_sightings'
    __table_args__ = (UniqueConstraint('event_id', 'frame_id', name='uq_emergency_sighting_frame'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    run_id: Mapped[str] = mapped_column(String(32), index=True)
    track_id: Mapped[int] = mapped_column(Integer)
    frame_id: Mapped[int] = mapped_column(Integer)
    lane_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    bbox_json: Mapped[str] = mapped_column(Text)


class EmergencyPlateLink(Base):
    __tablename__ = 'emergency_plate_links'
    __table_args__ = (UniqueConstraint('event_id','plate_id',name='uq_emergency_plate_link'),)
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer,index=True)
    plate_id: Mapped[int] = mapped_column(Integer,index=True)


class EmergencyPriority(Base):
    __tablename__ = 'emergency_priority'
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer,index=True)
    event_version: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(500))
    run_id: Mapped[str] = mapped_column(String(32))
    lane_id: Mapped[int] = mapped_column(Integer)
    green_seconds: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20),default='queued')
    actor: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True)
