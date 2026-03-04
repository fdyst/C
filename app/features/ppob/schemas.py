# app/features/ppob/schemas.py
from pydantic import BaseModel, Field


class ProductItem(BaseModel):
    sku_code: str
    name: str
    category: str
    price_sell: int
    is_active: int


class ProductListResponse(BaseModel):
    items: list[ProductItem]


class CreateOrderRequest(BaseModel):
    sku_code: str = Field(min_length=1, max_length=80)
    customer_no: str = Field(min_length=3, max_length=80)
    pin: str = Field(min_length=6, max_length=6)


class OrderResponse(BaseModel):
    id: str
    status: str
    sku_code: str
    customer_no: str
    price_sell: int
    provider_ref_id: str
    message: str | None = None
    sn: str | None = None
    
    
class OrderListResponse(BaseModel):
    items: list[OrderResponse]

class AdminPendingOrderItem(BaseModel):
    id: str
    user_id: str
    status: str
    sku_code: str
    customer_no: str
    price_sell: int
    provider_ref_id: str
    message: str | None = None


class AdminPendingOrdersResponse(BaseModel):
    items: list[AdminPendingOrderItem]