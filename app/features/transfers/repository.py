# app/features/transfers/repository.py
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.features.transfers.models import Transfer


class TransferRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, transfer_id: str) -> Transfer | None:
        return self.db.get(Transfer, transfer_id)

    def get_by_idempotency_key(self, idempotency_key: str) -> Transfer | None:
        return self.db.execute(
            select(Transfer).where(Transfer.idempotency_key == idempotency_key)
        ).scalar_one_or_none()

    def create(
        self,
        *,
        sender_user_id: str,
        receiver_user_id: str,
        amount: int,
        fee_amount: int,
        status: str,
        journal_id: str | None,
        idempotency_key: str,
        note: str | None,
    ) -> Transfer:
        t = Transfer(
            sender_user_id=sender_user_id,
            receiver_user_id=receiver_user_id,
            amount=amount,
            fee_amount=fee_amount,
            status=status,
            journal_id=journal_id,
            idempotency_key=idempotency_key,
            note=note,
        )
        self.db.add(t)
        return t