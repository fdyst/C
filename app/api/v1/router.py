from fastapi import APIRouter
from app.features.auth.routes import router as auth_router
from app.features.wallet.routes import router as wallet_router
from app.features.admin.routes import router as admin_router
from app.features.transfers.routes import router as transfers_router
from app.features.ppob.routes import router as ppob_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(wallet_router, prefix="/wallet", tags=["wallet"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(transfers_router, prefix="/transfers", tags=["transfers"])
api_router.include_router(ppob_router, prefix="/ppob", tags=["ppob"])