# app/features/users/repository.py
from sqlalchemy.orm import Session
from app.features.users.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_by_phone(self, phone: str) -> User | None:
        return self.db.query(User).filter(User.phone == phone).first()

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def create(self, *, phone: str, username: str, password_hash: str) -> User:
        user = User(phone=phone, username=username, password_hash=password_hash)
        self.db.add(user)
        return user