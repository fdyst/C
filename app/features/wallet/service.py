# app/features/wallet/service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case

from app.features.wallet.enums import (
    JournalStatus,
    AccountType,
    EntryDirection,
    JournalType,
)
from app.features.wallet.models import LedgerEntry
from app.features.wallet.repository import WalletRepository

SYSTEM_ACCOUNT_ID = "SYSTEM"


class WalletService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = WalletRepository(db)

    def ensure_wallet(self, user_id: str) -> str:
        wallet = self.repo.get_wallet_by_user_id(user_id)
        if wallet:
            return wallet.id

        wallet = self.repo.create_wallet(user_id=user_id, currency="IDR")
        self.db.flush()
        return wallet.id

    def _sum_account(self, *, account_type: AccountType, account_id: str) -> int:
        """
        Net balance untuk 1 account:
        CREDIT (+), DEBIT (-)
        """
        amount_expr = case(
            (LedgerEntry.direction == EntryDirection.CREDIT.value, LedgerEntry.amount),
            (LedgerEntry.direction == EntryDirection.DEBIT.value, -LedgerEntry.amount),
            else_=0,
        )

        q = select(func.coalesce(func.sum(amount_expr), 0)).where(
            LedgerEntry.account_type == account_type.value,
            LedgerEntry.account_id == account_id,
        )
        v = self.db.execute(q).scalar_one()
        return int(v)

    def get_balance(self, user_id: str) -> int:
        """
        Available balance = net USER_WALLET.
        """
        wallet = self.repo.get_wallet_by_user_id(user_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        return self._sum_account(account_type=AccountType.USER_WALLET, account_id=wallet.id)

    def get_hold_balance(self, user_id: str) -> int:
        """
        Hold balance = net HOLDING untuk wallet yang sama.
        """
        wallet = self.repo.get_wallet_by_user_id(user_id)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        return self._sum_account(account_type=AccountType.HOLDING, account_id=wallet.id)

    def get_summary(self, user_id: str) -> dict[str, int]:
        available = self.get_balance(user_id)
        hold = self.get_hold_balance(user_id)
        return {
            "available_balance": available,
            "hold_balance": hold,
            "total_balance": available + hold,
        }

    def post_double_entry(
        self,
        *,
        journal_type: JournalType,
        idempotency_key: str,
        description: str | None,
        reference_id: str | None,
        debit_account_type: AccountType,
        debit_account_id: str,
        credit_account_type: AccountType,
        credit_account_id: str,
        amount: int,
    ) -> str:
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be > 0")

        existing = self.repo.get_journal_by_idempotency(idempotency_key)
        if existing:
            return existing.id

        journal = self.repo.create_journal(
            type=journal_type.value,
            status=JournalStatus.POSTED.value,
            idempotency_key=idempotency_key,
            reference_id=reference_id,
            description=description,
        )
        self.db.flush()

        self.repo.add_entry(
            journal_id=journal.id,
            account_type=debit_account_type.value,
            account_id=debit_account_id,
            direction=EntryDirection.DEBIT.value,
            amount=amount,
        )
        self.repo.add_entry(
            journal_id=journal.id,
            account_type=credit_account_type.value,
            account_id=credit_account_id,
            direction=EntryDirection.CREDIT.value,
            amount=amount,
        )

        return journal.id