from decimal import Decimal, ROUND_HALF_UP
import re


# Initial KES tariffs are illustrative defaults. Confirm and configure these with
# MAKOS SACCO before using them to quote or collect real payments.
PRICE_RULES = {
    "documents": {"base": Decimal("100.00"), "per_kg": Decimal("25.00")},
    "clothing": {"base": Decimal("150.00"), "per_kg": Decimal("40.00")},
    "electronics": {"base": Decimal("250.00"), "per_kg": Decimal("75.00")},
    "fragile": {"base": Decimal("300.00"), "per_kg": Decimal("80.00")},
    "general": {"base": Decimal("200.00"), "per_kg": Decimal("50.00")},
}

CATEGORY_KEYWORDS = {
    "documents": ["document", "documents", "paper", "papers", "envelope", "letter"],
    "clothing": ["clothing", "clothes", "shirt", "trouser", "dress", "fabric", "shoes"],
    "electronics": ["electronic", "electronics", "phone", "laptop", "computer", "tablet", "charger"],
    "fragile": ["fragile", "glass", "ceramic", "bottle", "breakable"],
}


def get_parcel_category(description):
    """Classify a parcel using simple description keywords; unknown contents are general."""
    words = set(re.findall(r"[a-z0-9]+", (description or "").lower()))
    # Fragile handling takes precedence over the ordinary item category.
    for category in ("fragile", "electronics", "clothing", "documents"):
        if words.intersection(CATEGORY_KEYWORDS[category]):
            return category
    return "general"


def calculate_delivery_fee(description, weight_kg):
    """Return the initial description-category plus weight-based KES estimate."""
    category = get_parcel_category(description)
    rule = PRICE_RULES[category]
    fee = rule["base"] + (rule["per_kg"] * Decimal(weight_kg))
    return fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
