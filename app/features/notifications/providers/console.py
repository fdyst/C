# app/features/notifications/providers/console.py
import logging

log = logging.getLogger(__name__)


class ConsoleNotificationProvider:
    """
    MVP provider: cuma log ke console.
    Nanti bisa ganti WhatsApp/SMS/email.
    """
    def send(self, *, to: str, title: str, message: str) -> None:
        log.info("notify", extra={"to": to, "title": title, "message": message})