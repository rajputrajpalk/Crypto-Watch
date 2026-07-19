from __future__ import annotations

from pathlib import Path

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from CryptoWatch import settings
from .mock_feed import MockPriceFeed
from .serializers_live_prices import LivePricesSerializer


class LivePricesAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        prices = MockPriceFeed(json_path=Path(settings.BASE_DIR) / 'mock_prices.json').read_prices()
        return Response(LivePricesSerializer({'prices': prices}).data)

