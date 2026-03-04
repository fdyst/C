# app/core/database.py (patch bagian engine)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

def _normalize_db_url(url: str) -> str:
    # Railway sering kasih "postgresql://"
    # Kita pakai psycopg driver => "postgresql+psycopg://"
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

db_url = _normalize_db_url(settings.database_url)

engine = create_engine(
    db_url,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def init_db() -> None:
    from app.features.users.models import User  # noqa: F401
    from app.features.wallet.models import Wallet, LedgerJournal, LedgerEntry  # noqa: F401
    from app.features.transfers.models import Transfer  # noqa: F401
    from app.features.ppob.models import PPOBProduct, PPOBOrder  # noqa: F401

    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()