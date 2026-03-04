# app/jobs/tasks/poll_ppob_pending.py
import logging
import asyncio

from app.core.config import settings
from app.core.database import SessionLocal
from app.features.ppob.repository import PPOBRepository
from app.features.ppob.service import PPOBService

log = logging.getLogger(__name__)


def task_poll_pending() -> None:
    """
    Ambil beberapa order pending, lalu recheck ke provider.
    """
    db = SessionLocal()
    try:
        repo = PPOBRepository(db)
        orders = repo.list_pending_orders(limit=settings.job_poll_pending_batch_size)
        if not orders:
            return

        svc = PPOBService(db)
        for o in orders:
            try:
                asyncio.run(svc.admin_recheck_order(order_id=o.id))
            except Exception:
                log.exception("job_poll_pending_item_failed", extra={"order_id": o.id})

        log.info("job_poll_pending_done", extra={"count": len(orders)})
    finally:
        db.close()