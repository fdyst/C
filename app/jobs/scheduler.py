# app/jobs/scheduler.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.jobs.tasks.sync_digiflazz_pricelist import task_sync_pricelist
from app.jobs.tasks.poll_ppob_pending import task_poll_pending

log = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global scheduler
    if not settings.enable_jobs:
        log.info("jobs_disabled")
        return

    if scheduler:
        return

    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(
        task_sync_pricelist,
        trigger="interval",
        seconds=settings.job_sync_pricelist_interval_sec,
        id="sync_pricelist",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        task_poll_pending,
        trigger="interval",
        seconds=settings.job_poll_pending_interval_sec,
        id="poll_pending",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    log.info("scheduler_started")


def stop_scheduler() -> None:
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)
        scheduler = None