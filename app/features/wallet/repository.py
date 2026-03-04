# app/features/wallet/repository.py
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.features.wallet.models import Wallet, LedgerJournal, LedgerEntry


class WalletRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_wallet_by_user_id(self, user_id: str) -> Wallet | None:
        return self.db.execute(select(Wallet).where(Wallet.user_id == user_id)).scalar_one_or_none()

    def create_wallet(self, user_id: str, currency: str = "IDR") -> Wallet:
        wallet = Wallet(user_id=user_id, currency=currency)
        self.db.add(wallet)
        return wallet

    def get_journal_by_idempotency(self, idempotency_key: str) -> LedgerJournal | None:
        return (
            self.db.execute(select(LedgerJournal).where(LedgerJournal.idempotency_key == idempotency_key))
            .scalar_one_or_none()
        )

    def create_journal(self, *, type: str, status: str, idempotency_key: str, reference_id: str | None, description: str | None) -> LedgerJournal:
        journal = LedgerJournal(
            type=type,
            status=status,
            idempotency_key=idempotency_key,
            reference_id=reference_id,
            description=description,
        )
        self.db.add(journal)
        return journal

    def add_entry(
        self,
        *,
        journal_id: str,
        account_type: str,
        account_id: str,
        direction: str,
        amount: int,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            journal_id=journal_id,
            account_type=account_type,
            account_id=account_id,
            direction=direction,
            amount=amount,
        )
        self.db.add(entry)
        return entry