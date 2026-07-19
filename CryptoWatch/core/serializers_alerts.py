from __future__ import annotations

from rest_framework import serializers


class AlertDeactivateRequestSerializer(serializers.Serializer):
    symbol = serializers.CharField()

