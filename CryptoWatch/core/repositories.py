import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Fallback in-memory storage structures (thread-safe)
_LOCK = threading.Lock()
_MEMORY_PORTFOLIO: Dict[str, Dict[str, float]] = {}
_MEMORY_HISTORIES: Dict[str, List[tuple[float, float]]] = {}
_MEMORY_ALERTS: Dict[str, Dict[str, Any]] = {}
_MEMORY_TRANSACTIONS: List[Dict[str, Any]] = []

TRACKED_SYMBOLS = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "MATIC", "AVAX", "LTC"]


class RedisManager:
    """Manages Redis connection pooling and availability status."""

    _pool = None
    _is_available: Optional[bool] = None
    _last_check: float = 0.0

    @classmethod
    def get_client(cls):
        try:
            import redis
            if cls._pool is None:
                cls._pool = redis.ConnectionPool(
                    host=getattr(settings, 'REDIS_HOST', 'localhost'),
                    port=getattr(settings, 'REDIS_PORT', 6379),
                    db=getattr(settings, 'REDIS_DB', 0),
                    decode_responses=True,
                    socket_connect_timeout=0.5,
                )
            return redis.Redis(connection_pool=cls._pool)
        except Exception:
            return None

    @classmethod
    def is_available(cls) -> bool:
        now = time.time()
        # Re-check availability at most once every 10 seconds
        if cls._is_available is not None and (now - cls._last_check) < 10.0:
            return cls._is_available

        client = cls.get_client()
        if client is None:
            cls._is_available = False
            cls._last_check = now
            return False

        try:
            cls._is_available = bool(client.ping())
        except Exception:
            cls._is_available = False

        cls._last_check = now
        return cls._is_available

    @staticmethod
    def key(*parts: str) -> str:
        prefix = getattr(settings, 'REDIS_PREFIX', 'cryptowatch')
        return ':'.join([prefix, *parts])


