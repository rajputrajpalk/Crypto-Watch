from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from ..validators import validate_positive_price, validate_positive_quantity, validate_symbol


@dataclass
class Coin:
    """Represents a cryptocurrency coin and its market price."""
    symbol: str
    name: str = ""
    current_price: float = 0.0

    def __post_init__(self):
        self.symbol = validate_symbol(self.symbol)
        self.current_price = float(self.current_price)


@dataclass
class Holding:
    """Represents an active asset position in a user's portfolio."""
    symbol: str
    quantity: float
    avg_buy_price: float

    def __post_init__(self):
        self.symbol = validate_symbol(self.symbol)
        self.quantity = validate_positive_quantity(self.quantity)
        self.avg_buy_price = validate_positive_price(self.avg_buy_price)

    @property
    def cost(self) -> float:
        return self.quantity * self.avg_buy_price

    def current_value(self, market_price: float) -> float:
        return self.quantity * market_price

    def pnl(self, market_price: float) -> tuple[float, float]:
        val = self.current_value(market_price)
        cost = self.cost
        pnl_abs = val - cost
        pnl_pct = (pnl_abs / cost * 100.0) if cost > 0 else 0.0
        return pnl_abs, pnl_pct


@dataclass
class PriceAlert:
    """Represents a user price threshold trigger."""
    symbol: str
    target_price: float
    alert_type: str  # 'above' | 'below' | 'increase' | 'decrease'
    is_triggered: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    triggered_at: Optional[str] = None

    def __post_init__(self):
        self.symbol = validate_symbol(self.symbol)
        self.target_price = validate_positive_price(self.target_price)
        if self.alert_type not in ('above', 'below', 'increase', 'decrease'):
            raise ValueError("alert_type must be one of: above, below, increase, decrease")
