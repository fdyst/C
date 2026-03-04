# app/features/auth/routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import rate_limit_dep
from app.api.v1.deps import get_current_user
from app.features.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, SetPinRequest
from app.features.auth.service import AuthService

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    token = AuthService(db).register(
        phone=payload.phone,
        username=payload.username,
        password=payload.password,
    )
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_dep(prefix="login", limit=settings.rate_limit_login_per_minute))],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token = AuthService(db).login(phone=payload.phone, password=payload.password)
    return TokenResponse(access_token=token)


@router.post(
    "/set-pin",
    dependencies=[Depends(rate_limit_dep(prefix="set_pin", limit=settings.rate_limit_pin_per_minute))],
)
def set_pin(
    payload: SetPinRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    AuthService(db).set_pin(user_id=current_user.id, pin=payload.pin)
    return {"status": "ok"}