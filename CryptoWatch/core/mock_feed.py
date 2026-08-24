import json
import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .domain.exceptions import UnknownCoinSymbolError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MockPriceFeed:
    """Generates simulated live cryptocurrency prices with realistic market volatility."""

    json_path: Path

    def read_prices(self) -> Dict[str, float]:
        """Read base asset prices and apply dynamic market drift."""
        try:
            raw_text = self.json_path.read_text(encoding='utf-8')
            base_prices: Dict[str, float] = json.loads(raw_text)
        except Exception as exc:
            logger.error("Failed to read price feed from %s: %s", self.json_path, exc)
            return {}

        prices: Dict[str, float] = {}
        for symbol, base_val in base_prices.items():
            base = float(base_val)
            # Apply ±1.2% random drift per tick for realistic movement
            drift_factor = 1.0 + random.uniform(-0.012, 0.012)
            prices[symbol] = round(max(0.0001, base * drift_factor), 4)

        return prices

    def get_price(self, symbol: str) -> float:
        """Retrieve the live price of a specific cryptocurrency."""
        symbol = symbol.strip().upper()
        prices = self.read_prices()
        if symbol not in prices:
            raise UnknownCoinSymbolError(symbol)
        return prices[symbol]
