from datetime import datetime

from pydantic import BaseModel


class SpotStatus(BaseModel):
    id: str
    name: str
    buoy_id: str
    rating: str
    reason: str
    height_m: float | None
    period_sec: float | None
    direction_deg: float | None
    wind_speed_ms: float | None
    wind_dir_deg: float | None
    water_temp_c: float | None
    reading_timestamp: datetime | None
    stale: bool
    has_data: bool


class HistoryPoint(BaseModel):
    timestamp: datetime
    height_m: float | None
    period_sec: float | None
    direction_deg: float | None
