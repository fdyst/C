# app/features/ppob/models.py
import uuid
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PPOBProduct(Base):
    __tablename__ = "ppob_products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider: Mapped[str] = mapped_column(String(20), default="DIGIFLAZZ", index=True)

    sku_code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(30), index=True)  # PULSA / GAME (dll)

    price_base: Mapped[int] = mapped_column(Integer, default=0)  # dari digiflazz
    price_sell: Mapped[int] = mapped_column(Integer, default=0)  # harga jual kamu

    is_active: Mapped[int] = mapped_column(Integer, default=1)   # 1/0 biar aman di SQLite


class PPOBOrder(Base):
    __tablename__ = "ppob_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    sku_code: Mapped[str] = mapped_column(String(80), index=True)
    customer_no: Mapped[str] = mapped_column(String(80), index=True)

    price_sell: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), index=True)  # CREATED/PENDING/SUCCESS/FAILED

    # Digiflazz fields
    provider_ref_id: Mapped[str] = mapped_column(String(80), index=True)  # ref_id kita (unik per order)
    message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sn: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Ledger journals
    hold_journal_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    final_journal_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # Idempotency client (scoped by user di service)
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)