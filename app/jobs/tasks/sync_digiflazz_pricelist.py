# app/jobs/tasks/sync_digiflazz_pricelist.py
import logging
import asyncio

from app.core.database import SessionLocal
from app.features.ppob.service import PPOBService

log = logging.getLogger(__name__)


def task_sync_pricelist() -> None:
    """
    APScheduler bisa panggil function biasa.
    Karena PPOBService.sync_pricelist async, kita run pakai asyncio.run().
    """
    db = SessionLocal()
    try:
        upserted = asyncio.run(PPOBService(db).sync_pricelist())
        log.info("job_sync_pricelist_done", extra={"upserted": upserted})
    except Exception:
        log.exception("job_sync_pricelist_failed")
    finally:
        db.close()