import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from django.conf import settings

from .mock_feed import MockPriceFeed
from .repositories import AlertsRepository, PortfolioRepository

logger = logging.getLogger(__name__)


class PriceEngine:
    """Background engine that polls simulated price feeds, updates price histories,

    and evaluates threshold alerts.
    """

    def __init__(self, interval_seconds: Optional[float] = None):
        default_interval = getattr(settings, 'PRICE_ENGINE_INTERVAL_SECONDS', 5)
        self.interval = float(interval_seconds or default_interval)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        feed_path = Path(settings.BASE_DIR) / 'mock_prices.json'
        self.feed = MockPriceFeed(json_path=feed_path)
        self.portfolio_repo = PortfolioRepository()
        self.alerts_repo = AlertsRepository()

    def start(self) -> None:
        """Start the background worker thread if not already running."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._worker_loop,
            name='PriceEngineWorker',
            daemon=True,
        )
        self._thread.start()
        logger.info("PriceEngine background worker started (interval: %.1fs)", self.interval)

    def stop(self, timeout: float = 2.0) -> None:
        """Signal worker to stop and wait for termination."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            logger.info("PriceEngine background worker stopped")

    def _worker_loop(self) -> None:
        """Main execution loop for the price engine."""
        while not self._stop_event.is_set():
            try:
                self.tick()
            except Exception as exc:
                logger.error("Unexpected error in PriceEngine tick: %s", exc, exc_info=True)

            # Responsive sleep that exits promptly if stopped
            self._stop_event.wait(self.interval)

    def tick(self) -> None:
        """Execute a single polling and evaluation cycle."""
        now_epoch = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()

        prices = self.feed.read_prices()
        if not prices:
            return

        # 1. Record historical price points
        for symbol, price in prices.items():
            self.portfolio_repo.log_price(symbol=symbol, price=price, epoch=now_epoch)

        # 2. Evaluate active alerts
        active_alerts = self.alerts_repo.list_alerts().get('alerts', [])
        for alert in active_alerts:
            if alert.get('is_triggered'):
                continue

            symbol = alert.get('symbol')
            if symbol not in prices:
                continue

            target_price = float(alert.get('target_price', 0.0))
            alert_type = str(alert.get('alert_type', '')).lower()
            current_price = float(prices[symbol])

            is_crossed = False
            if alert_type in ('above', 'increase'):
                is_crossed = current_price >= target_price
            elif alert_type in ('below', 'decrease'):
                is_crossed = current_price <= target_price

            if is_crossed:
                logger.info(
                    "Alert triggered: %s crossed target $%.2f (Current: $%.2f)",
                    symbol, target_price, current_price
                )
                self.alerts_repo.mark_triggered(symbol=symbol, triggered_at=now_iso)
