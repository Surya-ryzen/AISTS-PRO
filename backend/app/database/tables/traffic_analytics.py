from datetime import datetime

from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.base import Base


class TrafficAnalytics(Base):
    __tablename__ = "traffic_analytics"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    current_vehicle_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    total_vehicle_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    average_speed: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    density: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    queue_length: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    waiting_vehicles: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    average_waiting_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    maximum_waiting_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    pcu: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    traffic_flow: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
