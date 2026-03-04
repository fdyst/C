# app/features/transfers/models.py
import uuid
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    sender_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    receiver_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    amount: Mapped[int] = mapped_column(Integer)
    fee_amount: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(20), index=True)  # SUCCESS/FAILED (MVP)
    journal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ledger_journals.id"), nullable=True)

    # Important: buat unik per sender (kita akan prefix sender_user_id di service)
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)

    note: Mapped[str | None] = mapped_column(String(255), nullable=True)