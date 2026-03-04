from pydantic import BaseModel


class BalanceResponse(BaseModel):
    currency: str = "IDR"
    available_balance: int
    hold_balance: int
    total_balance: int


class MutationItem(BaseModel):
    journal_id: str
    journal_type: str

    account_type: str          # USER_WALLET / HOLDING / SYSTEM (kalau nanti kamu expose)
    direction: str             # DEBIT / CREDIT
    amount: int

    description: str | None = None


class MutationsResponse(BaseModel):
    items: list[MutationItem]