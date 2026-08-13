import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import POLL_INTERVAL_MINUTES
from app.ingest import ingest_all

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_ingest_job() -> None:
    results = ingest_all()
    logger.info("ingest run complete: %s", results)


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(_run_ingest_job, "interval", minutes=POLL_INTERVAL_MINUTES, id="ndbc_ingest")
    scheduler.start()
    _scheduler = scheduler
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
