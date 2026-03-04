# app/features/ppob/repository.py
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.features.ppob.models import PPOBProduct, PPOBOrder


class PPOBRepository:
    def __init__(self, db: Session):
        self.db = db

    # products
    def list_products(self, *, category: str | None = None) -> list[PPOBProduct]:
        stmt = select(PPOBProduct).where(PPOBProduct.is_active == 1)
        if category:
            stmt = stmt.where(PPOBProduct.category == category.upper())
        stmt = stmt.order_by(PPOBProduct.category.asc(), PPOBProduct.price_sell.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_product_by_sku(self, sku_code: str) -> PPOBProduct | None:
        return self.db.execute(
            select(PPOBProduct).where(PPOBProduct.sku_code == sku_code)
        ).scalar_one_or_none()

    def upsert_product(
        self,
        *,
        provider: str,
        sku_code: str,
        name: str,
        category: str,
        price_base: int,
        price_sell: int,
        is_active: int,
    ) -> PPOBProduct:
        p = self.get_product_by_sku(sku_code)
        if p:
            p.provider = provider
            p.name = name
            p.category = category.upper()
            p.price_base = price_base
            p.price_sell = price_sell
            p.is_active = is_active
            return p

        p = PPOBProduct(
            provider=provider,
            sku_code=sku_code,
            name=name,
            category=category.upper(),
            price_base=price_base,
            price_sell=price_sell,
            is_active=is_active,
        )
        self.db.add(p)
        return p

    # orders
    def get_order_by_id(self, order_id: str) -> PPOBOrder | None:
        return self.db.get(PPOBOrder, order_id)

    def get_order_by_idempotency(self, idempotency_key: str) -> PPOBOrder | None:
        return self.db.execute(
            select(PPOBOrder).where(PPOBOrder.idempotency_key == idempotency_key)
        ).scalar_one_or_none()

    def create_order(
        self,
        *,
        user_id: str,
        sku_code: str,
        customer_no: str,
        price_sell: int,
        status: str,
        provider_ref_id: str,
        idempotency_key: str,
    ) -> PPOBOrder:
        o = PPOBOrder(
            user_id=user_id,
            sku_code=sku_code,
            customer_no=customer_no,
            price_sell=price_sell,
            status=status,
            provider_ref_id=provider_ref_id,
            idempotency_key=idempotency_key,
        )
        self.db.add(o)
        return o
        
    def get_order_by_id_and_user(self, *, order_id: str, user_id: str) -> PPOBOrder | None:
        return self.db.execute(
            select(PPOBOrder).where(
                PPOBOrder.id == order_id,
                PPOBOrder.user_id == user_id,
            )
        ).scalar_one_or_none()

    def list_orders_by_user(self, *, user_id: str, limit: int = 20) -> list[PPOBOrder]:
        limit = max(1, min(limit, 100))
        stmt = (
            select(PPOBOrder)
            .where(PPOBOrder.user_id == user_id)
            .order_by(PPOBOrder.id.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
        
    def list_pending_orders(self, *, limit: int = 50) -> list[PPOBOrder]:
        limit = max(1, min(limit, 200))
        stmt = (
            select(PPOBOrder)
            .where(PPOBOrder.status == "PENDING")
            .order_by(PPOBOrder.id.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())