class PortfolioRepository:
    """Repository handling cryptocurrency holdings, transactions, and valuation histories.

    Uses Redis when available, with an automatic in-memory fallback for local development.
    """

    def __init__(self, user_id: int = 55):
        self.user_id = user_id
        self.use_redis = RedisManager.is_available()
        self.redis = RedisManager.get_client() if self.use_redis else None
        self.portfolio_key = RedisManager.key('portfolio', f'user:{self.user_id}')
        self.tx_key = RedisManager.key('transactions', f'user:{self.user_id}')

    def _history_key(self, symbol: str) -> str:
        return RedisManager.key('prices', 'history', symbol)

    def log_price(self, symbol: str, price: float, epoch: float) -> None:
        """Record a historical price data point for a coin symbol."""
        symbol = symbol.upper()
        price = float(price)
        epoch = float(epoch)

        if self.use_redis and self.redis:
            try:
                hist_key = self._history_key(symbol)
                self.redis.zadd(hist_key, {str(price): epoch})
                # Retain the last 1000 data points
                self.redis.zremrangebyrank(hist_key, 0, -1001)
                return
            except Exception as exc:
                logger.warning("Redis log_price failed, falling back to memory: %s", exc)

        with _LOCK:
            rows = _MEMORY_HISTORIES.setdefault(symbol, [])
            rows.append((epoch, price))
            if len(rows) > 1000:
                _MEMORY_HISTORIES[symbol] = rows[-1000:]

    def upsert_holding(self, symbol: str, quantity: float, avg_buy_price: float) -> None:
        """Update or insert an asset holding."""
        symbol = symbol.upper()
        doc = {
            'quantity': float(quantity),
            'avg_buy_price': float(avg_buy_price),
        }

        if self.use_redis and self.redis:
            try:
                self.redis.hset(self.portfolio_key, symbol, json.dumps(doc))
                return
            except Exception as exc:
                logger.warning("Redis upsert_holding failed: %s", exc)

        with _LOCK:
            _MEMORY_PORTFOLIO[symbol] = doc

    def _get_holdings_dict(self) -> Dict[str, Dict[str, float]]:
        """Retrieve raw dictionary of symbol -> {quantity, avg_buy_price}."""
        if self.use_redis and self.redis:
            try:
                raw_data = self.redis.hgetall(self.portfolio_key)
                return {sym: json.loads(val) for sym, val in raw_data.items()}
            except Exception as exc:
                logger.warning("Redis get holdings failed: %s", exc)

        with _LOCK:
            return {sym: dict(val) for sym, val in _MEMORY_PORTFOLIO.items()}

    def _get_latest_price(self, symbol: str) -> float:
        """Fetch the most recent price for a symbol."""
        symbol = symbol.upper()
        if self.use_redis and self.redis:
            try:
                rows = self.redis.zrevrange(self._history_key(symbol), 0, 0, withscores=True)
                if rows:
                    return float(rows[0][0])
            except Exception:
                pass

        with _LOCK:
            rows = _MEMORY_HISTORIES.get(symbol, [])
            if rows:
                return float(rows[-1][1])
        return 0.0

    def _get_symbol_history(self, symbol: str, limit: int = 200) -> List[Dict[str, Any]]:
        """Fetch historical points for a single coin symbol."""
        symbol = symbol.upper()
        points: List[Dict[str, Any]] = []

        if self.use_redis and self.redis:
            try:
                rows = self.redis.zrevrange(self._history_key(symbol), 0, limit - 1, withscores=True)
                rows.reverse()
                for price_str, epoch_val in rows:
                    dt = datetime.fromtimestamp(float(epoch_val), tz=timezone.utc)
                    points.append({
                        'timestamp': dt.isoformat(),
                        'symbol': symbol,
                        'price': float(price_str),
                    })
                return points
            except Exception:
                pass

        with _LOCK:
            rows = _MEMORY_HISTORIES.get(symbol, [])[-limit:]
            for epoch_val, price_val in rows:
                dt = datetime.fromtimestamp(float(epoch_val), tz=timezone.utc)
                points.append({
                    'timestamp': dt.isoformat(),
                    'symbol': symbol,
                    'price': float(price_val),
                })
        return points

    def get_portfolio_snapshot(self) -> Dict[str, Any]:
        """Compute the full portfolio valuation snapshot, holdings list, and historical charts."""
        holdings_raw = self._get_holdings_dict()
        holdings_list: List[Dict[str, Any]] = []

        total_cost = 0.0
        total_value = 0.0

        for symbol, data in holdings_raw.items():
            quantity = float(data.get('quantity', 0.0))
            avg_buy_price = float(data.get('avg_buy_price', 0.0))
            current_price = self._get_latest_price(symbol)

            cost = quantity * avg_buy_price
            value = quantity * current_price
            pnl_abs = value - cost
            pnl_pct = (pnl_abs / cost * 100.0) if cost > 0 else 0.0

            total_cost += cost
            total_value += value

            holdings_list.append({
                'symbol': symbol,
                'quantity': quantity,
                'avg_buy_price': avg_buy_price,
                'current_price': current_price,
                'cost': cost,
                'value': value,
                'pnl_abs': pnl_abs,
                'pnl_pct': pnl_pct,
            })

        overall_pnl_abs = total_value - total_cost
        overall_pnl_pct = (overall_pnl_abs / total_cost * 100.0) if total_cost > 0 else 0.0

        # Build individual coin histories
        coin_histories: Dict[str, List[Dict[str, Any]]] = {}
        for sym in TRACKED_SYMBOLS:
            coin_histories[sym] = self._get_symbol_history(sym, limit=200)

        # Build portfolio value timeline
        price_history: List[Dict[str, Any]] = []
        timeline_symbol = holdings_list[0]['symbol'] if holdings_list else "BTC"
        base_timeline = coin_histories.get(timeline_symbol, [])

        for point in base_timeline:
            # Approximate portfolio value at this timestamp
            price_history.append({
                'timestamp': point['timestamp'],
                'value': total_value,
            })

        # Fetch recent transactions
        transactions: List[Dict[str, Any]] = []
        if self.use_redis and self.redis:
            try:
                raw_tx = self.redis.lrange(self.tx_key, 0, 99)
                transactions = [json.loads(tx) for tx in raw_tx] if raw_tx else []
            except Exception:
                pass
        else:
            with _LOCK:
                transactions = list(_MEMORY_TRANSACTIONS[:100])

        return {
            'holdings': holdings_list,
            'totals': {
                'total_cost': total_cost,
                'total_value': total_value,
                'pnl_abs': overall_pnl_abs,
                'pnl_pct': overall_pnl_pct,
            },
            'price_history': price_history,
            'coin_histories': coin_histories,
            'transactions': transactions,
        }

    def execute_trade(
        self,
        symbol: str,
        action: str,
        quantity: float,
        price: float = 0.0,
    ) -> Dict[str, Any]:
        """Execute a BUY or SELL order and update holding positions and trade history."""
        symbol = symbol.strip().upper()
        action = action.strip().upper()

        if action in ('SELL', 'SOLD'):
            action = 'SOLD'
        elif action == 'BUY':
            action = 'BUY'
        else:
            return {'status': 400, 'error': f'Unsupported trade action: {action}'}

        try:
            quantity = float(quantity)
            price = float(price)
        except (ValueError, TypeError):
            return {'status': 400, 'error': 'Quantity and price must be valid numeric values'}

        if not symbol or quantity <= 0:
            return {'status': 400, 'error': 'Invalid trade parameters: symbol and positive quantity required'}

        if price <= 0.0:
            price = self._get_latest_price(symbol)
            if price <= 0.0:
                price = 100.0

        # Retrieve current position
        holdings = self._get_holdings_dict()
        current = holdings.get(symbol, {'quantity': 0.0, 'avg_buy_price': 0.0})
        old_qty = float(current.get('quantity', 0.0))
        old_avg = float(current.get('avg_buy_price', 0.0))

        if action == 'BUY':
            new_qty = old_qty + quantity
            new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty if new_qty > 0 else price
        else:
            new_qty = max(0.0, old_qty - quantity)
            new_avg = old_avg if new_qty > 0 else 0.0

        self.upsert_holding(symbol, new_qty, new_avg)

        # Record trade transaction
        trade_record = {
            'id': f"{symbol}-{int(time.time() * 1000)}",
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'total': round(quantity * price, 2),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        if self.use_redis and self.redis:
            try:
                self.redis.lpush(self.tx_key, json.dumps(trade_record))
                self.redis.ltrim(self.tx_key, 0, 99)
            except Exception as exc:
                logger.warning("Failed to save transaction to Redis: %s", exc)
        else:
            with _LOCK:
                _MEMORY_TRANSACTIONS.insert(0, trade_record)
                if len(_MEMORY_TRANSACTIONS) > 100:
                    _MEMORY_TRANSACTIONS[:] = _MEMORY_TRANSACTIONS[:100]

        return {
            'status': 200,
            'message': f"Successfully executed {action} order for {quantity} {symbol} at ${price:,.2f}",
        }


class AlertsRepository:
    """Repository handling creation, evaluation, and deactivation of price alerts."""

    def __init__(self, user_id: int = 55):
        self.user_id = user_id
        self.use_redis = RedisManager.is_available()
        self.redis = RedisManager.get_client() if self.use_redis else None
        self.alerts_key = RedisManager.key('alerts', f'user:{self.user_id}')

    def list_alerts(self) -> Dict[str, Any]:
        """List all stored alerts for the active user."""
        if self.use_redis and self.redis:
            try:
                raw_alerts = self.redis.hgetall(self.alerts_key)
                return {'alerts': [json.loads(v) for v in raw_alerts.values()]}
            except Exception as exc:
                logger.warning("Redis list_alerts failed: %s", exc)

        with _LOCK:
            return {'alerts': list(_MEMORY_ALERTS.values())}

    def create_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new price alert."""
        symbol = str(payload.get('symbol', '')).strip().upper()
        target_price = payload.get('target_price')
        alert_type = str(payload.get('alert_type', '')).lower()

        if not symbol or target_price is None or alert_type not in ('above', 'below', 'increase', 'decrease'):
            return {'status': 400, 'error': 'Invalid alert payload'}

        doc = {
            'symbol': symbol,
            'target_price': float(target_price),
            'alert_type': alert_type,
            'is_triggered': False,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'triggered_at': None,
        }

        if self.use_redis and self.redis:
            try:
                self.redis.hset(self.alerts_key, symbol, json.dumps(doc))
                return {'status': 201, 'message': f'Alert created for {symbol}'}
            except Exception as exc:
                logger.warning("Redis create_alert failed: %s", exc)

        with _LOCK:
            _MEMORY_ALERTS[symbol] = doc

        return {'status': 201, 'message': f'Alert created for {symbol}'}

    def mark_triggered(self, symbol: str, triggered_at: str) -> None:
        """Mark an active alert as triggered."""
        symbol = symbol.strip().upper()

        if self.use_redis and self.redis:
            try:
                raw = self.redis.hget(self.alerts_key, symbol)
                if raw:
                    doc = json.loads(raw)
                    doc['is_triggered'] = True
                    doc['triggered_at'] = triggered_at
                    self.redis.hset(self.alerts_key, symbol, json.dumps(doc))
                    return
            except Exception as exc:
                logger.warning("Redis mark_triggered failed: %s", exc)

        with _LOCK:
            if symbol in _MEMORY_ALERTS:
                _MEMORY_ALERTS[symbol]['is_triggered'] = True
                _MEMORY_ALERTS[symbol]['triggered_at'] = triggered_at

    def deactivate_alert(self, symbol: str) -> Dict[str, Any]:
        """Deactivate and delete an alert for a symbol."""
        symbol = symbol.strip().upper()

        if self.use_redis and self.redis:
            try:
                deleted = self.redis.hdel(self.alerts_key, symbol)
                if deleted:
                    return {'status': 200, 'message': f'Alert for {symbol} deactivated'}
                return {'status': 400, 'error': 'Alert not found'}
            except Exception as exc:
                logger.warning("Redis deactivate_alert failed: %s", exc)

        with _LOCK:
            if symbol in _MEMORY_ALERTS:
                del _MEMORY_ALERTS[symbol]
                return {'status': 200, 'message': f'Alert for {symbol} deactivated'}

        return {'status': 400, 'error': 'Alert not found'}
