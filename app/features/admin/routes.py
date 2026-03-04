# app/features/admin/routes.py
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import require_admin_key
from app.features.users.repository import UserRepository
from app.features.wallet.repository import WalletRepository
from app.features.wallet.service import WalletService, SYSTEM_ACCOUNT_ID
from app.features.wallet.enums import JournalType, AccountType
from app.features.admin.schemas import AdminTopupRequest, AdminTopupResponse

router = APIRouter()


@router.post("/topup", response_model=AdminTopupResponse, dependencies=[Depends(require_admin_key)])
def admin_topup(
    payload: AdminTopupRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """
    Admin manual topup.
    Required header:
    - X-Admin-Key: <ADMIN_API_KEY>
    Recommended header:
    - Idempotency-Key: <unique-string>
    """
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

    users = UserRepository(db)
    user = users.get_by_phone(payload.phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    wallet_service = WalletService(db)
    wallet_repo = WalletRepository(db)

    # Ensure wallet exists (should already be created on register)
    wallet_id = wallet_service.ensure_wallet(user.id)

    # Post journal: DEBIT SYSTEM, CREDIT USER_WALLET
    journal_id = wallet_service.post_double_entry(
        journal_type=JournalType.ADMIN_TOPUP,
        idempotency_key=idempotency_key,
        description=payload.description or f"Admin topup to {payload.phone}",
        reference_id=user.id,
        debit_account_type=AccountType.SYSTEM,
        debit_account_id=SYSTEM_ACCOUNT_ID,
        credit_account_type=AccountType.USER_WALLET,
        credit_account_id=wallet_id,
        amount=payload.amount,
    )

    db.commit()

    return AdminTopupResponse(
        journal_id=journal_id,
        credited_user_id=user.id,
        wallet_id=wallet_id,
        amount=payload.amount,
    )