# app/features/transfers/schemas.py
from pydantic import BaseModel, Field


class TransferCreateRequest(BaseModel):
    receiver_phone: str = Field(min_length=8, max_length=20)
    amount: int = Field(gt=0)
    pin: str = Field(min_length=6, max_length=6)
    note: str | None = Field(default=None, max_length=255)


class TransferResponse(BaseModel):
    id: str
    status: str
    amount: int
    fee_amount: int
    sender_user_id: str
    receiver_user_id: str
    journal_id: str | None = None
    note: str | None = None