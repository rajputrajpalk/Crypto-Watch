from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from ..validators import validate_positive_price, validate_positive_quantity, validate_symbol


PriceSnapshot = Tuple[str, str, float]  # (timestamp_iso, symbol, price)


@dataclass
class Coin:
    symbol: str
    name: str = ''
    current_price: float = 0.0

    def __post_init__(self):
        self.symbol = validate_symbol(self.symbol)
        self.current_price = float(self.current_price)


@dataclass
class Portfolio:
    """Portfolio state held in memory as a dict."""

    holdings: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def add_coin(self, symbol: str, quantity: float, avg_buy_price: float) -> None:
        symbol = validate_symbol(symbol)
        quantity = validate_positive_quantity(quantity)
        avg_buy_price = validate_positive_price(avg_buy_price)

        if symbol not in self.holdings:
            self.holdings[symbol] = {
                'quantity': float(quantity),
                'avg_buy_price': float(avg_buy_price),
            }
            return

        # Weighted average buy price.
        prev_qty = self.holdings[symbol]['quantity']
        prev_avg = self.holdings[symbol]['avg_buy_price']
        new_total_qty = prev_qty + quantity
        new_avg = (prev_qty * prev_avg + quantity * avg_buy_price) / new_total_qty
        self.holdings[symbol]['quantity'] = float(new_total_qty)
        self.holdings[symbol]['avg_buy_price'] = float(new_avg)

    def set_quantity(self, symbol: str, quantity: float) -> None:
        symbol = validate_symbol(symbol)
        quantity = validate_positive_quantity(quantity)
        if symbol not in self.holdings:
            raise KeyError(f'Coin not in portfolio: {symbol}')
        self.holdings[symbol]['quantity'] = float(quantity)

    def get_quantity(self, symbol: str) -> float:
        symbol = validate_symbol(symbol)
        return float(self.holdings.get(symbol, {}).get('quantity', 0.0))

    def valuation(self, latest_prices: Dict[str, float]) -> Dict[str, float]:
        # Use list comprehensions for dynamic P&L across holdings.
        items = [
            (sym, float(h['quantity']), float(h['avg_buy_price']), float(latest_prices.get(sym, 0.0)))
            for sym, h in self.holdings.items()
        ]

        costs = [qty * avg for _, qty, avg, _ in items]
        values = [qty * price for _, qty, _, price in items]

        total_cost = math.fsum(costs)
        total_value = math.fsum(values)
        pnl_abs = total_value - total_cost
        pnl_pct = (pnl_abs / total_cost * 100.0) if total_cost else 0.0

        return {
            'total_cost': float(total_cost),
            'total_value': float(total_value),
            'pnl_abs': float(pnl_abs),
            'pnl_pct': float(pnl_pct),
        }


@dataclass
class PriceAlert:
    symbol: str
    target_price: float
    alert_type: str  # 'above' | 'below'
    is_triggered: bool = False

    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    triggered_at: Optional[str] = None

    def __post_init__(self):
        self.symbol = validate_symbol(self.symbol)
        self.target_price = validate_positive_price(self.target_price)
        if self.alert_type not in ('above', 'below'):
            raise ValueError('alert_type must be above/below')

