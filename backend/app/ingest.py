"""Fetches + parses a station's data and upserts it into buoy_readings.

Every poll re-fetches NDBC's rolling 45-day window, so ingestion has to be
an upsert keyed on (station_id, timestamp) rather than a blind insert —
otherwise every hourly poll would duplicate ~45 days of history.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import BuoyReading
from app.ndbc.client import NdbcFetchError, fetch_met_txt, fetch_spec_txt
from app.ndbc.parser import parse_met_txt, parse_spec_file
from app.spots import load_spots

logger = logging.getLogger(__name__)

_UPSERT_COLUMNS = [
    c.name
    for c in BuoyReading.__table__.columns
    if c.name not in ("id", "station_id", "timestamp")
]


def ingest_station(session: Session, station_id: str) -> int:
    met_readings = parse_met_txt(fetch_met_txt(station_id))
    spec_text = fetch_spec_txt(station_id)
    spec_by_ts = {r.timestamp: r for r in parse_spec_file(spec_text)} if spec_text else {}

    now = datetime.now(timezone.utc)
    rows = []
    for met in met_readings:
        spec = spec_by_ts.get(met.timestamp)
        rows.append(
            {
                "station_id": station_id,
                "timestamp": met.timestamp,
                "fetched_at": now,
                "wdir": met.wdir,
                "wspd": met.wspd,
                "gst": met.gst,
                "wvht": met.wvht,
                "dpd": met.dpd,
                "apd": met.apd,
                "mwd": met.mwd,
                "pres": met.pres,
                "atmp": met.atmp,
                "wtmp": met.wtmp,
                "swh": spec.swh if spec else None,
                "swp": spec.swp if spec else None,
                "wwh": spec.wwh if spec else None,
                "wwp": spec.wwp if spec else None,
                "swd": spec.swd if spec else None,
                "wwd": spec.wwd if spec else None,
                "steepness": spec.steepness if spec else None,
            }
        )

    if not rows:
        return 0

    # SQLite caps bound variables per statement (default 999); a 45-day,
    # ~10-min-cadence file times ~20 columns blows well past that in one
    # INSERT, so upsert in chunks instead of a single giant statement.
    total_columns = len(rows[0])
    batch_size = max(1, 900 // total_columns)
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        stmt = sqlite_insert(BuoyReading).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=["station_id", "timestamp"],
            set_={col: getattr(stmt.excluded, col) for col in _UPSERT_COLUMNS},
        )
        session.execute(stmt)
    session.commit()
    return len(rows)


def ingest_all() -> dict[str, int | str]:
    """Ingest every unique buoy referenced by the spot config. Returns a
    per-station report (row count, or an error string) so a single dead
    buoy doesn't take the rest of the ingestion run down with it."""
    station_ids = sorted({spot.buoy_id for spot in load_spots()})
    results: dict[str, int | str] = {}
    for station_id in station_ids:
        session = get_session()
        try:
            results[station_id] = ingest_station(session, station_id)
        except NdbcFetchError as exc:
            logger.warning("ingest failed for station %s: %s", station_id, exc)
            results[station_id] = f"error: {exc}"
        finally:
            session.close()
    return results
