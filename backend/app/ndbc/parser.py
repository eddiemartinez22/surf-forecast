"""Parsers for NDBC realtime2 station files.

Both file formats share the same shape: two `#`-prefixed header rows
(names, then units) followed by whitespace-delimited data rows, newest
reading first. Missing values are marked "MM" and must become ``None``,
never 0 — a 0 in WVHT/DPD/etc. means something physically different
(flat seas / no period) than "the sensor didn't report".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

MISSING = "MM"

# Compass points -> degrees true, as used in .spec SwD/WWD columns.
COMPASS_TO_DEG = {
    "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5,
    "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
    "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5,
    "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5,
}


def _f(raw: str) -> float | None:
    """Parse a numeric field, treating MM (and any non-numeric junk) as missing."""
    if raw is None:
        return None
    raw = raw.strip()
    if raw == "" or raw.upper() == MISSING:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _i(raw: str) -> int | None:
    val = _f(raw)
    return int(val) if val is not None else None


def _direction(raw: str) -> float | None:
    """Parse a direction field that may be either degrees (met .txt MWD/WDIR)
    or a compass abbreviation (.spec SwD/WWD)."""
    if raw is None:
        return None
    raw = raw.strip()
    if raw == "" or raw.upper() == MISSING:
        return None
    if raw.upper() in COMPASS_TO_DEG:
        return COMPASS_TO_DEG[raw.upper()]
    try:
        return float(raw)
    except ValueError:
        return None


def _timestamp(yy: str, mo: str, dd: str, hh: str, mn: str) -> datetime | None:
    try:
        return datetime(int(yy), int(mo), int(dd), int(hh), int(mn), tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class MetReading:
    """One row of a station's standard meteorological (.txt) file."""

    timestamp: datetime
    wdir: float | None
    wspd: float | None
    gst: float | None
    wvht: float | None
    dpd: float | None
    apd: float | None
    mwd: float | None
    pres: float | None
    atmp: float | None
    wtmp: float | None
    dewp: float | None
    vis: float | None
    ptdy: float | None
    tide: float | None


@dataclass(frozen=True)
class SpecReading:
    """One row of a station's spectral wave summary (.spec) file."""

    timestamp: datetime
    wvht: float | None
    swh: float | None
    swp: float | None
    wwh: float | None
    wwp: float | None
    swd: float | None
    wwd: float | None
    steepness: str | None
    apd: float | None
    mwd: float | None


def _data_lines(text: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(line.split())
    return rows


def parse_met_txt(text: str) -> list[MetReading]:
    """Parse a standard meteorological realtime2 .txt file into readings.

    Malformed rows (wrong column count, unparseable timestamp) are skipped
    rather than raising, since a single bad line in a 45-day feed shouldn't
    take down ingestion of everything else.
    """
    readings = []
    for cols in _data_lines(text):
        if len(cols) < 19:
            continue
        ts = _timestamp(cols[0], cols[1], cols[2], cols[3], cols[4])
        if ts is None:
            continue
        readings.append(
            MetReading(
                timestamp=ts,
                wdir=_direction(cols[5]),
                wspd=_f(cols[6]),
                gst=_f(cols[7]),
                wvht=_f(cols[8]),
                dpd=_f(cols[9]),
                apd=_f(cols[10]),
                mwd=_direction(cols[11]),
                pres=_f(cols[12]),
                atmp=_f(cols[13]),
                wtmp=_f(cols[14]),
                dewp=_f(cols[15]),
                vis=_f(cols[16]),
                ptdy=_f(cols[17]),
                tide=_f(cols[18]),
            )
        )
    return readings


def parse_spec_file(text: str) -> list[SpecReading]:
    """Parse a spectral wave summary .spec file into readings."""
    readings = []
    for cols in _data_lines(text):
        if len(cols) < 15:
            continue
        ts = _timestamp(cols[0], cols[1], cols[2], cols[3], cols[4])
        if ts is None:
            continue
        steepness = cols[12].strip()
        readings.append(
            SpecReading(
                timestamp=ts,
                wvht=_f(cols[5]),
                swh=_f(cols[6]),
                swp=_f(cols[7]),
                wwh=_f(cols[8]),
                wwp=_f(cols[9]),
                swd=_direction(cols[10]),
                wwd=_direction(cols[11]),
                steepness=None if steepness.upper() in ("", MISSING, "N/A") else steepness,
                apd=_f(cols[13]),
                mwd=_direction(cols[14]),
            )
        )
    return readings


def parse_met_file(path: str | Path) -> list[MetReading]:
    return parse_met_txt(Path(path).read_text())


def parse_spec_path(path: str | Path) -> list[SpecReading]:
    return parse_spec_file(Path(path).read_text())
