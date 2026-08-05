from __future__ import annotations

import threading
import time
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .domain.exceptions import UnknownCoinSymbolError


class InMemoryClock:
    def now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()


@dataclass
class InMemoryPortfolioState:
    # symbol -> {quantity, avg_buy_price}
    holdings: Dict[str, Dict[str, float]]

    def __init__(self):
        self.holdings = {}


@dataclass
class InMemoryHistoryState:
    # symbol -> list of (epoch, price)
    history: Dict[str, List[tuple[float, float]]]

    def __init__(self):
        self.history = {}


class InMemoryPortfolioRepository:
    """In-memory fallback when Redis is unavailable."""

    def __init__(self):
        self._lock = threading.Lock()
        self.user_id = 55
        self._portfolio = _SHARED_PORTFOLIO_STATE
        self._history = _SHARED_HISTORY_STATE
        self._clock = InMemoryClock()

    def log_price(self, symbol: str, price: float, epoch: float) -> None:
        with self._lock:
            rows = self._history.history.setdefault(symbol, [])
            rows.append((float(epoch), float(price)))
            if len(rows) > 1001:
                rows[:] = rows[-1001:]

    def upsert_holding(self, symbol: str, quantity: float, avg_buy_price: float) -> None:
        with self._lock:
            self._portfolio.holdings[symbol] = {
                'quantity': float(quantity),
                'avg_buy_price': float(avg_buy_price),
            }

    def execute_trade(self, symbol: str, action: str, quantity: float, price: float = 0.0) -> Dict[str, Any]:
        symbol = (symbol or '').strip().upper()
        action = (action or '').strip().upper()
        try:
            quantity = float(quantity)
            price = float(price)
        except (ValueError, TypeError):
            return {'status': 400, 'error': 'Invalid quantity or price numeric value'}

        if not symbol or quantity <= 0 or action not in ('BUY', 'SELL', 'SOLD'):
            return {'status': 400, 'error': 'Invalid trade parameters'}

        with self._lock:
            if price <= 0.0:
                if symbol in self._history.history and self._history.history[symbol]:
                    _, price = sorted(self._history.history[symbol], key=lambda x: x[0])[-1]
                else:
                    price = 100.0

            curr = self._portfolio.holdings.get(symbol, {'quantity': 0.0, 'avg_buy_price': 0.0})
            old_qty = float(curr.get('quantity', 0.0))
            old_avg = float(curr.get('avg_buy_price', 0.0))

            if action == 'BUY':
                new_qty = old_qty + quantity
                new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty if new_qty > 0 else price
                self._portfolio.holdings[symbol] = {'quantity': new_qty, 'avg_buy_price': new_avg}
            else:
                new_qty = max(0.0, old_qty - quantity)
                new_avg = old_avg if new_qty > 0 else 0.0
                self._portfolio.holdings[symbol] = {'quantity': new_qty, 'avg_buy_price': new_avg}

            trade_record = {
                'id': f"{symbol}-{int(time.time()*1000)}",
                'symbol': symbol,
                'action': 'BUY' if action == 'BUY' else 'SOLD',
                'quantity': quantity,
                'price': price,
                'total': quantity * price,
                'timestamp': self._clock.now_iso(),
            }
            _SHARED_TRANSACTIONS.insert(0, trade_record)
            if len(_SHARED_TRANSACTIONS) > 100:
                _SHARED_TRANSACTIONS[:] = _SHARED_TRANSACTIONS[:100]

        return {'status': 200, 'message': f"Successfully executed {action} for {quantity} {symbol}"}

    def get_portfolio_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            holdings = self._portfolio.holdings

            total_cost = 0.0
            total_value = 0.0
            per_symbol: List[Dict[str, Any]] = []

            for symbol, payload in holdings.items():
                qty = float(payload['quantity'])
                avg_buy_price = float(payload['avg_buy_price'])

                latest_price = 0.0
                if symbol in self._history.history and self._history.history[symbol]:
                    _, latest_price = sorted(self._history.history[symbol], key=lambda x: x[0])[-1]

                cost = qty * avg_buy_price
                value = qty * latest_price
                pnl_abs = value - cost
                pnl_pct = (pnl_abs / cost * 100.0) if cost else 0.0

                total_cost += cost
                total_value += value

                per_symbol.append({
                    'symbol': symbol,
                    'quantity': qty,
                    'avg_buy_price': avg_buy_price,
                    'current_price': latest_price,
                    'cost': cost,
                    'value': value,
                    'pnl_abs': pnl_abs,
                    'pnl_pct': pnl_pct,
                })

            overall_pnl_abs = total_value - total_cost
            overall_pnl_pct = (overall_pnl_abs / total_cost * 100.0) if total_cost else 0.0

            chart_points: List[Dict[str, Any]] = []
            any_symbol: Optional[str] = next(iter(holdings.keys()), None)
            if not any_symbol and "BTC" in self._history.history:
                any_symbol = "BTC"
            if any_symbol and any_symbol in self._history.history:
                rows = sorted(self._history.history[any_symbol], key=lambda x: x[0])[-200:]
                for epoch, price in rows:
                    chart_points.append({
                        'timestamp': datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(),
                        'symbol': any_symbol,
                        'price': float(price),
                    })

            coin_histories: Dict[str, List[Dict[str, Any]]] = {}
            for sym, points in self._history.history.items():
                rows = sorted(points, key=lambda x: x[0])[-200:]
                sym_points = []
                for epoch, price in rows:
                    sym_points.append({
                        'timestamp': datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(),
                        'symbol': sym,
                        'price': float(price),
                    })
                coin_histories[sym] = sym_points

            return {
                'holdings': per_symbol,
                'totals': {
                    'total_cost': total_cost,
                    'total_value': total_value,
                    'pnl_abs': overall_pnl_abs,
                    'pnl_pct': overall_pnl_pct,
                },
                'price_history': chart_points,
                'coin_histories': coin_histories,
                'transactions': list(_SHARED_TRANSACTIONS),
            }


