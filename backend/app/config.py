from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "surf.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

SPOTS_CONFIG_PATH = Path(__file__).resolve().parent / "spots.json"

NDBC_BASE_URL = "https://www.ndbc.noaa.gov/data/realtime2"
USER_AGENT = "surf-forecast-app/0.1 (personal project; contact: eddiemartinez2@yahoo.com)"

# These stations actually post new readings roughly every 20-30 min, not
# hourly, so polling every 15 min stays close to their real cadence
# without hammering NDBC (still a handful of requests per buoy per hour).
POLL_INTERVAL_MINUTES = 15

# A reading older than this is treated as the buoy being offline/stale, not just "last hour's data".
STALE_AFTER_MINUTES = 150

# How much history the dashboard trend chart shows.
TREND_WINDOW_HOURS = 72
