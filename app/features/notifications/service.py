# app/features/notifications/service.py
from app.features.notifications.providers.console import ConsoleNotificationProvider


class NotificationService:
    def __init__(self):
        self.provider = ConsoleNotificationProvider()

    def transfer_received(self, *, receiver_phone: str, amount: int) -> None:
        self.provider.send(
            to=receiver_phone,
            title="Saldo masuk",
            message=f"Kamu menerima transfer sebesar Rp{amount}",
        )

    def ppob_success(self, *, user_phone: str, sku_code: str, customer_no: str) -> None:
        self.provider.send(
            to=user_phone,
            title="Pembayaran PPOB sukses",
            message=f"Produk {sku_code} untuk {customer_no} berhasil.",
        )