"""Source-scoped forecasting records. Legacy lane analytics are never used for training."""
from sqlalchemy import Integer, Float, String, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.base import Base
from backend.app.database.tables.week10 import now
from datetime import datetime


class ForecastStream(Base):
    __tablename__ = 'forecast_streams'
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    source: Mapped[str] = mapped_column(String(500))
    run_id: Mapped[str] = mapped_column(String(64))
    layout_id: Mapped[str] = mapped_column(String(64))
    data_kind: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ForecastSample(Base):
    __tablename__ = 'forecast_samples'
    __table_args__ = (UniqueConstraint('stream_id','lane_id','minute',name='uq_forecast_sample'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stream_id: Mapped[str] = mapped_column(String(32),index=True)
    lane_id: Mapped[int] = mapped_column(Integer)
    minute: Mapped[int] = mapped_column(Integer)
    vehicle_count: Mapped[float] = mapped_column(Float)
    average_speed: Mapped[float] = mapped_column(Float)
    queue_length: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)


class ForecastModel(Base):
    __tablename__ = 'forecast_models'
    id: Mapped[str] = mapped_column(String(32),primary_key=True)
    stream_id: Mapped[str] = mapped_column(String(32),index=True)
    lane_id: Mapped[int] = mapped_column(Integer)
    horizon: Mapped[int] = mapped_column(Integer)
    trained_through: Mapped[int] = mapped_column(Integer)
    artifact_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)


class ForecastJob(Base):
    __tablename__ = 'forecast_jobs'
    id: Mapped[str] = mapped_column(String(32),primary_key=True)
    stream_id: Mapped[str] = mapped_column(String(32))
    lane_id: Mapped[int] = mapped_column(Integer)
    horizon: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20),default='queued')
    model_id: Mapped[str | None] = mapped_column(String(32),nullable=True)
    error: Mapped[str | None] = mapped_column(String(500),nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)


class ForecastResult(Base):
    __tablename__ = 'forecast_results'
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    cache_key: Mapped[str] = mapped_column(String(64),unique=True)
    stream_id: Mapped[str] = mapped_column(String(32),index=True)
    lane_id: Mapped[int] = mapped_column(Integer)
    model_id: Mapped[str] = mapped_column(String(32))
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now)
