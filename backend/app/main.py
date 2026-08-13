import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db import init_db
from app.ingest import ingest_all
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Kick off an immediate fetch in the background so the dashboard has
    # data on first load instead of waiting up to an hour for the first
    # scheduled poll, without blocking server startup on 5 NDBC requests.
    threading.Thread(target=ingest_all, daemon=True).start()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Surf Forecast", lifespan=lifespan)

# Read-only public buoy data, no auth or cookies involved, so a permissive
# origin policy carries no real risk and avoids having to track every
# environment (local dev port, Render static site URL, etc.) by hand.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
