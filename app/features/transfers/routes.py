# app/features/transfers/routes.py
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.features.transfers.schemas import TransferCreateRequest, TransferResponse
from app.features.transfers.service import TransferService
from app.features.transfers.repository import TransferRepository

router = APIRouter()


@router.post("", response_model=TransferResponse)
def create_transfer(
    payload: TransferCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    transfer = TransferService(db).create_transfer(
        sender_user_id=current_user.id,
        sender_pin_hash=current_user.pin_hash,
        receiver_phone=payload.receiver_phone,
        amount=payload.amount,
        pin=payload.pin,
        note=payload.note,
        idempotency_key=idempotency_key or "",
    )
    return TransferResponse(
        id=transfer.id,
        status=transfer.status,
        amount=transfer.amount,
        fee_amount=transfer.fee_amount,
        sender_user_id=transfer.sender_user_id,
        receiver_user_id=transfer.receiver_user_id,
        journal_id=transfer.journal_id,
        note=transfer.note,
    )


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(
    transfer_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    t = TransferRepository(db).get_by_id(transfer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transfer not found")

    # user hanya boleh lihat transfer yang dia terlibat
    if current_user.id not in (t.sender_user_id, t.receiver_user_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    return TransferResponse(
        id=t.id,
        status=t.status,
        amount=t.amount,
        fee_amount=t.fee_amount,
        sender_user_id=t.sender_user_id,
        receiver_user_id=t.receiver_user_id,
        journal_id=t.journal_id,
        note=t.note,
    )