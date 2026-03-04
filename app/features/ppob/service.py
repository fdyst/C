# app/features/ppob/service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import verify_pin
from app.features.wallet.service import WalletService, SYSTEM_ACCOUNT_ID
from app.features.wallet.enums import JournalType, AccountType
from app.features.ppob.repository import PPOBRepository
from app.features.ppob.providers.digiflazz.client import DigiflazzClient
from app.features.ppob.pricing import apply_markup


class PPOBService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PPOBRepository(db)
        self.wallet = WalletService(db)
        self.dg = DigiflazzClient()

    async def sync_pricelist(self) -> int:
        """
        Sync price list Digiflazz -> ppob_products.
        MVP: ambil PREPAID, lalu simpan produk kategori PULSA & GAME saja.
        """
        data = await self.dg.pricelist()
        items = data.get("data") or []
        if not isinstance(items, list):
            raise HTTPException(status_code=502, detail="Invalid Digiflazz response (pricelist)")

        upserted = 0
        for it in items:
            try:
                # Digiflazz fields umumnya: buyer_sku_code, product_name, category, price, buyer_product_status
                sku = str(it.get("buyer_sku_code") or "").strip()
                name = str(it.get("product_name") or "").strip()
                category = str(it.get("category") or "").strip().upper()
                price_base = int(it.get("price") or 0)

                # Filter hanya PULSA + GAME untuk tahap ini
                if category not in ("PULSA", "GAME"):
                    continue

                # Active?
                # buyer_product_status biasanya True/False atau "1"/"0" tergantung data
                status_raw = it.get("buyer_product_status")
                is_active = 1 if str(status_raw).lower() in ("true", "1", "yes") else 0

                if not sku or not name or price_base <= 0:
                    continue

                price_sell = apply_markup(price_base, category=category)

                self.repo.upsert_product(
                    provider="DIGIFLAZZ",
                    sku_code=sku,
                    name=name,
                    category=category,
                    price_base=price_base,
                    price_sell=price_sell,
                    is_active=is_active,
                )
                upserted += 1
            except Exception:
                # Skip item yang rusak, jangan gagalin 1 batch
                continue

        self.db.commit()
        return upserted

    async def create_order_and_process(
        self,
        *,
        user_id: str,
        user_pin_hash: str | None,
        sku_code: str,
        customer_no: str,
        pin: str,
        idempotency_key: str,
    ):
        """
        Create order idempotent (scoped per user), HOLD saldo, call Digiflazz,
        lalu SETTLE / RELEASE.

        Header requirement: Idempotency-Key (dari routes)
        """
        if not idempotency_key:
            raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

        if not user_pin_hash:
            raise HTTPException(status_code=400, detail="PIN not set. Call /auth/set-pin first")

        if not verify_pin(pin, user_pin_hash):
            raise HTTPException(status_code=401, detail="Invalid PIN")

        product = self.repo.get_product_by_sku(sku_code)
        if not product or product.is_active != 1:
            raise HTTPException(status_code=404, detail="Product not found or inactive")

        # scope idempotency per user
        scoped_key = f"{user_id}:{idempotency_key}"

        # Idempotent: kalau sudah pernah create, return order existing
        existing = self.repo.get_order_by_idempotency(scoped_key)
        if existing:
            return existing

        # Pastikan wallet ada
        wallet_id = self.wallet.ensure_wallet(user_id)

        # cek balance available (USER_WALLET only)
        balance = self.wallet.get_balance(user_id)
        price_sell = int(product.price_sell)
        if price_sell <= 0:
            raise HTTPException(status_code=500, detail="Invalid product price configuration")

        if balance < price_sell:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        # STEP 1: create order + HOLD dalam 1 transaksi DB
        with self.db.begin():
            # ref_id untuk Digiflazz: pakai UUID order (kita set setelah flush)
            # create dulu dengan placeholder ref_id, lalu update setelah flush
            order = self.repo.create_order(
                user_id=user_id,
                sku_code=product.sku_code,
                customer_no=customer_no,
                price_sell=price_sell,
                status="PENDING",
                provider_ref_id="TEMP",
                idempotency_key=scoped_key,
            )
            self.db.flush()  # order.id kebentuk

            order.provider_ref_id = f"ppob-{order.id}"

            # HOLD: debit USER_WALLET -> credit HOLDING (account_id sama wallet_id)
            hold_journal_id = self.wallet.post_double_entry(
                journal_type=JournalType.PPOB,
                idempotency_key=f"{scoped_key}:hold",
                description=f"HOLD PPOB {product.category} {product.sku_code}",
                reference_id=order.id,
                debit_account_type=AccountType.USER_WALLET,
                debit_account_id=wallet_id,
                credit_account_type=AccountType.HOLDING,
                credit_account_id=wallet_id,
                amount=price_sell,
            )
            order.hold_journal_id = hold_journal_id

        # STEP 2: call provider di luar transaksi DB (biar gak nge-lock DB lama)
        try:
            resp = await self.dg.buy(
                buyer_sku_code=product.sku_code,
                customer_no=customer_no,
                ref_id=order.provider_ref_id,
            )
        except Exception:
            # Kalau network error: biarkan status tetap PENDING (saldo masih ke-hold)
            # Nanti bisa dibuat job poller untuk cek status/refund.
            with self.db.begin():
                order.status = "PENDING"
                order.message = "Provider timeout / network error. Pending."
            return order

        # STEP 3: interpret response Digiflazz
        data = resp.get("data") or {}
        status_raw = str(data.get("status") or "").upper()   # biasanya: Sukses/Gagal/Pending
        message = str(data.get("message") or "")
        sn = data.get("sn")
        sn_str = str(sn) if sn is not None else None

        # Normalisasi sederhana
        if "SUKSES" in status_raw or status_raw == "SUCCESS":
            final_status = "SUCCESS"
        elif "GAGAL" in status_raw or status_raw == "FAILED":
            final_status = "FAILED"
        else:
            final_status = "PENDING"

        # STEP 4: settle / release
        with self.db.begin():
            order.message = message
            order.sn = sn_str

            if final_status == "SUCCESS":
                # SETTLE: debit HOLDING -> credit SYSTEM
                final_journal_id = self.wallet.post_double_entry(
                    journal_type=JournalType.PPOB,
                    idempotency_key=f"{scoped_key}:settle",
                    description=f"SETTLE PPOB {product.category} {product.sku_code}",
                    reference_id=order.id,
                    debit_account_type=AccountType.HOLDING,
                    debit_account_id=wallet_id,
                    credit_account_type=AccountType.SYSTEM,
                    credit_account_id=SYSTEM_ACCOUNT_ID,
                    amount=price_sell,
                )
                order.final_journal_id = final_journal_id
                order.status = "SUCCESS"

            elif final_status == "FAILED":
                # RELEASE: debit HOLDING -> credit USER_WALLET (balikin saldo)
                final_journal_id = self.wallet.post_double_entry(
                    journal_type=JournalType.PPOB,
                    idempotency_key=f"{scoped_key}:release",
                    description=f"RELEASE PPOB {product.category} {product.sku_code}",
                    reference_id=order.id,
                    debit_account_type=AccountType.HOLDING,
                    debit_account_id=wallet_id,
                    credit_account_type=AccountType.USER_WALLET,
                    credit_account_id=wallet_id,
                    amount=price_sell,
                )
                order.final_journal_id = final_journal_id
                order.status = "FAILED"
            else:
                order.status = "PENDING"

        return order
        

    async def admin_recheck_order(self, *, order_id: str):
        order = self.repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Kalau sudah final, langsung return
        if order.status in ("SUCCESS", "FAILED"):
            return order

        # Ambil wallet id untuk posting settle/release
        wallet_id = self.wallet.ensure_wallet(order.user_id)
        amount = int(order.price_sell)

        # Call Digiflazz status check
        try:
            resp = await self.dg.check_status(ref_id=order.provider_ref_id)
        except Exception:
            raise HTTPException(status_code=502, detail="Failed to check status to provider")

        data = resp.get("data") or {}
        status_raw = str(data.get("status") or "").upper()
        message = str(data.get("message") or "")
        sn = data.get("sn")
        sn_str = str(sn) if sn is not None else None

        # Normalisasi
        if "SUKSES" in status_raw or status_raw == "SUCCESS":
            final_status = "SUCCESS"
        elif "GAGAL" in status_raw or status_raw == "FAILED":
            final_status = "FAILED"
        else:
            final_status = "PENDING"

        # scoped_key = order.idempotency_key sudah dalam format "{user_id}:{Idempotency-Key}"
        scoped_key = order.idempotency_key

        # Update + settle/release idempotent
        with self.db.begin():
            order.message = message
            order.sn = sn_str

            if final_status == "SUCCESS":
                final_journal_id = self.wallet.post_double_entry(
                    journal_type=JournalType.PPOB,
                    idempotency_key=f"{scoped_key}:settle",
                    description=f"SETTLE PPOB {order.sku_code}",
                    reference_id=order.id,
                    debit_account_type=AccountType.HOLDING,
                    debit_account_id=wallet_id,
                    credit_account_type=AccountType.SYSTEM,
                    credit_account_id=SYSTEM_ACCOUNT_ID,
                    amount=amount,
                )
                order.final_journal_id = final_journal_id
                order.status = "SUCCESS"

            elif final_status == "FAILED":
                final_journal_id = self.wallet.post_double_entry(
                    journal_type=JournalType.PPOB,
                    idempotency_key=f"{scoped_key}:release",
                    description=f"RELEASE PPOB {order.sku_code}",
                    reference_id=order.id,
                    debit_account_type=AccountType.HOLDING,
                    debit_account_id=wallet_id,
                    credit_account_type=AccountType.USER_WALLET,
                    credit_account_id=wallet_id,
                    amount=amount,
                )
                order.final_journal_id = final_journal_id
                order.status = "FAILED"
            else:
                order.status = "PENDING"

        return order
        

    def cancel_order_by_user(self, *, user_id: str, order_id: str):
        """
        User cancel order hanya jika masih PENDING.
        Aksi: RELEASE HOLDING -> USER_WALLET.
        Idempotent via ledger idempotency key.
        """
        order = self.repo.get_order_by_id(order_id)
        if not order or order.user_id != user_id:
            raise HTTPException(status_code=404, detail="Order not found")

        # Kalau sudah final, tidak bisa cancel
        if order.status in ("SUCCESS", "FAILED", "CANCELLED"):
            return order

        if order.status != "PENDING":
            raise HTTPException(status_code=400, detail=f"Order not cancellable (status={order.status})")

        # Jika sudah pernah ada final_journal_id, jangan cancel (sudah settle/release)
        if order.final_journal_id:
            return order

        wallet_id = self.wallet.ensure_wallet(order.user_id)
        amount = int(order.price_sell)
        if amount <= 0:
            raise HTTPException(status_code=500, detail="Invalid order amount")

        # order.idempotency_key formatnya "{user_id}:{client-idempotency}"
        scoped_key = order.idempotency_key

        with self.db.begin():
            # RELEASE: debit HOLDING -> credit USER_WALLET
            final_journal_id = self.wallet.post_double_entry(
                journal_type=JournalType.PPOB,
                idempotency_key=f"{scoped_key}:cancel-release",
                description=f"CANCEL PPOB {order.sku_code}",
                reference_id=order.id,
                debit_account_type=AccountType.HOLDING,
                debit_account_id=wallet_id,
                credit_account_type=AccountType.USER_WALLET,
                credit_account_id=wallet_id,
                amount=amount,
            )
            order.final_journal_id = final_journal_id
            order.status = "CANCELLED"
            order.message = "Cancelled by user"

        return order