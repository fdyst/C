# app/features/admin/schemas.py
from pydantic import BaseModel, Field

class AdminTopupRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    amount: int = Field(gt=0)  # rupiah integer
    description: str | None = None

class AdminTopupResponse(BaseModel):
    journal_id: str
    credited_user_id: str
    wallet_id: str
    amount: int