class InMemoryAlertsRepository:
    """In-memory fallback for alerts."""

    def __init__(self):
        self._lock = threading.Lock()
        self.user_id = 55
        self._alerts: Dict[str, Dict[str, Any]] = _SHARED_ALERTS_STATE

    def list_alerts(self) -> Dict[str, Any]:
        with self._lock:
            return {'alerts': list(self._alerts.values())}

    def mark_triggered(self, symbol: str, triggered_at: str) -> None:
        with self._lock:
            doc = self._alerts.get(symbol)
            if not doc:
                return
            doc['is_triggered'] = True
            doc['triggered_at'] = triggered_at
            self._alerts[symbol] = doc

    def create_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = (payload.get('symbol') or '').strip().upper()
        target_price = payload.get('target_price')
        alert_type = payload.get('alert_type')

        if not symbol or target_price is None or alert_type not in ('above', 'below', 'increase', 'decrease'):
            return {'status': 400, 'error': 'Invalid payload'}

        doc = {
            'symbol': symbol,
            'target_price': float(target_price),
            'alert_type': alert_type,
            'is_triggered': False,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'triggered_at': None,
        }

        with self._lock:
            self._alerts[symbol] = doc

        return {'status': 201, 'message': 'Alert created'}

    def deactivate_alert(self, symbol: str) -> Dict[str, Any]:
        with self._lock:
            if symbol not in self._alerts:
                return {'status': 400, 'error': 'Alert not found'}
            del self._alerts[symbol]
            return {'status': 200, 'message': 'Alert deactivated'}


_SHARED_PORTFOLIO_STATE = InMemoryPortfolioState()
_SHARED_HISTORY_STATE = InMemoryHistoryState()
_SHARED_ALERTS_STATE: Dict[str, Dict[str, Any]] = {}
_SHARED_TRANSACTIONS: List[Dict[str, Any]] = []



