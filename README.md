# Surf Forecast

Pulls real-time buoy data from NOAA's National Data Buoy Center (NDBC) and
translates it into a surf-quality rating for a configured set of Florida
Atlantic coast spots.

## Spots tracked

| Spot | Buoy | Notes |
|---|---|---|
| Fernandina Beach, FL | [41112](https://www.ndbc.noaa.gov/station_page.php?station=41112) | Offshore Waverider, full spectral data |
| St. Augustine, FL | [41117](https://www.ndbc.noaa.gov/station_page.php?station=41117) | Nearshore, full spectral data |
| New Smyrna Beach / Ponce Inlet, FL | [41070](https://www.ndbc.noaa.gov/station_page.php?station=41070) | Substituted for 41069, which reports no wave data |
| Canaveral Offshore Reference (20nm), FL | [41009](https://www.ndbc.noaa.gov/station_page.php?station=41009) | Cleaner open-ocean swell signal |
| Cape Canaveral Nearshore, FL | [41113](https://www.ndbc.noaa.gov/station_page.php?station=41113) | Closer to what actually reaches the beach |

Swell direction window, period window, and size thresholds per spot are
editable in [`backend/app/spots.json`](backend/app/spots.json) — the
defaults are a generic Florida east-coast starting point (NE-SE window,
6s minimum / 8-14s optimal period), meant to be tuned against real
sessions.

## Tech stack

- **Backend:** FastAPI + SQLAlchemy + SQLite, APScheduler for hourly polling
- **Frontend:** React + TypeScript + Vite, Recharts for trend lines

## Running locally

**Backend:**

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate  # or source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

On startup it initializes `backend/data/surf.db`, immediately ingests all
configured buoys in the background, and then polls NDBC hourly.

**Frontend:**

```bash
cd frontend
npm install
npm run dev -- --port 5174
```

Open http://localhost:5174.

## Running tests

```bash
cd backend
pytest tests/ -v
```

Parser tests run against real sample NDBC files committed under
`backend/tests/fixtures/`, including edge cases (missing `MM` fields,
garbage rows) — no network access required.

## How scoring works

See [`backend/app/scoring.py`](backend/app/scoring.py). Period and
direction match matter more than raw height: a size band (Flat / Small /
Good / Firing) is downgraded when the period is too short (wind chop, not
real swell) or the swell direction falls outside the spot's configured
window. The `.spec` file's swell partition (`SwH`/`SwP`/`SwD`) is
preferred over the combined sea state (`WVHT`/`DPD`/`MWD`) when available,
since it isolates true swell from local wind waves.

## Data freshness

A reading older than 150 minutes is treated as stale (buoy likely
offline) rather than shown as current conditions — NDBC buoys do go down.
