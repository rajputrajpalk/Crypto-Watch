from __future__ import annotations

from typing import Any, Dict

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .api import AlertsAPIView  # noqa: F401 (keeps style consistent)
from .repositories import AlertsRepository
from .serializers_alerts import AlertDeactivateRequestSerializer


class AlertDeactivateAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request) -> Response:
        serializer = AlertDeactivateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        symbol = serializer.validated_data['symbol'].strip().upper()

        result: Dict[str, Any] = AlertsRepository().deactivate_alert(symbol=symbol)
        if result.get('status') != 200:
            return Response({'error': result.get('error', 'Could not deactivate alert')}, status=400)

        alerts = AlertsRepository().list_alerts().get('alerts', [])
        return Response({'message': 'Alert deactivated', 'alerts': alerts}, status=200)

