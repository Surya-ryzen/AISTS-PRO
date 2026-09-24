from datetime import datetime

from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.base import Base


class LaneAnalytics(Base):
    __tablename__ = "lane_analytics"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    lane_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    vehicle_count: Mapped[int] = mapped_column(
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

    traffic_flow: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
