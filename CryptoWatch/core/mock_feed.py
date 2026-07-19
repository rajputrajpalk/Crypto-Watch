from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .domain.exceptions import UnknownCoinSymbolError


@dataclass(frozen=True)
class MockPriceFeed:
    """Produces dynamic mock prices.

    Base prices are loaded from mock_prices.json, then each call perturbs them with
    a small deterministic-random factor so values change frequently.
    """

    json_path: Path

    def read_prices(self) -> Dict[str, float]:
        base_raw = json.loads(self.json_path.read_text(encoding='utf-8'))
        base = {k: float(v) for k, v in base_raw.items()}

        # Perturb each symbol slightly so the dashboard shows changing prices.
        # We use a high-resolution time seed so values change on frequent calls.
        import random
        import time

        seed = time.time_ns()
        rnd = random.Random(seed)


        out: Dict[str, float] = {}
        for sym, price in base.items():
            # ±1% move per tick
            drift = rnd.uniform(-0.01, 0.01)
            out[sym] = float(max(0.0, price * (1.0 + drift)))

        return out

    def get_price(self, symbol: str) -> float:
        prices = self.read_prices()
        if symbol not in prices:
            raise UnknownCoinSymbolError(symbol)
        return float(prices[symbol])


