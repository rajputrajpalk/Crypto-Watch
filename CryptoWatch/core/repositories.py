from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import json
import time

from CryptoWatch.settings import REDIS_DB, REDIS_HOST, REDIS_PREFIX, REDIS_PORT

from redis import Redis

from .repositories_fallback import InMemoryAlertsRepository, InMemoryPortfolioRepository
from .domain.exceptions import UnknownCoinSymbolError


class RedisHandle:
    def __init__(self):
        self.client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

    def key(self, *parts: str) -> str:
        return ':'.join([REDIS_PREFIX, *parts])


    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except Exception:
            return False


def _redis_available() -> bool:
    rh = RedisHandle()
    return rh.ping()



class PortfolioRepository:
    """Repository layer for Redis-backed domain state.

    If Redis is unavailable, falls back to an in-memory implementation so the project remains executable.
    """

    def __init__(self):
        if not _redis_available():
            self._fallback = InMemoryPortfolioRepository()
            return

        self._fallback = None
        self.rh = RedisHandle()
        # Single user demo: user_id=55 as requested in pattern.
        self.user_id = 55

        # Redis Hash:
        # portfolio:user:55 -> {"BTC": "{quantity,avg_buy_price}", ...}
        self.k_portfolio = self.rh.key('portfolio', f'user:{self.user_id}')

    def _z_hist_key(self, symbol: str) -> str:

        # prices:history:BTC
        return self.rh.key('prices', 'history', symbol)

    def log_price(self, symbol: str, price: float, epoch: float) -> None:
        if self._fallback is not None:
            return self._fallback.log_price(symbol=symbol, price=price, epoch=epoch)

        # Store in ZSET: member=price, score=epoch
        self.rh.client.zadd(self._z_hist_key(symbol), {str(float(price)): float(epoch)})
        # Keep last ~1000 points per symbol
        self.rh.client.zremrangebyrank(self._z_hist_key(symbol), 0, -1001)


    def upsert_holding(self, symbol: str, quantity: float, avg_buy_price: float) -> None:
        if self._fallback is not None:
            return self._fallback.upsert_holding(symbol=symbol, quantity=quantity, avg_buy_price=avg_buy_price)

        doc = {'quantity': float(quantity), 'avg_buy_price': float(avg_buy_price)}
        self.rh.client.hset(self.k_portfolio, symbol, json.dumps(doc))

    def get_portfolio_snapshot(self) -> Dict[str, Any]:
        if self._fallback is not None:
            return self._fallback.get_portfolio_snapshot()

        holdings = self.rh.client.hgetall(self.k_portfolio)  # symbol -> json string


        total_cost = 0.0
        total_value = 0.0
        per_symbol: List[Dict[str, Any]] = []

        for symbol, payload_json in holdings.items():
            payload = json.loads(payload_json)
            qty = float(payload['quantity'])
            avg_buy_price = float(payload['avg_buy_price'])

            # get latest price by taking the max-score member
            latest = self.rh.client.zrevrange(self._z_hist_key(symbol), 0, 0, withscores=True)

            current_price = float(latest[0][0]) if latest else 0.0

            cost = qty * avg_buy_price
            value = qty * current_price
            pnl_abs = value - cost
            pnl_pct = (pnl_abs / cost * 100.0) if cost else 0.0

            total_cost += cost
            total_value += value

            per_symbol.append({
                'symbol': symbol,
                'quantity': qty,
                'avg_buy_price': avg_buy_price,
                'current_price': current_price,
                'cost': cost,
                'value': value,
                'pnl_abs': pnl_abs,
                'pnl_pct': pnl_pct,
            })

        overall_pnl_abs = total_value - total_cost
        overall_pnl_pct = (overall_pnl_abs / total_cost * 100.0) if total_cost else 0.0

        # Portfolio value chart points: compute total portfolio value across all holdings
        # for a set of common epochs.
        chart_points: List[Dict[str, Any]] = []

        symbols = [h['symbol'] for h in per_symbol]
        if symbols:
            # Use one symbol's history epochs as the common timeline.
            # This is a deterministic approximation given our current storage model.
            timeline_symbol = symbols[0]
            rows = self.rh.client.zrevrange(
                self._z_hist_key(timeline_symbol), 0, 199, withscores=True
            )
            rows.reverse()
            epochs = [float(score) for _, score in rows]

            for epoch in epochs:
                total_value_at_epoch = 0.0

                for symbol, payload in holdings.items():
                    payload = json.loads(payload)
                    qty = float(payload['quantity'])

                    # Latest price at or before this epoch.
                    # Scores are epoch; member is price.
                    capped_rows = self.rh.client.zrevrangebyscore(
                        self._z_hist_key(symbol), epoch, '-inf',
                        start=0, num=1, withscores=False
                    )
                    # Note: redis-py zrevrangebyscore signature varies by version; fallback to manual query.
                    if not capped_rows:
                        capped_rows = self.rh.client.zrangebyscore(
                            self._z_hist_key(symbol), '-inf', epoch,
                            start=0, num=1
                        )
                    if capped_rows:
                        current_price = float(capped_rows[0])
                    else:
                        current_price = 0.0

                    total_value_at_epoch += qty * current_price

                chart_points.append({
                    'timestamp': datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(),
                    'value': total_value_at_epoch,
                })

        return {
            'holdings': per_symbol,
            'totals': {
                'total_cost': total_cost,
                'total_value': total_value,
                'pnl_abs': overall_pnl_abs,
                'pnl_pct': overall_pnl_pct,
            },
            'price_history': chart_points,
        }



