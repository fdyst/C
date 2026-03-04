# app/features/ppob/providers/digiflazz/client.py
from typing import Any
import httpx

from app.core.config import settings
from app.features.ppob.providers.digiflazz.signer import sign_pricelist, sign_transaction


class DigiflazzClient:
    def __init__(self):
        self.base_url = settings.digiflazz_base_url.rstrip("/")
        self.username = settings.digiflazz_username
        self.api_key = settings.digiflazz_api_key

    def _check_config(self) -> None:
        if not self.username or not self.api_key:
            raise RuntimeError("Digiflazz config missing: DIGIFLAZZ_USERNAME / DIGIFLAZZ_API_KEY")

    async def pricelist(self) -> dict[str, Any]:
        self._check_config()
        url = f"{self.base_url}/price-list"
        payload = {
            "cmd": "prepaid",
            "username": self.username,
            "sign": sign_pricelist(self.username, self.api_key),
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return r.json()

    async def buy(self, *, buyer_sku_code: str, customer_no: str, ref_id: str) -> dict[str, Any]:
        self._check_config()
        url = f"{self.base_url}/transaction"
        payload = {
            "username": self.username,
            "buyer_sku_code": buyer_sku_code,
            "customer_no": customer_no,
            "ref_id": ref_id,
            "sign": sign_transaction(self.username, self.api_key, ref_id),
        }
        async with httpx.AsyncClient(timeout=25) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return r.json()

    async def check_status(self, *, ref_id: str) -> dict[str, Any]:
        """
        Cek status transaksi berdasarkan ref_id.
        Catatan: beberapa akun Digiflazz bisa beda 'cmd'. Kalau respons tidak sesuai,
        kamu bisa adjust 'cmd' (mis. 'status') sesuai dokumentasi akunmu.
        """
        self._check_config()
        url = f"{self.base_url}/transaction"
        payload = {
            "cmd": "status",
            "username": self.username,
            "ref_id": ref_id,
            "sign": sign_transaction(self.username, self.api_key, ref_id),
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return r.json()