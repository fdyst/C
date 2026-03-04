# app/features/wallet/routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.features.wallet.models import LedgerJournal, LedgerEntry
from app.features.wallet.enums import AccountType
from app.features.wallet.repository import WalletRepository
from app.features.wallet.service import WalletService
from app.features.wallet.schemas import BalanceResponse, MutationsResponse, MutationItem

router = APIRouter()


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    summary = WalletService(db).get_summary(current_user.id)
    return BalanceResponse(**summary)
    

@router.get("/mutations", response_model=MutationsResponse)
def get_mutations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    repo = WalletRepository(db)
    wallet = repo.get_wallet_by_user_id(current_user.id)
    if not wallet:
        return MutationsResponse(items=[])

    # Tampilkan mutasi untuk USER_WALLET dan HOLDING (biar hold kelihatan)
    stmt = (
        select(LedgerEntry, LedgerJournal)
        .join(LedgerJournal, LedgerJournal.id == LedgerEntry.journal_id)
        .where(
            LedgerEntry.account_id == wallet.id,
            LedgerEntry.account_type.in_(["USER_WALLET", "HOLDING"]),
        )
        .order_by(LedgerEntry.id.desc())
        .limit(100)
    )

    rows = db.execute(stmt).all()

    items: list[MutationItem] = []
    for entry, journal in rows:
        items.append(
            MutationItem(
                journal_id=journal.id,
                journal_type=journal.type,
                account_type=entry.account_type,
                direction=entry.direction,
                amount=entry.amount,
                description=journal.description,
            )
        )

    return MutationsResponse(items=items)