class AlertsRepository:
    def __init__(self):
        if not _redis_available():
            self._fallback = InMemoryAlertsRepository()
            return

        self._fallback = None
        self.rh = RedisHandle()
        self.user_id = 55
        # alerts stored as hash: alerts:user:55 -> field=symbol, value=json
        self.k_alerts = self.rh.key('alerts', f'user:{self.user_id}')


    def list_alerts(self) -> Dict[str, Any]:
        if self._fallback is not None:
            return self._fallback.list_alerts()

        raw = self.rh.client.hgetall(self.k_alerts)
        alerts = [json.loads(v) for v in raw.values()]
        return {'alerts': alerts}


    def mark_triggered(self, symbol: str, triggered_at: str) -> None:
        if self._fallback is not None:
            return self._fallback.mark_triggered(symbol=symbol, triggered_at=triggered_at)

        doc_raw = self.rh.client.hget(self.k_alerts, symbol)
        if not doc_raw:
            return
        doc = json.loads(doc_raw)
        doc['is_triggered'] = True
        doc['triggered_at'] = triggered_at
        self.rh.client.hset(self.k_alerts, symbol, json.dumps(doc))

    def create_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self._fallback is not None:
            return self._fallback.create_alert(payload=payload)

        symbol = (payload.get('symbol') or '').strip().upper()
        target_price = payload.get('target_price')
        alert_type = payload.get('alert_type')


        if not symbol or target_price is None or alert_type not in ('above', 'below'):
            return {'status': 400, 'error': 'Invalid payload'}

        doc = {
            'symbol': symbol,
            'target_price': float(target_price),
            'alert_type': alert_type,
            'is_triggered': False,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'triggered_at': None,
        }

        # Use symbol as field key for single active alert per symbol (demo)
        self.rh.client.hset(self.k_alerts, symbol, json.dumps(doc))
        return {'status': 201, 'message': 'Alert created'}

    def deactivate_alert(self, symbol: str) -> Dict[str, Any]:
        """Remove alert for a symbol (demo deactivation)."""
        if self._fallback is not None:
            return self._fallback.deactivate_alert(symbol=symbol)

        # delete hash field
        deleted = self.rh.client.hdel(self.k_alerts, symbol)
        if deleted:
            return {'status': 200, 'message': 'Alert deactivated'}
        return {'status': 400, 'error': 'Alert not found'}




