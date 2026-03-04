# app/features/wallet/models.py
import uuid
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="IDR")


class LedgerJournal(Base):
    __tablename__ = "ledger_journals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)

    # idempotency untuk transaksi finansial (transfer/topup/ppob)
    idempotency_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)

    reference_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    journal_id: Mapped[str] = mapped_column(String(36), ForeignKey("ledger_journals.id"), index=True)

    account_type: Mapped[str] = mapped_column(String(30), index=True)  # USER_WALLET / SYSTEM
    account_id: Mapped[str] = mapped_column(String(36), index=True)    # wallet_id atau "SYSTEM"

    direction: Mapped[str] = mapped_column(String(6), index=True)      # DEBIT/CREDIT
    amount: Mapped[int] = mapped_column(Integer)                       # rupiah integer