# app/features/auth/service.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token, hash_pin
from app.features.users.repository import UserRepository
from app.features.wallet.service import WalletService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, *, phone: str, username: str, password: str) -> str:
        if self.users.get_by_phone(phone):
            raise HTTPException(status_code=400, detail="Phone already used")
        if self.users.get_by_username(username):
            raise HTTPException(status_code=400, detail="Username already used")

        user = self.users.create(
            phone=phone,
            username=username,
            password_hash=hash_password(password),
        )
        self.db.flush()
        WalletService(self.db).ensure_wallet(user.id)
        
        self.db.commit()
        self.db.refresh(user)
        return create_access_token(subject=user.id)

    def login(self, *, phone: str, password: str) -> str:
        user = self.users.get_by_phone(phone)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone or password",
            )

        return create_access_token(subject=user.id)

    def set_pin(self, *, user_id: str, pin: str) -> None:
        user = self.users.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.pin_hash = hash_pin(pin)
        self.db.commit()