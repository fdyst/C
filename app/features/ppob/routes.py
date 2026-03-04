# app/features/ppob/routes.py
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
# app/features/ppob/routes.py (tambahan)
from fastapi import Query
from app.api.v1.deps import get_current_user
from app.features.ppob.schemas import OrderListResponse
from app.features.ppob.repository import PPOBRepository

# ... (router tetap)
from app.core.database import get_db
from app.api.v1.deps import get_current_user, require_admin_key
from app.features.ppob.schemas import (
    ProductListResponse,
    ProductItem,
    CreateOrderRequest,
    OrderResponse,
    OrderListResponse,
    AdminPendingOrdersResponse,
    AdminPendingOrderItem,
)
from app.features.ppob.repository import PPOBRepository
from app.features.ppob.service import PPOBService

router = APIRouter()


@router.get("/products", response_model=ProductListResponse)
def list_products(
    db: Session = Depends(get_db),
    category: str | None = Query(default=None, description="PULSA or GAME"),
):
    items = PPOBRepository(db).list_products(category=category)
    return ProductListResponse(
        items=[
            ProductItem(
                sku_code=p.sku_code,
                name=p.name,
                category=p.category,
                price_sell=p.price_sell,
                is_active=p.is_active,
            )
            for p in items
        ]
    )


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    payload: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

    order = await PPOBService(db).create_order_and_process(
        user_id=current_user.id,
        user_pin_hash=current_user.pin_hash,
        sku_code=payload.sku_code,
        customer_no=payload.customer_no,
        pin=payload.pin,
        idempotency_key=idempotency_key,
    )

    return OrderResponse(
        id=order.id,
        status=order.status,
        sku_code=order.sku_code,
        customer_no=order.customer_no,
        price_sell=order.price_sell,
        provider_ref_id=order.provider_ref_id,
        message=order.message,
        sn=order.sn,
    )


@router.post("/admin/sync-pricelist", dependencies=[Depends(require_admin_key)])
async def admin_sync_pricelist(
    db: Session = Depends(get_db),
):
    upserted = await PPOBService(db).sync_pricelist()
    return {"status": "ok", "upserted": upserted}
    

@router.post("/admin/recheck/{order_id}", response_model=OrderResponse, dependencies=[Depends(require_admin_key)])
async def admin_recheck_order(
    order_id: str,
    db: Session = Depends(get_db),
):
    order = await PPOBService(db).admin_recheck_order(order_id=order_id)
    return OrderResponse(
        id=order.id,
        status=order.status,
        sku_code=order.sku_code,
        customer_no=order.customer_no,
        price_sell=order.price_sell,
        provider_ref_id=order.provider_ref_id,
        message=order.message,
        sn=order.sn,
    )
    


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_my_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order = PPOBRepository(db).get_order_by_id_and_user(order_id=order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse(
        id=order.id,
        status=order.status,
        sku_code=order.sku_code,
        customer_no=order.customer_no,
        price_sell=order.price_sell,
        provider_ref_id=order.provider_ref_id,
        message=order.message,
        sn=order.sn,
    )


@router.get("/orders", response_model=OrderListResponse)
def list_my_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
):
    orders = PPOBRepository(db).list_orders_by_user(user_id=current_user.id, limit=limit)

    return OrderListResponse(
        items=[
            OrderResponse(
                id=o.id,
                status=o.status,
                sku_code=o.sku_code,
                customer_no=o.customer_no,
                price_sell=o.price_sell,
                provider_ref_id=o.provider_ref_id,
                message=o.message,
                sn=o.sn,
            )
            for o in orders
        ]
    )

@router.get(
    "/admin/orders/pending",
    response_model=AdminPendingOrdersResponse,
    dependencies=[Depends(require_admin_key)],
)
def admin_list_pending_orders(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
):
    orders = PPOBRepository(db).list_pending_orders(limit=limit)
    return AdminPendingOrdersResponse(
        items=[
            AdminPendingOrderItem(
                id=o.id,
                user_id=o.user_id,
                status=o.status,
                sku_code=o.sku_code,
                customer_no=o.customer_no,
                price_sell=o.price_sell,
                provider_ref_id=o.provider_ref_id,
                message=o.message,
            )
            for o in orders
        ]
    )


@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_my_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order = PPOBService(db).cancel_order_by_user(user_id=current_user.id, order_id=order_id)
    return OrderResponse(
        id=order.id,
        status=order.status,
        sku_code=order.sku_code,
        customer_no=order.customer_no,
        price_sell=order.price_sell,
        provider_ref_id=order.provider_ref_id,
        message=order.message,
        sn=order.sn,
    )
