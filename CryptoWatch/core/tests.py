import json
from django.test import Client, TestCase
from django.urls import reverse

from core.domain.models import Coin, Holding, PriceAlert
from core.mock_feed import MockPriceFeed
from core.price_engine import PriceEngine
from core.repositories import AlertsRepository, PortfolioRepository, TRACKED_SYMBOLS


class DomainModelTests(TestCase):
    """Unit tests for domain dataclasses and business logic."""

    def test_coin_validation(self):
        coin = Coin(symbol='btc', current_price=65000.5)
        self.assertEqual(coin.symbol, 'BTC')
        self.assertEqual(coin.current_price, 65000.5)

    def test_holding_pnl_calculation(self):
        holding = Holding(symbol='ETH', quantity=2.0, avg_buy_price=3000.0)
        self.assertEqual(holding.cost, 6000.0)
        self.assertEqual(holding.current_value(3500.0), 7000.0)

        pnl_abs, pnl_pct = holding.pnl(3500.0)
        self.assertEqual(pnl_abs, 1000.0)
        self.assertAlmostEqual(pnl_pct, 16.6666, places=2)

    def test_price_alert_validation(self):
        alert = PriceAlert(symbol='sol', target_price=150.0, alert_type='above')
        self.assertEqual(alert.symbol, 'SOL')
        self.assertFalse(alert.is_triggered)

        with self.assertRaises(ValueError):
            PriceAlert(symbol='SOL', target_price=150.0, alert_type='invalid_type')


class RepositoryTests(TestCase):
    """Unit tests for PortfolioRepository and AlertsRepository."""

    def setUp(self):
        self.portfolio_repo = PortfolioRepository()
        self.alerts_repo = AlertsRepository()

    def test_log_price_and_snapshot(self):
        self.portfolio_repo.log_price('BTC', 65000.0, 1700000000.0)
        snapshot = self.portfolio_repo.get_portfolio_snapshot()
        self.assertIn('holdings', snapshot)
        self.assertIn('totals', snapshot)
        self.assertIn('coin_histories', snapshot)
        self.assertIn('BTC', snapshot['coin_histories'])

    def test_execute_buy_and_sell_trade(self):
        # 1. Buy 2.0 BTC at $50,000
        res = self.portfolio_repo.execute_trade(symbol='BTC', action='BUY', quantity=2.0, price=50000.0)
        self.assertEqual(res['status'], 200)

        # 2. Buy another 1.0 BTC at $65,000 -> New average buy price = (100,000 + 65,000) / 3 = $55,000
        res2 = self.portfolio_repo.execute_trade(symbol='BTC', action='BUY', quantity=1.0, price=65000.0)
        self.assertEqual(res2['status'], 200)

        snapshot = self.portfolio_repo.get_portfolio_snapshot()
        btc_holding = next((h for h in snapshot['holdings'] if h['symbol'] == 'BTC'), None)
        self.assertIsNotNone(btc_holding)
        self.assertEqual(btc_holding['quantity'], 3.0)
        self.assertAlmostEqual(btc_holding['avg_buy_price'], 55000.0, places=2)

        # 3. Sell 1.0 BTC
        res3 = self.portfolio_repo.execute_trade(symbol='BTC', action='SELL', quantity=1.0, price=60000.0)
        self.assertEqual(res3['status'], 200)

        snapshot2 = self.portfolio_repo.get_portfolio_snapshot()
        btc_holding2 = next((h for h in snapshot2['holdings'] if h['symbol'] == 'BTC'), None)
        self.assertEqual(btc_holding2['quantity'], 2.0)
        # Average buy price remains unchanged on sell
        self.assertAlmostEqual(btc_holding2['avg_buy_price'], 55000.0, places=2)

    def test_alert_lifecycle(self):
        # Create alert
        create_res = self.alerts_repo.create_alert({
            'symbol': 'SOL',
            'target_price': 160.0,
            'alert_type': 'above',
        })
        self.assertEqual(create_res['status'], 201)

        # List alerts
        alerts_data = self.alerts_repo.list_alerts()
        sol_alert = next((a for a in alerts_data['alerts'] if a['symbol'] == 'SOL'), None)
        self.assertIsNotNone(sol_alert)
        self.assertFalse(sol_alert['is_triggered'])

        # Mark triggered
        self.alerts_repo.mark_triggered('SOL', '2026-08-24T12:00:00Z')
        alerts_data2 = self.alerts_repo.list_alerts()
        sol_alert2 = next((a for a in alerts_data2['alerts'] if a['symbol'] == 'SOL'), None)
        self.assertTrue(sol_alert2['is_triggered'])

        # Deactivate
        deact_res = self.alerts_repo.deactivate_alert('SOL')
        self.assertEqual(deact_res['status'], 200)


class APITests(TestCase):
    """Integration tests for all REST API endpoints."""

    def setUp(self):
        self.client = Client()

    def test_get_portfolio_endpoint(self):
        response = self.client.get(reverse('api_portfolio'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('holdings', data)
        self.assertIn('totals', data)
        self.assertIn('price_history', data)

    def test_execute_trade_endpoint(self):
        payload = {
            'symbol': 'ETH',
            'action': 'BUY',
            'quantity': 2.5,
            'price': 3200.0,
        }
        response = self.client.post(
            reverse('api_trade'),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('portfolio', data)

    def test_alerts_endpoints(self):
        # 1. Create alert
        create_payload = {
            'symbol': 'ADA',
            'target_price': 0.50,
            'alert_type': 'above',
        }
        create_resp = self.client.post(
            reverse('api_create_alert'),
            data=json.dumps(create_payload),
            content_type='application/json',
        )
        self.assertEqual(create_resp.status_code, 201)

        # 2. List alerts
        list_resp = self.client.get(reverse('api_alerts'))
        self.assertEqual(list_resp.status_code, 200)
        self.assertIn('alerts', list_resp.json())

        # 3. Deactivate alert
        deact_resp = self.client.post(
            reverse('api_alerts_deactivate'),
            data=json.dumps({'symbol': 'ADA'}),
            content_type='application/json',
        )
        self.assertEqual(deact_resp.status_code, 200)

    def test_live_prices_endpoint(self):
        response = self.client.get(reverse('api_live_prices'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('prices', data)
        self.assertIn('BTC', data['prices'])

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CryptoWatch')

