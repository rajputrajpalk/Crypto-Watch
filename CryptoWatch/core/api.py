from pathlib import Path

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .mock_feed import MockPriceFeed
from .repositories import AlertsRepository, PortfolioRepository
from .serializers import (
    AlertCreateRequestSerializer,
    AlertDeactivateRequestSerializer,
    AlertSerializer,
    LivePricesSerializer,
    PortfolioStateSerializer,
    TradeRequestSerializer,
)


class PortfolioStateAPIView(APIView):
    """Retrieve full snapshot of user holdings, totals, chart timelines, and transactions."""

    def get(self, request: Request) -> Response:
        repo = PortfolioRepository()
        data = repo.get_portfolio_snapshot()
        serializer = PortfolioStateSerializer(data)
        return Response(serializer.data)


class TradeAPIView(APIView):
    """Execute BUY or SELL trade orders on a cryptocurrency asset."""

    def post(self, request: Request) -> Response:
        serializer = TradeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payload = serializer.validated_data
        repo = PortfolioRepository()
        result = repo.execute_trade(
            symbol=payload['symbol'],
            action=payload['action'],
            quantity=payload['quantity'],
            price=payload.get('price', 0.0),
        )

        if result.get('status', 200) not in (200, 201):
            return Response(
                {'error': result.get('error', 'Trade execution failed')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        snapshot = repo.get_portfolio_snapshot()
        return Response(
            {
                'message': result.get('message', 'Trade executed successfully'),
                'portfolio': PortfolioStateSerializer(snapshot).data,
            },
            status=status.HTTP_200_OK,
        )


class AlertsAPIView(APIView):
    """List all active and triggered price alerts."""

    def get(self, request: Request) -> Response:
        repo = AlertsRepository()
        data = repo.list_alerts()
        alerts = data.get('alerts', [])
        return Response({'alerts': AlertSerializer(alerts, many=True).data})


class AlertCreateAPIView(APIView):
    """Create a new price threshold alert."""

    def post(self, request: Request) -> Response:
        serializer = AlertCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        repo = AlertsRepository()
        result = repo.create_alert(serializer.validated_data)
        if result.get('status') != 201:
            return Response(
                {'error': result.get('error', 'Could not create alert')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alerts = repo.list_alerts().get('alerts', [])
        return Response(
            {
                'message': result.get('message', 'Alert created successfully'),
                'alerts': AlertSerializer(alerts, many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AlertDeactivateAPIView(APIView):
    """Deactivate/remove an existing price alert."""

    def post(self, request: Request) -> Response:
        serializer = AlertDeactivateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        symbol = serializer.validated_data['symbol']
        repo = AlertsRepository()
        result = repo.deactivate_alert(symbol=symbol)

        if result.get('status') != 200:
            return Response(
                {'error': result.get('error', 'Alert not found')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alerts = repo.list_alerts().get('alerts', [])
        return Response(
            {
                'message': f'Alert for {symbol} deactivated',
                'alerts': AlertSerializer(alerts, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class LivePricesAPIView(APIView):
    """Fetch simulated real-time market prices for all tracked assets."""

    def get(self, request: Request) -> Response:
        feed_path = Path(settings.BASE_DIR) / 'mock_prices.json'
        prices = MockPriceFeed(json_path=feed_path).read_prices()
        return Response(LivePricesSerializer({'prices': prices}).data)
