from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import STALE_AFTER_MINUTES
from app.models import BuoyReading
from app.scoring import SpotConfig, score_from_buoy_reading
from app.schemas import HistoryPoint, SpotStatus


def _latest_reading(session: Session, buoy_id: str) -> BuoyReading | None:
    stmt = (
        select(BuoyReading)
        .where(BuoyReading.station_id == buoy_id)
        .order_by(BuoyReading.timestamp.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def get_spot_status(session: Session, spot: SpotConfig) -> SpotStatus:
    reading = _latest_reading(session, spot.buoy_id)

    if reading is None:
        return SpotStatus(
            id=spot.id,
            name=spot.name,
            buoy_id=spot.buoy_id,
            rating="Unknown",
            reason="No data has been ingested for this buoy yet",
            height_m=None,
            period_sec=None,
            direction_deg=None,
            wind_speed_ms=None,
            wind_dir_deg=None,
            water_temp_c=None,
            reading_timestamp=None,
            stale=True,
            has_data=False,
        )

    result = score_from_buoy_reading(reading, spot)
    now = datetime.now(timezone.utc)
    ts = reading.timestamp if reading.timestamp.tzinfo else reading.timestamp.replace(tzinfo=timezone.utc)
    stale = (now - ts) > timedelta(minutes=STALE_AFTER_MINUTES)

    return SpotStatus(
        id=spot.id,
        name=spot.name,
        buoy_id=spot.buoy_id,
        rating="Unknown" if stale else result.rating,
        reason="Buoy hasn't reported recently — data may be stale" if stale else result.reason,
        height_m=result.height_m,
        period_sec=result.period_sec,
        direction_deg=result.direction_deg,
        wind_speed_ms=reading.wspd,
        wind_dir_deg=reading.wdir,
        water_temp_c=reading.wtmp,
        reading_timestamp=reading.timestamp,
        stale=stale,
        has_data=True,
    )


def get_spot_history(session: Session, spot: SpotConfig, hours: int) -> list[HistoryPoint]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    stmt = (
        select(BuoyReading)
        .where(BuoyReading.station_id == spot.buoy_id, BuoyReading.timestamp >= cutoff)
        .order_by(BuoyReading.timestamp.asc())
    )
    readings = session.execute(stmt).scalars().all()
    points = []
    for r in readings:
        height = r.swh if r.swh is not None else r.wvht
        period = r.swp if r.swp is not None else r.dpd
        direction = r.swd if r.swd is not None else r.mwd
        points.append(HistoryPoint(timestamp=r.timestamp, height_m=height, period_sec=period, direction_deg=direction))
    return points
