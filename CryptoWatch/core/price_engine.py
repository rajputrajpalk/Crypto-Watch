from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from CryptoWatch import settings

from .mock_feed import MockPriceFeed
from .repositories import AlertsRepository, PortfolioRepository
from .domain.exceptions import UnknownCoinSymbolError, UnsupportedAssetWarning



class PriceEngine:
    """Background thread that updates Redis price history and triggers alerts.

    Safety: catches UnsupportedAssetWarning and continues.
    """


    def __init__(self, interval_seconds: int | float | None = None):
        self.interval_seconds = float(interval_seconds or settings.PRICE_ENGINE_INTERVAL_SECONDS)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self.feed = MockPriceFeed(json_path=Path(settings.BASE_DIR) / 'mock_prices.json')
        self.repo_portfolio = PortfolioRepository()
        self.repo_alerts = AlertsRepository()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name='PriceEngineThread', daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                now_epoch = time.time()
                now_iso = datetime.now(timezone.utc).isoformat()

                prices = self.feed.read_prices()  # may raise UnknownCoinSymbolError only when queried per-symbol

                # 1) Append price history for every symbol into Redis ZSET.
                for symbol, price in prices.items():
                    self.repo_portfolio.log_price(symbol=symbol, price=price, epoch=now_epoch)

                # 2) Trigger alerts.
                current_prices = prices
                for alert in self.repo_alerts.list_alerts().get('alerts', []):
                    if alert.get('is_triggered'):
                        continue

                    sym = alert['symbol']
                    if sym not in current_prices:
                        raise UnsupportedAssetWarning(sym)

                    target = float(alert['target_price'])
                    alert_type = alert['alert_type']
                    current_price = float(current_prices.get(sym, 0.0))

                    crossed = (current_price >= target) if alert_type == 'above' else (current_price <= target)
                    if crossed:
                        self.repo_alerts.mark_triggered(symbol=sym, triggered_at=now_iso)

                time.sleep(self.interval_seconds)
            except UnsupportedAssetWarning:
                # Silently ignore unsupported assets and continue running.
                continue
            except Exception:
                # Safety isolation: never let the engine thread crash the server.
                # In real production, you'd log via a logger.
                continue


