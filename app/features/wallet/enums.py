# app/features/wallet/enums.py
from enum import StrEnum

class JournalType(StrEnum):
    ADMIN_TOPUP = "ADMIN_TOPUP"
    TRANSFER = "TRANSFER"
    PPOB = "PPOB"

class JournalStatus(StrEnum):
    POSTED = "POSTED"
    FAILED = "FAILED"

class AccountType(StrEnum):
    USER_WALLET = "USER_WALLET"
    HOLDING = "HOLDING"     # <-- tambahan untuk reserve saldo
    SYSTEM = "SYSTEM"

class EntryDirection(StrEnum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"