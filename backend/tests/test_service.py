from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import BuoyReading
from app.scoring import SpotConfig
from app.service import get_spot_status

SPOT = SpotConfig(
    id="test-spot",
    name="Test Spot",
    buoy_id="99999",
    optimal_direction_deg=(60, 120),
    min_period_sec=6,
    optimal_period_sec=(8, 14),
    size_thresholds_m={"small": 0.3, "good": 0.6, "firing": 1.2},
)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def _add_reading(session, minutes_ago: int, **fields):
    ts = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    reading = BuoyReading(station_id=SPOT.buoy_id, timestamp=ts, fetched_at=ts, **fields)
    session.add(reading)
    session.commit()
    return reading


def test_no_readings_at_all_is_unknown_and_flagged_no_data(session):
    status = get_spot_status(session, SPOT)
    assert status.rating == "Unknown"
    assert status.has_data is False
    assert status.stale is True


def test_falls_back_to_last_usable_reading_when_latest_ping_is_blank(session):
    # A good reading an hour ago, then the buoy's most recent ping blanked
    # out its wave sensors (WVHT/DPD = MM) but still reported water temp --
    # a real, observed NDBC pattern (see buoy 41070).
    _add_reading(session, minutes_ago=60, wvht=0.8, dpd=12, mwd=90, wtmp=27.0)
    _add_reading(session, minutes_ago=3, wvht=None, dpd=None, mwd=None, wtmp=27.2)

    status = get_spot_status(session, SPOT)

    assert status.rating != "Unknown"
    assert status.height_m == 0.8
    assert status.period_sec == 12
    # water temp still comes from the true latest ping, not the fallback
    assert status.water_temp_c == 27.2
    assert status.stale is False


def test_reading_timestamp_reflects_the_usable_reading_not_the_blank_ping(session):
    _add_reading(session, minutes_ago=60, wvht=0.8, dpd=12, mwd=90)
    blank = _add_reading(session, minutes_ago=3, wvht=None, dpd=None, mwd=None)

    status = get_spot_status(session, SPOT)

    assert status.reading_timestamp != blank.timestamp
    assert abs((status.reading_timestamp - (blank.timestamp - timedelta(minutes=57))).total_seconds()) < 1


def test_no_usable_reading_within_staleness_window_shows_unknown(session):
    # Last usable reading is older than STALE_AFTER_MINUTES (150) -- even
    # with the fallback, this should still be reported as stale/Unknown.
    _add_reading(session, minutes_ago=200, wvht=0.8, dpd=12, mwd=90)
    _add_reading(session, minutes_ago=5, wvht=None, dpd=None, mwd=None)

    status = get_spot_status(session, SPOT)

    assert status.stale is True
    assert status.rating == "Unknown"


def test_prefers_swell_partition_fallback_over_met_fallback(session):
    # Latest ping blank; most recent usable reading only has the .spec
    # swell partition populated (no combined WVHT/DPD) -- should still
    # be picked up by the "usable" query, not just the met fields.
    _add_reading(session, minutes_ago=30, swh=0.9, swp=11, swd=90)
    _add_reading(session, minutes_ago=2, wvht=None, dpd=None)

    status = get_spot_status(session, SPOT)

    assert status.height_m == 0.9
    assert status.period_sec == 11


def test_uses_latest_reading_directly_when_it_has_data(session):
    _add_reading(session, minutes_ago=60, wvht=0.4, dpd=8, mwd=90)
    _add_reading(session, minutes_ago=3, wvht=0.9, dpd=13, mwd=95, wtmp=27.5)

    status = get_spot_status(session, SPOT)

    assert status.height_m == 0.9
    assert status.period_sec == 13
