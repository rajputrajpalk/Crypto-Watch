from __future__ import annotations

import re
from decimal import Decimal
from typing import Union


COIN_SYMBOL_RE = re.compile(r'^[A-Z]{3,5}$')


def validate_symbol(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise ValueError('symbol must be a string')
    symbol = symbol.strip().upper()
    if not COIN_SYMBOL_RE.match(symbol):
        raise ValueError('Invalid coin symbol. Must match ^[A-Z]{3,5}$')
    return symbol


def validate_positive_quantity(qty: Union[int, float, str]) -> float:
    # Accept ints/floats/strings that parse to positive numbers.
    try:
        val = float(qty)
    except (TypeError, ValueError):
        raise ValueError('quantity must be a positive number')

    if val <= 0:
        raise ValueError('quantity must be > 0')
    return val


def validate_positive_price(price: Union[int, float, str]) -> float:
    try:
        val = float(price)
    except (TypeError, ValueError):
        raise ValueError('price must be a positive number')

    if val <= 0:
        raise ValueError('price must be > 0')
    return val

