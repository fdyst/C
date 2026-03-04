# app/features/ppob/pricing.py
def apply_markup(price_base: int, *, category: str) -> int:
    """
    MVP: markup sederhana.
    Nanti bisa dibuat per user tier / per produk / per jam.
    """
    category = category.upper()

    if category == "PULSA":
        return price_base + 500   # contoh
    if category == "GAME":
        return price_base + 1000  # contoh

    return price_base + 500