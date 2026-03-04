# app/features/transfers/service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import verify_pin
from app.features.users.repository import UserRepository
from app.features.wallet.service import WalletService
from app.features.wallet.repository import WalletRepository
from app.features.wallet.enums import JournalType, AccountType
from app.features.transfers.repository import TransferRepository


class TransferService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.wallet_service = WalletService(db)
        self.wallet_repo = WalletRepository(db)
        self.transfers = TransferRepository(db)

    def create_transfer(
        self,
        *,
        sender_user_id: str,
        sender_pin_hash: str | None,
        receiver_phone: str,
        amount: int,
        pin: str,
        note: str | None,
        idempotency_key: str,
    ):
        """
        Rules MVP:
        - wajib Idempotency-Key
        - wajib PIN
        - transfer via phone (receiver_phone)
        - fee = 0 (bisa ditambah nanti)
        - atomic (1 DB transaction)
        """
        if not idempotency_key:
            raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

        if not sender_pin_hash:
            raise HTTPException(status_code=400, detail="PIN not set. Call /auth/set-pin first")

        if not verify_pin(pin, sender_pin_hash):
            raise HTTPException(status_code=401, detail="Invalid PIN")

        receiver = self.users.get_by_phone(receiver_phone)
        if not receiver:
            raise HTTPException(status_code=404, detail="Receiver not found")

        if receiver.id == sender_user_id:
            raise HTTPException(status_code=400, detail="Cannot transfer to self")

        # Prefix idempotency per sender biar aman dari collision antar user
        scoped_key = f"{sender_user_id}:{idempotency_key}"

        # If retry -> return existing transfer (idempotent)
        existing = self.transfers.get_by_idempotency_key(scoped_key)
        if existing:
            return existing

        # Transaction boundary
        try:
            with self.db.begin():
                # ensure wallets exist
                sender_wallet_id = self.wallet_service.ensure_wallet(sender_user_id)
                receiver_wallet_id = self.wallet_service.ensure_wallet(receiver.id)

                sender_balance = self.wallet_service.get_balance(sender_user_id)
                fee_amount = 0
                total_debit = amount + fee_amount

                if sender_balance < total_debit:
                    raise HTTPException(status_code=400, detail="Insufficient balance")

                # Post ledger journal: debit sender wallet -> credit receiver wallet
                # idempotency journal pakai scoped_key juga
                journal_id = self.wallet_service.post_double_entry(
                    journal_type=JournalType.TRANSFER,
                    idempotency_key=scoped_key,
                    description=f"Transfer to {receiver_phone}" if not note else note,
                    reference_id=None,
                    debit_account_type=AccountType.USER_WALLET,
                    debit_account_id=sender_wallet_id,
                    credit_account_type=AccountType.USER_WALLET,
                    credit_account_id=receiver_wallet_id,
                    amount=amount,
                )

                transfer = self.transfers.create(
                    sender_user_id=sender_user_id,
                    receiver_user_id=receiver.id,
                    amount=amount,
                    fee_amount=fee_amount,
                    status="SUCCESS",
                    journal_id=journal_id,
                    idempotency_key=scoped_key,
                    note=note,
                )

                # flush supaya transfer.id kebentuk
                self.db.flush()
                return transfer

        except HTTPException:
            # propagate expected errors
            raise
        except Exception:
            # avoid leaking internal error
            raise HTTPException(status_code=500, detail="Transfer failed")