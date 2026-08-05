from __future__ import annotations

from typing import Any, Dict

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .repositories import AlertsRepository, PortfolioRepository
from .serializers import (
    AlertCreateRequestSerializer,
    AlertSerializer,
    PortfolioStateSerializer,
    TradeRequestSerializer,
)


class PortfolioStateAPIView(APIView):

    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        data = PortfolioRepository().get_portfolio_snapshot()
        return Response(PortfolioStateSerializer(data).data)


class TradeAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request) -> Response:
        serializer = TradeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payload: Dict[str, Any] = serializer.validated_data
        result = PortfolioRepository().execute_trade(
            symbol=payload['symbol'],
            action=payload['action'],
            quantity=payload['quantity'],
            price=payload.get('price', 0.0),
        )
        if result.get('status', 200) not in (200, 201):
            return Response({'error': result.get('error', 'Trade failed')}, status=400)

        data = PortfolioRepository().get_portfolio_snapshot()
        return Response(
            {
                'message': result.get('message', 'Trade executed successfully'),
                'portfolio': PortfolioStateSerializer(data).data,
            },
            status=200,
        )


class AlertsAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        data = AlertsRepository().list_alerts()
        alerts = data.get('alerts', [])
        return Response({'alerts': AlertSerializer(alerts, many=True).data})


class AlertCreateAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request) -> Response:
        serializer = AlertCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payload: Dict[str, Any] = serializer.validated_data
        result = AlertsRepository().create_alert(payload)
        if result.get('status') != 201:
            return Response({'error': result.get('error', 'Invalid payload')}, status=400)

        alerts = AlertsRepository().list_alerts().get('alerts', [])
        return Response(
            {
                'message': result.get('message', 'Alert created'),
                'alerts': AlertSerializer(alerts, many=True).data,
            },
            status=201,
        )

