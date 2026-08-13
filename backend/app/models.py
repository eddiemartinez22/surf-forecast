from datetime import datetime

from sqlalchemy import DateTime, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BuoyReading(Base):
    """One merged reading (met + spectral) for a station at a timestamp.

    Unique on (station_id, timestamp) so re-fetching the rolling 45-day
    NDBC window on every poll is a harmless upsert, not a growing pile of
    duplicates.
    """

    __tablename__ = "buoy_readings"
    __table_args__ = (UniqueConstraint("station_id", "timestamp", name="uq_station_timestamp"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[str] = mapped_column(String(8), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # standard meteorological (.txt)
    wdir: Mapped[float | None] = mapped_column(Float, nullable=True)
    wspd: Mapped[float | None] = mapped_column(Float, nullable=True)
    gst: Mapped[float | None] = mapped_column(Float, nullable=True)
    wvht: Mapped[float | None] = mapped_column(Float, nullable=True)
    dpd: Mapped[float | None] = mapped_column(Float, nullable=True)
    apd: Mapped[float | None] = mapped_column(Float, nullable=True)
    mwd: Mapped[float | None] = mapped_column(Float, nullable=True)
    pres: Mapped[float | None] = mapped_column(Float, nullable=True)
    atmp: Mapped[float | None] = mapped_column(Float, nullable=True)
    wtmp: Mapped[float | None] = mapped_column(Float, nullable=True)

    # spectral partitioning (.spec), nullable since not every station has it
    swh: Mapped[float | None] = mapped_column(Float, nullable=True)
    swp: Mapped[float | None] = mapped_column(Float, nullable=True)
    wwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    wwp: Mapped[float | None] = mapped_column(Float, nullable=True)
    swd: Mapped[float | None] = mapped_column(Float, nullable=True)
    wwd: Mapped[float | None] = mapped_column(Float, nullable=True)
    steepness: Mapped[str | None] = mapped_column(String(16), nullable=True)
