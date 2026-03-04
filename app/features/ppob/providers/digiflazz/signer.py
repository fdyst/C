# app/features/ppob/providers/digiflazz/signer.py
import hashlib

def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def sign_pricelist(username: str, api_key: str) -> str:
    # Digiflazz: md5(username + api_key + "pricelist")
    return md5_hex(f"{username}{api_key}pricelist")

def sign_transaction(username: str, api_key: str, ref_id: str) -> str:
    # Digiflazz: md5(username + api_key + ref_id)
    return md5_hex(f"{username}{api_key}{ref_id}")