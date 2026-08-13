"""Fetches raw NDBC realtime2 files. No parsing here — see parser.py."""
from __future__ import annotations

import httpx

from app.config import NDBC_BASE_URL, USER_AGENT

_HEADERS = {"User-Agent": USER_AGENT}


class NdbcFetchError(RuntimeError):
    pass


def fetch_met_txt(station_id: str) -> str:
    return _fetch(f"{NDBC_BASE_URL}/{station_id}.txt")


def fetch_spec_txt(station_id: str) -> str | None:
    """Returns None (not an error) if the station has no spectral file —
    that's a normal condition for met-only stations, not a fetch failure."""
    try:
        return _fetch(f"{NDBC_BASE_URL}/{station_id}.spec")
    except NdbcFetchError:
        return None


def _fetch(url: str) -> str:
    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=30.0)
    except httpx.HTTPError as exc:
        raise NdbcFetchError(f"request to {url} failed: {exc}") from exc
    if resp.status_code != 200:
        raise NdbcFetchError(f"{url} returned HTTP {resp.status_code}")
    return resp.text
