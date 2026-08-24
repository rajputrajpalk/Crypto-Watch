import re
from typing import Union

COIN_SYMBOL_PATTERN = re.compile(r'^[A-Z]{3,10}$')


def validate_symbol(symbol: str) -> str:
    """Validate and sanitize a cryptocurrency ticker symbol (e.g., BTC, ETH, SOL)."""
    if not isinstance(symbol, str):
        raise ValueError("Symbol must be a valid string")
    cleaned = symbol.strip().upper()
    if not COIN_SYMBOL_PATTERN.match(cleaned):
        raise ValueError(f"Invalid coin symbol '{cleaned}'. Must be 3-10 uppercase letters.")
    return cleaned


def validate_positive_quantity(quantity: Union[int, float, str]) -> float:
    """Validate that the quantity is a positive number greater than zero."""
    try:
        val = float(quantity)
    except (TypeError, ValueError):
        raise ValueError("Quantity must be a valid numeric value")

    if val <= 0:
        raise ValueError("Quantity must be strictly greater than 0")
    return val


def validate_positive_price(price: Union[int, float, str]) -> float:
    """Validate that the price is a positive number greater than zero."""
    try:
        val = float(price)
    except (TypeError, ValueError):
        raise ValueError("Price must be a valid numeric value")

    if val <= 0:
        raise ValueError("Price must be strictly greater than 0")
    return val
